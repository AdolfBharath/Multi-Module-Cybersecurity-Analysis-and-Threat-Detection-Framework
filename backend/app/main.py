from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import api_error_handler, rate_limit_handler
from app.db.models import AuditLog
from app.db.session import Base, engine
from app.db.session import SessionLocal
from app.seed import seed_database

limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    settings.validate_runtime_security()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    )
    app.state.limiter = limiter
    if settings.ENVIRONMENT.lower() != "test":
        app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(Exception, api_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.middleware("http")
    async def security_context(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id") or str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' ws: wss: http://localhost:8000 http://127.0.0.1:8000; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Cache-Control"] = "no-store"
        if request.url.path.startswith(settings.API_V1_PREFIX) and not request.url.path.endswith("/health"):
            db = SessionLocal()
            try:
                db.add(
                    AuditLog(
                        actor=request.headers.get("x-api-actor", "api"),
                        action=f"{request.method} {response.status_code}",
                        entity=request.url.path,
                        metadata_json={"client": request.client.host if request.client else "", "request_id": request.state.request_id, "user_agent": request.headers.get("user-agent", "")[:255]},
                        ip_address=request.client.host if request.client else "",
                    )
                )
                db.commit()
            finally:
                db.close()
        return response

    @app.on_event("startup")
    def startup() -> None:
        if settings.AUTO_CREATE_TABLES and not settings.is_production:
            Base.metadata.create_all(bind=engine)
        seed_database()

    return app


app = create_app()

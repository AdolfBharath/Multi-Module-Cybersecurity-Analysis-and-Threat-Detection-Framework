from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import api_error_handler, rate_limit_handler
from app.db.session import Base, engine
from app.seed import seed_database

limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    )
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(Exception, api_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.on_event("startup")
    def startup() -> None:
        Base.metadata.create_all(bind=engine)
        seed_database()

    return app


app = create_app()


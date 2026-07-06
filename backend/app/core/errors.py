from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"success": False, "error": {"code": "RATE_LIMITED", "message": str(exc.detail)}},
    )


async def api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "Unexpected server error"}},
    )


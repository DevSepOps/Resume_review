"""Maps exceptions to the contract error envelope."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.pkg.errors import (
    Conflict,
    DomainError,
    Forbidden,
    NotFound,
    PayloadTooLarge,
    ServiceUnavailable,
    Unauthorized,
    ValidationFailed,
)
from app.pkg.logger import get_logger

log = get_logger(__name__)

STATUS = {
    NotFound: 404,
    Conflict: 409,
    Unauthorized: 401,
    Forbidden: 403,
    ValidationFailed: 400,
    PayloadTooLarge: 413,
    ServiceUnavailable: 503,
}


def envelope(status_code: int, detail, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "status_code": status_code, "detail": detail},
        headers=headers,
    )


def _headers(status_code: int) -> dict | None:
    return {"WWW-Authenticate": "Bearer"} if status_code == 401 else None


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_handler(request: Request, exc: DomainError):
        code = next((c for t, c in STATUS.items() if isinstance(exc, t)), 400)
        return envelope(code, exc.message, _headers(code))

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        return envelope(exc.status_code, exc.detail, _headers(exc.status_code))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        # drop "input"/"ctx": they can echo passwords back to the client
        errors = [
            {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
            for e in exc.errors()
        ]
        return envelope(422, errors)

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        log.error(
            "unhandled error",
            exc_info=exc,
            extra={"path": request.url.path, "method": request.method},
        )
        return envelope(500, "Internal server error")

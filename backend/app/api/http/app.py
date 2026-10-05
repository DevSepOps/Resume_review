import time
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.http.dependencies import Container
from app.api.http.errors import register_error_handlers
from app.api.http.routers import admin, health, resumes, users
from app.pkg.config import Settings, get_settings
from app.pkg.logger import get_logger, setup_logging

log = get_logger(__name__)


def create_app(
    settings: Optional[Settings] = None, container: Optional[Container] = None
) -> FastAPI:
    settings = settings or (container.settings if container else get_settings())
    setup_logging(settings.LOG_LEVEL)

    app = FastAPI(
        title="Resume Review API",
        version="1.0.0",
        docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
        redoc_url=None,
        openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
    )
    app.state.container = container or Container(settings)

    origins = settings.cors_origins_list
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        log.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(elapsed * 1000, 1),
            },
        )
        return response

    register_error_handlers(app)
    for module in (health, users, resumes, admin):
        app.include_router(module.router)
    return app

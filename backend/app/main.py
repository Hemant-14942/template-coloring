from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    SlideNotFoundError,
    TemplateNotFoundError,
    slide_not_found_handler,
    template_not_found_handler,
)
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_exception_handler(TemplateNotFoundError, template_not_found_handler)
    app.add_exception_handler(SlideNotFoundError, slide_not_found_handler)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()

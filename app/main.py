"""Точка входа FastAPI-приложения «Форт»."""

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Фабрика приложения."""
    settings = get_settings()
    application = FastAPI(title=settings.app_name, debug=settings.debug)
    application.include_router(api_v1_router)

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        """Health-check."""
        return {"status": "ok"}

    return application


app = create_app()

"""Конфигурация приложения через pydantic-settings. Секреты — только из .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаются из окружения / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Приложение
    app_name: str = "Fort Security SaaS"
    debug: bool = False

    # База данных
    database_url: str = "postgresql+asyncpg://fort:fort@localhost:5432/fort"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 14

    # Суперадмин для сидинга
    superadmin_email: str = "admin@fort.local"
    superadmin_password: str = "change-me-too"


@lru_cache
def get_settings() -> Settings:
    """Возвращает синглтон настроек."""
    return Settings()

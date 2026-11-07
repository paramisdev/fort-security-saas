from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Fort Security SaaS"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://fort:fort@localhost:5432/fort"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 14

    superadmin_email: str = "admin@fort.local"
    superadmin_password: str = "change-me-too"


@lru_cache
def get_settings() -> Settings:
    return Settings()

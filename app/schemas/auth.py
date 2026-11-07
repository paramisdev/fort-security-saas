"""Pydantic-схемы аутентификации."""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import TenantAdminCreate


class TenantRegisterRequest(BaseModel):
    """Регистрация новой компании: тенант + первый пользователь (TenantAdmin)."""

    tenant_name: str = Field(min_length=1, max_length=255)
    admin: TenantAdminCreate


class LoginRequest(BaseModel):
    """Вход по email и паролю."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Обновление access-токена по refresh-токену."""

    refresh_token: str


class TokenPairResponse(BaseModel):
    """Пара access/refresh токенов."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Только access-токен (после refresh)."""

    access_token: str
    token_type: str = "bearer"

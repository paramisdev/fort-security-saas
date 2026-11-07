"""Хеширование паролей (bcrypt) и работа с JWT (PyJWT)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings
from app.models.enums import UserRole

settings = get_settings()

# Ключи в payload токена.
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(password: str) -> str:
    """Хеширует пароль bcrypt-ом."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Проверяет пароль против сохранённого хеша."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        # Некорректный формат хеша в БД.
        return False


def _create_token(
    *,
    subject: str,
    token_type: str,
    role: UserRole | str,
    tenant_id: uuid.UUID | None,
    expires_delta: timedelta,
) -> str:
    """Собирает и подписывает JWT с общим набором claims."""
    # ORM возвращает роль как str (колонка String) — приводим к enum.
    role_value = role.value if isinstance(role, UserRole) else role
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "role": role_value,
        "iat": now,
        "exp": now + expires_delta,
    }
    if tenant_id is not None:
        payload["tenant_id"] = str(tenant_id)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    *, user_id: uuid.UUID, role: UserRole | str, tenant_id: uuid.UUID | None
) -> str:
    """Создаёт короткоживущий access-токен."""
    return _create_token(
        subject=str(user_id),
        token_type=TOKEN_TYPE_ACCESS,
        role=role,
        tenant_id=tenant_id,
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )


def create_refresh_token(
    *, user_id: uuid.UUID, role: UserRole | str, tenant_id: uuid.UUID | None
) -> str:
    """Создаёт долгоживущий refresh-токен."""
    return _create_token(
        subject=str(user_id),
        token_type=TOKEN_TYPE_REFRESH,
        role=role,
        tenant_id=tenant_id,
        expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Декодирует и валидирует JWT.

    Raises:
        jwt.InvalidTokenError: подпись невалидна или токен просрочен.
    """
    decoded: dict[str, Any] = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    return decoded

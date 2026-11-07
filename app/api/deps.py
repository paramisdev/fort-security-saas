"""FastAPI-зависимости: БД, текущий пользователь, RBAC."""

import uuid
from collections.abc import Awaitable, Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.db import get_session
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
) -> User:
    """Извлекает пользователя из access-токена.

    Raises:
        HTTPException: 401, если токен невалиден или пользователь не найден.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_token(token)
        token_type: str = payload.get("type", "")
        user_id: str | None = payload.get("sub")
    except jwt.InvalidTokenError:
        raise credentials_error from None

    if token_type != security.TOKEN_TYPE_ACCESS or user_id is None:
        raise credentials_error

    try:
        parsed_id = uuid.UUID(user_id)
    except ValueError:
        raise credentials_error from None

    user = await UserRepository(session).get_by_id(parsed_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """Фабрика зависимости: разрешает доступ только указанным ролям.

    Пример: Depends(require_roles(UserRole.SUPERADMIN, UserRole.TENANT_ADMIN)).
    """

    async def check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return check_role

"""Эндпоинты аутентификации: регистрация, вход, refresh."""

import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.db import get_session
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    TenantRegisterRequest,
    TokenPairResponse,
)
from app.schemas.user import UserRead
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_tenant(
    payload: TenantRegisterRequest, session: AsyncSession = Depends(get_session)
) -> User:
    """Регистрация новой компании: создаёт tenant и его администратора."""
    try:
        _tenant, admin = await auth_service.register_tenant_with_admin(
            session,
            tenant_name=payload.tenant_name,
            email=payload.admin.email,
            password=payload.admin.password,
            full_name=payload.admin.full_name,
        )
    except auth_service.EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from None
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None
    return admin


@router.post("/login", response_model=TokenPairResponse)
async def login(
    payload: LoginRequest, session: AsyncSession = Depends(get_session)
) -> TokenPairResponse:
    """Выдаёт пару access/refresh токенов по email и паролю."""
    try:
        user = await auth_service.authenticate(
            session, email=payload.email, password=payload.password
        )
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    tokens = auth_service.issue_token_pair(user)
    return TokenPairResponse(**tokens)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    payload: RefreshRequest, session: AsyncSession = Depends(get_session)
) -> AccessTokenResponse:
    """Выдаёт новый access-токен по валидному refresh-токену."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
    try:
        token_payload = security.decode_token(payload.refresh_token)
    except jwt.InvalidTokenError:
        raise credentials_error from None

    if token_payload.get("type") != security.TOKEN_TYPE_REFRESH:
        raise credentials_error

    subject = token_payload.get("sub")
    if not subject:
        raise credentials_error
    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise credentials_error from None

    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_error

    return AccessTokenResponse(access_token=auth_service.issue_access_token_from_refresh(user))

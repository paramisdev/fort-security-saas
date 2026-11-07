"""Сервис аутентификации и регистрации. Без импортов FastAPI."""

import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.models.enums import UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.repositories.subscription import SubscriptionRepository
from app.repositories.tariff import TariffRepository
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository

DEFAULT_TARIFF_CODE = "start"


class AuthError(Exception):
    """Базовая ошибка аутентификации/регистрации."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EmailAlreadyExistsError(AuthError):
    """Email уже занят."""


class InvalidCredentialsError(AuthError):
    """Неверный email или пароль."""

    def __init__(self) -> None:
        super().__init__("Incorrect email or password", status_code=401)


class InvalidTenantNameError(AuthError):
    """Имя тенанта нельзя преобразовать в уникальный slug."""


class DefaultTariffNotConfiguredError(AuthError):
    """Тариф по умолчанию отсутствует или отключён."""

    def __init__(self, code: str) -> None:
        super().__init__(f"Default tariff '{code}' is not configured", status_code=500)


def _slugify(value: str) -> str:
    """Преобразует имя компании в slug (a-z, 0-9, дефис)."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:100]


async def register_tenant_with_admin(
    session: AsyncSession, *, tenant_name: str, email: str, password: str, full_name: str
) -> tuple[Tenant, User]:
    """Создаёт нового тенанта и его первого администратора.

    Валидация email/пароля выполняется Pydantic-схемой на уровне API.
    """
    user_repo = UserRepository(session)
    tenant_repo = TenantRepository(session)

    if await user_repo.get_by_email(email):
        raise EmailAlreadyExistsError("Email is already registered")

    tariff = await TariffRepository(session).get_by_code(DEFAULT_TARIFF_CODE)
    if tariff is None or not tariff.is_active:
        raise DefaultTariffNotConfiguredError(DEFAULT_TARIFF_CODE)

    base_slug = _slugify(tenant_name)
    if not base_slug:
        raise InvalidTenantNameError("Tenant name must contain latin letters or digits")

    # Гарантия уникальности slug: к суффиксу добавляется короткий uuid.
    slug = base_slug
    if await tenant_repo.get_by_slug(slug):
        slug = f"{base_slug[:80]}-{uuid.uuid4().hex[:8]}"

    tenant = Tenant(name=tenant_name, slug=slug)
    tenant_repo.session.add(tenant)
    await tenant_repo.session.flush()

    admin = User(
        email=email,
        hashed_password=security.hash_password(password),
        full_name=full_name,
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant.id,
    )
    await user_repo.add(admin)
    await SubscriptionRepository(session).create_active(tenant.id, tariff.id)
    await session.commit()
    return tenant, admin


async def authenticate(session: AsyncSession, *, email: str, password: str) -> User:
    """Проверяет пару email/пароль и возвращает активного пользователя."""
    user = await UserRepository(session).get_by_email(email)
    if user is None or not security.verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()
    if not user.is_active:
        raise InvalidCredentialsError()
    return user


def issue_token_pair(user: User) -> dict[str, str]:
    """Формирует пару access/refresh токенов для пользователя."""
    access = security.create_access_token(user_id=user.id, role=user.role, tenant_id=user.tenant_id)
    refresh = security.create_refresh_token(
        user_id=user.id, role=user.role, tenant_id=user.tenant_id
    )
    return {"access_token": access, "refresh_token": refresh}


def issue_access_token_from_refresh(user: User) -> str:
    """Создаёт новый access-токен по данным пользователя из refresh-токена."""
    return security.create_access_token(user_id=user.id, role=user.role, tenant_id=user.tenant_id)

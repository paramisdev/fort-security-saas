"""Общие фикстуры тестов: in-memory SQLite, приложение, клиент, токены ролей."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.db import get_session
from app.main import create_app
from app.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine(request):  # type: ignore[no-untyped-def]
    """Создаёт движок, схему БД и стандартные тарифы на время теста."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if request.node.get_closest_marker("no_tariffs") is None:
        from app.models import Tariff
        from scripts.seed import DEFAULT_TARIFFS

        maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with maker() as session:
            session.add_all([Tariff(**data) for data in DEFAULT_TARIFFS])
            await session.commit()

    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):  # type: ignore[no-untyped-def]
    """Сессия БД для тестов (одна на тест, данные изолированы)."""
    maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest.fixture
async def client(db_engine):  # type: ignore[no-untyped-def]
    """HTTP-клиент с подменённой зависимостью БД."""
    maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_session():  # type: ignore[no-untyped-def]
        async with maker() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def register_tenant(client: AsyncClient, slug: str = "acme") -> dict:
    """Регистрирует тенанта и возвращает JSON ответа (TenantAdmin-профиль)."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": f"Company {slug}",
            "admin": {
                "email": f"admin-{slug}@example.com",
                "password": "Str0ngPass!",
                "full_name": f"Admin {slug}",
            },
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def login(client: AsyncClient, email: str, password: str = "Str0ngPass!") -> dict:
    """Выполняет вход и возвращает JSON с токенами."""
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def auth_header(tokens: dict) -> dict[str, str]:
    """Собирает заголовок Authorization из пары токенов."""
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
async def tenant_admin(client):  # type: ignore[no-untyped-def]
    """Тенант + админ, возвращает dict с токенами и профилем."""
    profile = await register_tenant(client, "acme")
    tokens = await login(client, "admin-acme@example.com")
    return {"tokens": tokens, "profile": profile}


async def subscribe_tenant(admin_tokens: dict, client: AsyncClient, tariff_code: str) -> dict:
    """Оформляет тенанту активную подписку на тариф через заглушку оплаты."""
    response = await client.post(
        "/api/v1/subscriptions/change",
        json={"tariff_code": tariff_code},
        headers=auth_header(admin_tokens),
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
async def superadmin(db_session, client):  # type: ignore[no-untyped-def]
    """SuperAdmin без тенанта, возвращает dict с токенами и профилем."""
    from app.core import security
    from app.models import User
    from app.models.enums import UserRole

    user = User(
        email="super@example.com",
        hashed_password=security.hash_password("Str0ngPass!"),
        full_name="Super Admin",
        role=UserRole.SUPERADMIN,
        tenant_id=None,
    )
    db_session.add(user)
    await db_session.commit()

    tokens = await login(client, "super@example.com")
    return {"tokens": tokens, "profile": {"id": str(user.id), "email": user.email}}


@pytest.fixture
async def subscribed_admin(tenant_admin, client):  # type: ignore[no-untyped-def]
    """Тенант с автоматической подпиской на тариф 'start' (1 объект, 3 устройства)."""
    response = await client.get(
        "/api/v1/subscriptions/current", headers=auth_header(tenant_admin["tokens"])
    )
    assert response.status_code == 200, response.text
    return {**tenant_admin, "subscription": response.json()}

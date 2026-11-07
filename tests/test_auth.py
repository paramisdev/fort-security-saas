"""Тесты аутентификации: регистрация, логин, refresh, защита роутов, RBAC-основа."""

from tests.conftest import auth_header, login, register_tenant

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
ME_URL = "/api/v1/users/me"


async def test_register_creates_tenant_admin(client) -> None:  # type: ignore[no-untyped-def]
    """Регистрация создаёт TenantAdmin с привязкой к новому тенанту."""
    profile = await register_tenant(client, "acme")

    assert profile["email"] == "admin-acme@example.com"
    assert profile["role"] == "tenant_admin"
    assert profile["tenant_id"] is not None
    assert profile["is_active"] is True


async def test_register_duplicate_email_conflict(client) -> None:  # type: ignore[no-untyped-def]
    """Повторная регистрация с тем же email возвращает 409."""
    await register_tenant(client, "acme")
    response = await client.post(
        REGISTER_URL,
        json={
            "tenant_name": "Other Co",
            "admin": {
                "email": "admin-acme@example.com",
                "password": "Str0ngPass!",
                "full_name": "Another Admin",
            },
        },
    )
    assert response.status_code == 409


async def test_register_weak_password_rejected(client) -> None:  # type: ignore[no-untyped-def]
    """Слишком короткий пароль отклоняется валидацией схемы (422)."""
    response = await client.post(
        REGISTER_URL,
        json={
            "tenant_name": "Acme",
            "admin": {
                "email": "weak@example.com",
                "password": "short",
                "full_name": "Weak",
            },
        },
    )
    assert response.status_code == 422


async def test_login_success(client) -> None:  # type: ignore[no-untyped-def]
    """Успешный логин выдаёт пару токенов."""
    await register_tenant(client, "acme")
    tokens = await login(client, "admin-acme@example.com")

    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]


async def test_login_wrong_password_unauthorized(client) -> None:  # type: ignore[no-untyped-def]
    """Неверный пароль — 401."""
    await register_tenant(client, "acme")
    response = await client.post(
        LOGIN_URL, json={"email": "admin-acme@example.com", "password": "WrongPass!"}
    )
    assert response.status_code == 401


async def test_login_unknown_email_unauthorized(client) -> None:  # type: ignore[no-untyped-def]
    """Несуществующий email — 401 (без раскрытия, что email не найден)."""
    response = await client.post(
        LOGIN_URL, json={"email": "nobody@example.com", "password": "Str0ngPass!"}
    )
    assert response.status_code == 401


async def test_me_requires_token(client) -> None:  # type: ignore[no-untyped-def]
    """Доступ к /users/me без токена запрещён."""
    response = await client.get(ME_URL)
    assert response.status_code == 401


async def test_me_with_valid_token(client) -> None:  # type: ignore[no-untyped-def]
    """С валидным access-токеном /users/me возвращает профиль."""
    await register_tenant(client, "acme")
    tokens = await login(client, "admin-acme@example.com")

    response = await client.get(ME_URL, headers=auth_header(tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "admin-acme@example.com"
    assert body["role"] == "tenant_admin"


async def test_me_with_garbage_token_rejected(client) -> None:  # type: ignore[no-untyped-def]
    """Подделанный токен отклоняется."""
    response = await client.get(ME_URL, headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


async def test_refresh_issues_new_access_token(client) -> None:  # type: ignore[no-untyped-def]
    """Refresh выдаёт рабочий access-токен."""
    await register_tenant(client, "acme")
    tokens = await login(client, "admin-acme@example.com")

    response = await client.post(REFRESH_URL, json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    new_access = response.json()["access_token"]
    assert new_access

    me = await client.get(ME_URL, headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200


async def test_refresh_rejects_access_token(client) -> None:  # type: ignore[no-untyped-def]
    """Access-токен нельзя использовать как refresh."""
    await register_tenant(client, "acme")
    tokens = await login(client, "admin-acme@example.com")

    response = await client.post(REFRESH_URL, json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401


async def test_refresh_rejects_garbage(client) -> None:  # type: ignore[no-untyped-def]
    """Мусор вместо refresh-токена — 401."""
    response = await client.post(REFRESH_URL, json={"refresh_token": "garbage"})
    assert response.status_code == 401


async def test_two_tenants_are_isolated(client) -> None:  # type: ignore[no-untyped-def]
    """Регистрация двух компаний создаёт разных тенантов и разных пользователей."""
    first = await register_tenant(client, "acme")
    second = await register_tenant(client, "globex")

    assert first["tenant_id"] != second["tenant_id"]

    tokens = await login(client, "admin-globex@example.com")
    me = await client.get(ME_URL, headers=auth_header(tokens))
    assert me.json()["tenant_id"] == second["tenant_id"]

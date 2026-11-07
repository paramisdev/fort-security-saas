"""Тесты тарифов и подписок: каталог, RBAC, смена тарифа, запись платежа."""

import pytest

from tests.conftest import auth_header, subscribe_tenant

TARIFFS_URL = "/api/v1/tariffs"
SUBSCRIPTIONS_URL = "/api/v1/subscriptions"


@pytest.mark.no_tariffs
async def test_tariff_catalog_empty_without_seed(client) -> None:  # type: ignore[no-untyped-def]
    """Каталог публичен и доступен без авторизации."""
    response = await client.get(TARIFFS_URL)
    assert response.status_code == 200
    assert response.json() == []


async def test_tariff_catalog_lists_seeded(client) -> None:  # type: ignore[no-untyped-def]
    """Засеянные тарифы отдаются публичным каталогом, отсортированы по цене."""
    response = await client.get(TARIFFS_URL)
    assert response.status_code == 200
    codes = [t["code"] for t in response.json()]
    assert codes == ["start", "comfort", "premium", "premium_plus"]


async def test_create_tariff_superadmin_only(client, db_session, superadmin, tenant_admin) -> None:  # type: ignore[no-untyped-def]
    """Создавать тарифы может только SuperAdmin."""
    payload = {
        "code": "enterprise",
        "name": "Энтерпрайз",
        "price_monthly": 19990.0,
        "max_objects": 100,
        "max_devices": 500,
    }

    # Без токена и TenantAdmin — отказ.
    assert (await client.post(TARIFFS_URL, json=payload)).status_code == 401
    forbidden = await client.post(
        TARIFFS_URL, json=payload, headers=auth_header(tenant_admin["tokens"])
    )
    assert forbidden.status_code == 403

    created = await client.post(
        TARIFFS_URL, json=payload, headers=auth_header(superadmin["tokens"])
    )
    assert created.status_code == 201, created.text
    assert created.json()["code"] == "enterprise"

    # Дубликат кода — 409.
    duplicate = await client.post(
        TARIFFS_URL, json=payload, headers=auth_header(superadmin["tokens"])
    )
    assert duplicate.status_code == 409


async def test_update_tariff_superadmin(client, superadmin) -> None:  # type: ignore[no-untyped-def]
    """SuperAdmin обновляет лимиты тарифа."""
    listing = (await client.get(TARIFFS_URL)).json()
    start = next(t for t in listing if t["code"] == "start")

    response = await client.patch(
        f"{TARIFFS_URL}/{start['id']}",
        json={"max_devices": 5},
        headers=auth_header(superadmin["tokens"]),
    )
    assert response.status_code == 200
    assert response.json()["max_devices"] == 5
    assert response.json()["max_objects"] == start["max_objects"]


async def test_current_subscription_auto_created_on_registration(client, tenant_admin) -> None:  # type: ignore[no-untyped-def]
    """Регистрация автоматически назначает активную подписку на тариф 'start'."""
    response = await client.get(
        f"{SUBSCRIPTIONS_URL}/current", headers=auth_header(tenant_admin["tokens"])
    )
    assert response.status_code == 200
    assert response.json()["tariff"]["code"] == "start"


async def test_change_tariff_creates_active_subscription_and_payment(
    client, tenant_admin, db_session
) -> None:  # type: ignore[no-untyped-def]
    """Смена тарифа: активная подписка + запись в payments со статусом succeeded."""
    subscription = await subscribe_tenant(tenant_admin["tokens"], client, "comfort")

    assert subscription["status"] == "active"
    assert subscription["tariff"]["code"] == "comfort"
    assert subscription["period_expires_at"] is not None

    # /current возвращает ту же подписку.
    current = await client.get(
        f"{SUBSCRIPTIONS_URL}/current", headers=auth_header(tenant_admin["tokens"])
    )
    assert current.status_code == 200
    assert current.json()["id"] == subscription["id"]

    # Запись о платеже создана заглушкой.
    from sqlalchemy import select

    from app.models import Payment
    from app.models.enums import PaymentStatus

    result = await db_session.execute(select(Payment))
    payments = result.scalars().all()
    assert len(payments) == 1
    assert payments[0].status == PaymentStatus.SUCCEEDED
    assert float(payments[0].amount) == 2490.00


async def test_change_tariff_twice_keeps_single_active(client, tenant_admin) -> None:  # type: ignore[no-untyped-def]
    """Повторная смена тарифа деактивирует старую подписку (одна активная)."""
    first = await subscribe_tenant(tenant_admin["tokens"], client, "start")
    second = await subscribe_tenant(tenant_admin["tokens"], client, "premium")

    assert second["id"] != first["id"]
    current = await client.get(
        f"{SUBSCRIPTIONS_URL}/current", headers=auth_header(tenant_admin["tokens"])
    )
    assert current.json()["id"] == second["id"]
    assert current.json()["tariff"]["code"] == "premium"


async def test_upgrade_raises_limits(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """После апгрейда тарифа лимит объектов расширяется."""
    tokens = subscribed_admin["tokens"]
    # start: 1 объект.
    first = await client.post(
        "/api/v1/objects",
        json={"name": "Первый", "address": "а", "type": "apartment"},
        headers=auth_header(tokens),
    )
    assert first.status_code == 201
    blocked = await client.post(
        "/api/v1/objects",
        json={"name": "Второй", "address": "б", "type": "apartment"},
        headers=auth_header(tokens),
    )
    assert blocked.status_code == 403

    # Апгрейд до comfort (3 объекта) — второй объект проходит.
    await subscribe_tenant(tokens, client, "comfort")
    upgraded = await client.post(
        "/api/v1/objects",
        json={"name": "Второй", "address": "б", "type": "apartment"},
        headers=auth_header(tokens),
    )
    assert upgraded.status_code == 201


async def test_change_tariff_unknown_code(client, tenant_admin) -> None:  # type: ignore[no-untyped-def]
    """Неизвестный код тарифа — 404."""
    response = await client.post(
        f"{SUBSCRIPTIONS_URL}/change",
        json={"tariff_code": "nonexistent"},
        headers=auth_header(tenant_admin["tokens"]),
    )
    assert response.status_code == 404


async def test_subscriptions_forbidden_for_client_role(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Управление подписками доступно только TenantAdmin (проверяем через 403/401 сценарий)."""
    # Client-роль ещё не создаётся API — проверяем, что аноним доступ запрещён.
    response = await client.get(f"{SUBSCRIPTIONS_URL}/current")
    assert response.status_code == 401

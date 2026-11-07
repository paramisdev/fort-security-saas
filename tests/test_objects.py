"""Тесты объектов: CRUD, изоляция тенантов, лимиты тарифа, RBAC."""

import uuid

from tests.conftest import auth_header, register_tenant

OBJECTS_URL = "/api/v1/objects"


def _payload(name: str = "Квартира") -> dict:
    return {"name": name, "address": "ул. Ленина, 1", "type": "apartment"}


async def test_create_object_with_auto_subscription(client, tenant_admin) -> None:  # type: ignore[no-untyped-def]
    """После регистрации подписка 'start' уже активна: объект создаётся сразу."""
    response = await client.post(
        OBJECTS_URL, json=_payload(), headers=auth_header(tenant_admin["tokens"])
    )
    assert response.status_code == 201, response.text
    assert response.json()["name"] == "Квартира"


async def test_create_and_get_object(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Успешное создание и чтение объекта своего тенанта."""
    response = await client.post(
        OBJECTS_URL, json=_payload(), headers=auth_header(subscribed_admin["tokens"])
    )
    assert response.status_code == 201, response.text
    created = response.json()

    got = await client.get(
        f"{OBJECTS_URL}/{created['id']}", headers=auth_header(subscribed_admin["tokens"])
    )
    assert got.status_code == 200
    assert got.json()["name"] == "Квартира"


async def test_update_object(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Частичное обновление объекта."""
    created = (
        await client.post(
            OBJECTS_URL, json=_payload(), headers=auth_header(subscribed_admin["tokens"])
        )
    ).json()

    response = await client.patch(
        f"{OBJECTS_URL}/{created['id']}",
        json={"name": "Офис", "type": "office"},
        headers=auth_header(subscribed_admin["tokens"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Офис"
    assert body["type"] == "office"
    assert body["address"] == "ул. Ленина, 1"  # не изменилось


async def test_delete_object(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Удаление объекта: после удаления GET возвращает 404."""
    created = (
        await client.post(
            OBJECTS_URL, json=_payload(), headers=auth_header(subscribed_admin["tokens"])
        )
    ).json()

    deleted = await client.delete(
        f"{OBJECTS_URL}/{created['id']}", headers=auth_header(subscribed_admin["tokens"])
    )
    assert deleted.status_code == 204

    got = await client.get(
        f"{OBJECTS_URL}/{created['id']}", headers=auth_header(subscribed_admin["tokens"])
    )
    assert got.status_code == 404


async def test_object_limit_enforced(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Тариф 'start' разрешает 1 объект: второй — 403 с сообщением о лимите."""
    first = await client.post(
        OBJECTS_URL, json=_payload("Первый"), headers=auth_header(subscribed_admin["tokens"])
    )
    assert first.status_code == 201

    second = await client.post(
        OBJECTS_URL, json=_payload("Второй"), headers=auth_header(subscribed_admin["tokens"])
    )
    assert second.status_code == 403
    assert second.json()["detail"] == "Tariff limit reached: max 1 object for tariff 'Старт'"


async def test_object_isolated_between_tenants(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Чужой объект недоступен: GET по id из другого тенанта возвращает 404."""
    created = (
        await client.post(
            OBJECTS_URL, json=_payload(), headers=auth_header(subscribed_admin["tokens"])
        )
    ).json()

    # Вторая компания: тарифы уже засеяны (общий движок), подписываемся на тот же.
    from tests.conftest import login, subscribe_tenant

    await register_tenant(client, "globex")
    globex_tokens = await login(client, "admin-globex@example.com")
    await subscribe_tenant(globex_tokens, client, "comfort")

    foreign = await client.get(f"{OBJECTS_URL}/{created['id']}", headers=auth_header(globex_tokens))
    assert foreign.status_code == 404

    listing = await client.get(OBJECTS_URL, headers=auth_header(globex_tokens))
    assert listing.status_code == 200
    assert listing.json() == []


async def test_objects_require_auth(client) -> None:  # type: ignore[no-untyped-def]
    """Список объектов без токена недоступен."""
    response = await client.get(OBJECTS_URL)
    assert response.status_code == 401


async def test_object_not_found_returns_404(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Случайный UUID — 404."""
    response = await client.get(
        f"{OBJECTS_URL}/{uuid.uuid4()}", headers=auth_header(subscribed_admin["tokens"])
    )
    assert response.status_code == 404

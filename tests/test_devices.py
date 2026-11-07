"""Тесты оборудования: CRUD, лимиты, heartbeat, уникальность serial."""

import uuid

from tests.conftest import auth_header

DEVICES_URL = "/api/v1/devices"
OBJECTS_URL = "/api/v1/objects"


async def _create_object(client, admin_tokens: dict) -> str:
    response = await client.post(
        OBJECTS_URL,
        json={"name": "Офис", "address": "ул. Тестовая, 5", "type": "office"},
        headers=auth_header(admin_tokens),
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _device_payload(serial: str, object_id: str | None = None) -> dict:
    payload: dict = {"name": "Камера входа", "type": "camera", "serial_number": serial}
    if object_id:
        payload["object_id"] = object_id
    return payload


async def test_create_device_without_subscription_forbidden(client, tenant_admin) -> None:  # type: ignore[no-untyped-def]
    """Без подписки регистрация устройства запрещена (403)."""
    response = await client.post(
        DEVICES_URL, json=_device_payload("SN-001"), headers=auth_header(tenant_admin["tokens"])
    )
    assert response.status_code == 403


async def test_create_and_list_devices_with_filters(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Создание устройств и фильтры списка по type/status/object_id."""
    tokens = subscribed_admin["tokens"]
    object_id = await _create_object(client, tokens)

    camera = await client.post(
        DEVICES_URL, json=_device_payload("SN-CAM-1", object_id), headers=auth_header(tokens)
    )
    assert camera.status_code == 201, camera.text
    assert camera.json()["status"] == "offline"
    assert camera.json()["object_id"] == object_id

    lock = await client.post(
        DEVICES_URL,
        json={"name": "Замок", "type": "lock", "serial_number": "SN-LOCK-1"},
        headers=auth_header(tokens),
    )
    assert lock.status_code == 201

    all_devices = await client.get(DEVICES_URL, headers=auth_header(tokens))
    assert len(all_devices.json()) == 2

    only_cameras = await client.get(
        DEVICES_URL, params={"type": "camera"}, headers=auth_header(tokens)
    )
    assert [d["type"] for d in only_cameras.json()] == ["camera"]

    by_object = await client.get(
        DEVICES_URL, params={"object_id": object_id}, headers=auth_header(tokens)
    )
    assert len(by_object.json()) == 1


async def test_device_limit_enforced(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Тариф 'start' разрешает 3 устройства: четвёртое — 403 с сообщением о лимите."""
    tokens = subscribed_admin["tokens"]
    for i in range(3):
        response = await client.post(
            DEVICES_URL, json=_device_payload(f"SN-{i}"), headers=auth_header(tokens)
        )
        assert response.status_code == 201

    fourth = await client.post(
        DEVICES_URL, json=_device_payload("SN-EXTRA"), headers=auth_header(tokens)
    )
    assert fourth.status_code == 403
    assert "limit" in fourth.json()["detail"].lower()


async def test_duplicate_serial_number_conflict(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Дубликат серийного номера в рамках тенанта — 409."""
    tokens = subscribed_admin["tokens"]
    first = await client.post(
        DEVICES_URL, json=_device_payload("SN-DUP"), headers=auth_header(tokens)
    )
    assert first.status_code == 201

    second = await client.post(
        DEVICES_URL, json=_device_payload("SN-DUP"), headers=auth_header(tokens)
    )
    assert second.status_code == 409


async def test_device_serial_unique_per_tenant(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Одинаковый серийный номер в разных тенантах допустим."""
    tokens = subscribed_admin["tokens"]
    first = await client.post(
        DEVICES_URL, json=_device_payload("SN-SHARED"), headers=auth_header(tokens)
    )
    assert first.status_code == 201

    from tests.conftest import login, register_tenant, subscribe_tenant

    await register_tenant(client, "globex")
    globex = await login(client, "admin-globex@example.com")
    await subscribe_tenant(globex, client, "comfort")

    second = await client.post(
        DEVICES_URL, json=_device_payload("SN-SHARED"), headers=auth_header(globex)
    )
    assert second.status_code == 201


async def test_update_device_and_heartbeat(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """PATCH устройства и heartbeat-эндпоинт меняют данные и фиксируют last_seen_at."""
    tokens = subscribed_admin["tokens"]
    object_id = await _create_object(client, tokens)
    created = (
        await client.post(DEVICES_URL, json=_device_payload("SN-HB"), headers=auth_header(tokens))
    ).json()

    # Heartbeat: устройство вышло на связь.
    online = await client.patch(
        f"{DEVICES_URL}/{created['id']}/status",
        json={"status": "online"},
        headers=auth_header(tokens),
    )
    assert online.status_code == 200
    body = online.json()
    assert body["status"] == "online"
    assert body["last_seen_at"] is not None

    # Перепривязка к объекту.
    updated = await client.patch(
        f"{DEVICES_URL}/{created['id']}",
        json={"name": "Камера холла", "object_id": object_id},
        headers=auth_header(tokens),
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Камера холла"
    assert updated.json()["object_id"] == object_id


async def test_delete_device(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Удаление устройства."""
    tokens = subscribed_admin["tokens"]
    created = (
        await client.post(DEVICES_URL, json=_device_payload("SN-DEL"), headers=auth_header(tokens))
    ).json()

    deleted = await client.delete(f"{DEVICES_URL}/{created['id']}", headers=auth_header(tokens))
    assert deleted.status_code == 204

    got = await client.get(f"{DEVICES_URL}/{created['id']}", headers=auth_header(tokens))
    assert got.status_code == 404


async def test_device_unknown_object_rejected(client, subscribed_admin) -> None:  # type: ignore[no-untyped-def]
    """Привязка к несуществующему объекту — 404."""
    tokens = subscribed_admin["tokens"]
    response = await client.post(
        DEVICES_URL,
        json=_device_payload("SN-BAD-OBJ", str(uuid.uuid4())),
        headers=auth_header(tokens),
    )
    assert response.status_code == 404


async def test_devices_require_auth(client) -> None:  # type: ignore[no-untyped-def]
    """Список устройств без токена недоступен."""
    assert (await client.get(DEVICES_URL)).status_code == 401

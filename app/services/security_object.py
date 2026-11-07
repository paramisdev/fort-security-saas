"""Сервисы объектов и устройств: проверка лимитов активного тарифа."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.enums import DeviceStatus, DeviceType
from app.models.security_object import SecurityObject
from app.models.tariff import Tariff
from app.repositories.device import DeviceRepository
from app.repositories.security_object import SecurityObjectRepository
from app.repositories.subscription import SubscriptionRepository
from app.schemas.device import DeviceCreate, DeviceStatusUpdate, DeviceUpdate
from app.schemas.security_object import ObjectCreate, ObjectUpdate
from app.services.errors import (
    ConflictError,
    LimitExceededError,
    NoActiveSubscriptionError,
    NotFoundError,
)


async def get_active_tariff(session: AsyncSession, tenant_id: uuid.UUID) -> Tariff:
    """Возвращает тариф активной подписки тенанта.

    Raises:
        NoActiveSubscriptionError: активной подписки нет.
    """
    subscription = await SubscriptionRepository(session).get_active(tenant_id)
    if subscription is None:
        raise NoActiveSubscriptionError("No active subscription: choose a tariff first")
    await session.refresh(subscription, ["tariff"])
    return subscription.tariff


# --- Объекты ---


async def list_objects(session: AsyncSession, tenant_id: uuid.UUID) -> list[SecurityObject]:
    """Список объектов тенанта."""
    return await SecurityObjectRepository(session).list_by_tenant(tenant_id)


async def get_object(
    session: AsyncSession, object_id: uuid.UUID, tenant_id: uuid.UUID
) -> SecurityObject:
    """Объект тенанта по id."""
    security_object = await SecurityObjectRepository(session).get_in_tenant(object_id, tenant_id)
    if security_object is None:
        raise NotFoundError("Object not found")
    return security_object


async def create_object(
    session: AsyncSession, tenant_id: uuid.UUID, payload: ObjectCreate
) -> SecurityObject:
    """Создаёт объект, проверяя лимит max_objects тарифа."""
    tariff = await get_active_tariff(session, tenant_id)
    repo = SecurityObjectRepository(session)
    if await repo.count_by_tenant(tenant_id) >= tariff.max_objects:
        raise LimitExceededError(
            f"Tariff limit reached: max {tariff.max_objects} objects " f"for tariff '{tariff.name}'"
        )
    security_object = SecurityObject(
        tenant_id=tenant_id,
        name=payload.name,
        address=payload.address,
        type=payload.type,
    )
    await repo.add(security_object)
    await session.commit()
    return security_object


async def update_object(
    session: AsyncSession, object_id: uuid.UUID, tenant_id: uuid.UUID, payload: ObjectUpdate
) -> SecurityObject:
    """Частично обновляет объект тенанта."""
    security_object = await get_object(session, object_id, tenant_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(security_object, field, value)
    await session.commit()
    return security_object


async def delete_object(session: AsyncSession, object_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
    """Удаляет объект тенанта. Устройства остаются с object_id = NULL."""
    security_object = await get_object(session, object_id, tenant_id)
    await session.delete(security_object)
    await session.commit()


# --- Устройства ---


async def list_devices(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    object_id: uuid.UUID | None = None,
    device_type: DeviceType | None = None,
    status: DeviceStatus | None = None,
) -> list[Device]:
    """Список устройств тенанта с фильтрами."""
    return await DeviceRepository(session).list_by_tenant(
        tenant_id, object_id=object_id, device_type=device_type, status=status
    )


async def get_device(session: AsyncSession, device_id: uuid.UUID, tenant_id: uuid.UUID) -> Device:
    """Устройство тенанта по id."""
    device = await DeviceRepository(session).get_in_tenant(device_id, tenant_id)
    if device is None:
        raise NotFoundError("Device not found")
    return device


async def create_device(
    session: AsyncSession, tenant_id: uuid.UUID, payload: DeviceCreate
) -> Device:
    """Регистрирует устройство, проверяя лимит max_devices и данные."""
    tariff = await get_active_tariff(session, tenant_id)
    repo = DeviceRepository(session)

    if payload.object_id is not None:
        await get_object(session, payload.object_id, tenant_id)

    if await repo.get_by_serial_in_tenant(tenant_id, payload.serial_number):
        raise ConflictError(f"Device with serial number '{payload.serial_number}' already exists")

    if await repo.count_by_tenant(tenant_id) >= tariff.max_devices:
        raise LimitExceededError(
            f"Tariff limit reached: max {tariff.max_devices} devices " f"for tariff '{tariff.name}'"
        )

    device = Device(
        tenant_id=tenant_id,
        object_id=payload.object_id,
        name=payload.name,
        type=payload.type,
        serial_number=payload.serial_number,
        status=DeviceStatus.OFFLINE,
    )
    await repo.add(device)
    await session.commit()
    return device


async def update_device(
    session: AsyncSession, device_id: uuid.UUID, tenant_id: uuid.UUID, payload: DeviceUpdate
) -> Device:
    """Частично обновляет устройство (переименование, перепривязка к объекту)."""
    device = await get_device(session, device_id, tenant_id)
    data = payload.model_dump(exclude_unset=True)
    if "object_id" in data and data["object_id"] is not None:
        await get_object(session, data["object_id"], tenant_id)
    for field, value in data.items():
        setattr(device, field, value)
    await session.commit()
    return device


async def update_device_status(
    session: AsyncSession,
    device_id: uuid.UUID,
    tenant_id: uuid.UUID,
    payload: DeviceStatusUpdate,
) -> Device:
    """Heartbeat: меняет статус устройства и фиксирует время последнего контакта."""
    device = await get_device(session, device_id, tenant_id)
    device.status = payload.status
    device.last_seen_at = datetime.now(UTC)
    await session.commit()
    return device


async def delete_device(session: AsyncSession, device_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
    """Удаляет устройство тенанта."""
    device = await get_device(session, device_id, tenant_id)
    await session.delete(device)
    await session.commit()

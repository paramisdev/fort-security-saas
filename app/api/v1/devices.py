"""Эндпоинты оборудования."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_tenant_id
from app.core.db import get_session
from app.models.device import Device
from app.models.enums import DeviceStatus, DeviceType, UserRole
from app.schemas.device import (
    DeviceCreate,
    DeviceRead,
    DeviceStatusUpdate,
    DeviceUpdate,
)
from app.services import security_object as device_service
from app.services.errors import (
    ConflictError,
    LimitExceededError,
    NoActiveSubscriptionError,
    NotFoundError,
)

router = APIRouter(prefix="/devices", tags=["devices"])

tenant_read = require_tenant_id(UserRole.TENANT_ADMIN, UserRole.CLIENT)
tenant_write = require_tenant_id(UserRole.TENANT_ADMIN)


@router.get("", response_model=list[DeviceRead])
async def list_devices(
    tenant_id: uuid.UUID = Depends(tenant_read),
    session: AsyncSession = Depends(get_session),
    object_id: uuid.UUID | None = Query(default=None),
    type: DeviceType | None = Query(default=None),
    status: DeviceStatus | None = Query(default=None),
) -> list:
    """Список устройств тенанта с фильтрами (TenantAdmin и Client)."""
    return await device_service.list_devices(
        session, tenant_id, object_id=object_id, device_type=type, status=status
    )


@router.post("", response_model=DeviceRead, status_code=201)
async def create_device(
    payload: DeviceCreate,
    tenant_id: uuid.UUID = Depends(tenant_write),
    session: AsyncSession = Depends(get_session),
) -> Device:
    """Регистрация устройства (TenantAdmin; проверяется лимит тарифа)."""
    try:
        return await device_service.create_device(session, tenant_id, payload)
    except (LimitExceededError, NoActiveSubscriptionError, ConflictError, NotFoundError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None


@router.get("/{device_id}", response_model=DeviceRead)
async def get_device(
    device_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(tenant_read),
    session: AsyncSession = Depends(get_session),
) -> Device:
    """Устройство по id (только своего тенанта; чужой id вернёт 404)."""
    try:
        return await device_service.get_device(session, device_id, tenant_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None


@router.patch("/{device_id}", response_model=DeviceRead)
async def update_device(
    device_id: uuid.UUID,
    payload: DeviceUpdate,
    tenant_id: uuid.UUID = Depends(tenant_write),
    session: AsyncSession = Depends(get_session),
) -> Device:
    """Частичное обновление устройства (TenantAdmin)."""
    try:
        return await device_service.update_device(session, device_id, tenant_id, payload)
    except (NotFoundError, ConflictError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None


@router.patch("/{device_id}/status", response_model=DeviceRead)
async def update_device_status(
    device_id: uuid.UUID,
    payload: DeviceStatusUpdate,
    tenant_id: uuid.UUID = Depends(tenant_write),
    session: AsyncSession = Depends(get_session),
) -> Device:
    """Heartbeat: смена статуса online/offline (TenantAdmin)."""
    try:
        return await device_service.update_device_status(session, device_id, tenant_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(tenant_write),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Удаление устройства (TenantAdmin)."""
    try:
        await device_service.delete_device(session, device_id, tenant_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None

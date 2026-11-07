"""Эндпоинты охраняемых объектов."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_tenant_id
from app.core.db import get_session
from app.models.enums import UserRole
from app.models.security_object import SecurityObject
from app.schemas.security_object import ObjectCreate, ObjectRead, ObjectUpdate
from app.services import security_object as object_service
from app.services.errors import LimitExceededError, NoActiveSubscriptionError, NotFoundError

router = APIRouter(prefix="/objects", tags=["objects"])

tenant_read = require_tenant_id(UserRole.TENANT_ADMIN, UserRole.CLIENT)
tenant_write = require_tenant_id(UserRole.TENANT_ADMIN)


@router.get("", response_model=list[ObjectRead])
async def list_objects(
    tenant_id: uuid.UUID = Depends(tenant_read),
    session: AsyncSession = Depends(get_session),
) -> list:
    """Список объектов тенанта (TenantAdmin и Client)."""
    return await object_service.list_objects(session, tenant_id)


@router.post("", response_model=ObjectRead, status_code=201)
async def create_object(
    payload: ObjectCreate,
    tenant_id: uuid.UUID = Depends(tenant_write),
    session: AsyncSession = Depends(get_session),
) -> SecurityObject:
    """Создание объекта (TenantAdmin; проверяется лимит тарифа)."""
    try:
        return await object_service.create_object(session, tenant_id, payload)
    except (LimitExceededError, NoActiveSubscriptionError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None


@router.get("/{object_id}", response_model=ObjectRead)
async def get_object(
    object_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(tenant_read),
    session: AsyncSession = Depends(get_session),
) -> SecurityObject:
    """Объект по id (только своего тенанта; чужой id вернёт 404)."""
    try:
        return await object_service.get_object(session, object_id, tenant_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None


@router.patch("/{object_id}", response_model=ObjectRead)
async def update_object(
    object_id: uuid.UUID,
    payload: ObjectUpdate,
    tenant_id: uuid.UUID = Depends(tenant_write),
    session: AsyncSession = Depends(get_session),
) -> SecurityObject:
    """Частичное обновление объекта (TenantAdmin)."""
    try:
        return await object_service.update_object(session, object_id, tenant_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None


@router.delete("/{object_id}", status_code=204)
async def delete_object(
    object_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(tenant_write),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Удаление объекта (TenantAdmin). Привязанные устройства открепляются."""
    try:
        await object_service.delete_object(session, object_id, tenant_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None

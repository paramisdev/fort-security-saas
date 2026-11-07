"""Эндпоинты тарифов: публичный каталог + управление SuperAdmin."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.db import get_session
from app.models.enums import UserRole
from app.models.tariff import Tariff
from app.models.user import User
from app.repositories.tariff import TariffRepository
from app.schemas.tariff import TariffCreate, TariffRead, TariffUpdate
from app.services import tariff as tariff_service
from app.services.errors import ConflictError, NotFoundError

router = APIRouter(prefix="/tariffs", tags=["tariffs"])

superadmin_only = require_roles(UserRole.SUPERADMIN)


@router.get("", response_model=list[TariffRead])
async def list_tariffs(session: AsyncSession = Depends(get_session)) -> list:
    """Публичный каталог активных тарифов."""
    return await tariff_service.list_tariffs(session, only_active=True)


@router.post("", response_model=TariffRead, status_code=status.HTTP_201_CREATED)
async def create_tariff(
    payload: TariffCreate,
    _user: User = Depends(superadmin_only),
    session: AsyncSession = Depends(get_session),
) -> Tariff:
    """Создание тарифа (только SuperAdmin)."""
    try:
        return await tariff_service.create_tariff(session, payload)
    except ConflictError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None


@router.patch("/{tariff_id}", response_model=TariffRead)
async def update_tariff(
    tariff_id: uuid.UUID,
    payload: TariffUpdate,
    _user: User = Depends(superadmin_only),
    session: AsyncSession = Depends(get_session),
) -> Tariff:
    """Частичное обновление тарифа (только SuperAdmin)."""
    try:
        return await tariff_service.update_tariff(session, tariff_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from None


@router.get("/{tariff_id}", response_model=TariffRead)
async def get_tariff(tariff_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Tariff:
    """Получение тарифа по id (публично по id, авторизация не требуется)."""
    tariff = await TariffRepository(session).get_by_id(tariff_id)
    if tariff is None:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return tariff

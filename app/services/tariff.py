"""Сервис тарифов."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tariff import Tariff
from app.repositories.tariff import TariffRepository
from app.schemas.tariff import TariffCreate, TariffUpdate
from app.services.errors import ConflictError, NotFoundError


async def list_tariffs(session: AsyncSession, *, only_active: bool = True) -> list[Tariff]:
    """Список тарифов. Публичный каталог показывает только активные."""
    repo = TariffRepository(session)
    tariffs = await repo.list_all()
    if only_active:
        return [t for t in tariffs if t.is_active]
    return tariffs


async def create_tariff(session: AsyncSession, payload: TariffCreate) -> Tariff:
    """Создаёт новый тариф (SuperAdmin)."""
    repo = TariffRepository(session)
    if await repo.get_by_code(payload.code):
        raise ConflictError(f"Tariff code '{payload.code}' already exists")
    tariff = Tariff(**payload.model_dump())
    await repo.add(tariff)
    await session.commit()
    return tariff


async def update_tariff(
    session: AsyncSession, tariff_id: uuid.UUID, payload: TariffUpdate
) -> Tariff:
    """Частично обновляет тариф (SuperAdmin)."""
    repo = TariffRepository(session)
    tariff = await repo.get_by_id(tariff_id)
    if tariff is None:
        raise NotFoundError("Tariff not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tariff, field, value)
    await session.commit()
    return tariff

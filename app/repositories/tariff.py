"""Репозиторий тарифов."""

from sqlalchemy import select

from app.models.tariff import Tariff
from app.repositories.base import BaseRepository


class TariffRepository(BaseRepository[Tariff]):
    """Доступ к данным тарифов."""

    model = Tariff

    async def get_by_code(self, code: str) -> Tariff | None:
        """Возвращает тариф по коду."""
        result = await self.session.execute(select(Tariff).where(Tariff.code == code))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Tariff]:
        """Возвращает все тарифы (включая неактивные — фильтрует роут/сервис)."""
        result = await self.session.execute(select(Tariff).order_by(Tariff.price_monthly))
        return list(result.scalars().all())

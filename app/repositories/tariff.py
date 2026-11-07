from sqlalchemy import select

from app.models.tariff import Tariff
from app.repositories.base import BaseRepository


class TariffRepository(BaseRepository[Tariff]):
    model = Tariff

    async def get_by_code(self, code: str) -> Tariff | None:
        result = await self.session.execute(select(Tariff).where(Tariff.code == code))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Tariff]:
        result = await self.session.execute(select(Tariff).order_by(Tariff.price_monthly))
        return list(result.scalars().all())

"""Репозиторий тенантов."""

from sqlalchemy import select

from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Доступ к данным тенантов."""

    model = Tenant

    async def get_by_slug(self, slug: str) -> Tenant | None:
        """Возвращает тенанта по slug."""
        result = await self.session.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()

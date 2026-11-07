"""Репозиторий охраняемых объектов."""

import uuid

from sqlalchemy import func, select

from app.models.security_object import SecurityObject
from app.repositories.base import BaseRepository


class SecurityObjectRepository(BaseRepository[SecurityObject]):
    """Доступ к данным объектов (всегда с фильтром по tenant_id)."""

    model = SecurityObject

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[SecurityObject]:
        """Возвращает объекты тенанта."""
        result = await self.session.execute(
            select(SecurityObject)
            .where(SecurityObject.tenant_id == tenant_id)
            .order_by(SecurityObject.created_at)
        )
        return list(result.scalars().all())

    async def get_in_tenant(
        self, object_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> SecurityObject | None:
        """Возвращает объект только если он принадлежит тенанту."""
        result = await self.session.execute(
            select(SecurityObject).where(
                SecurityObject.id == object_id, SecurityObject.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()

    async def count_by_tenant(self, tenant_id: uuid.UUID) -> int:
        """Количество объектов тенанта (для лимита тарифа)."""
        result = await self.session.execute(
            select(func.count())
            .select_from(SecurityObject)
            .where(SecurityObject.tenant_id == tenant_id)
        )
        return int(result.scalar_one())

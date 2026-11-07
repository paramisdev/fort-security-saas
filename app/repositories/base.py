"""Базовый репозиторий с типовыми операциями над сессией."""

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Обёртка над AsyncSession для CRUD одной модели."""

    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: Any) -> ModelType | None:
        """Возвращает запись по первичному ключу."""
        return await self.session.get(self.model, entity_id)

    async def add(self, entity: ModelType) -> ModelType:
        """Добавляет запись (без коммита — коммитами управляет сервис/роут)."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def list_all(self) -> list[ModelType]:
        """Возвращает все записи модели."""
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())

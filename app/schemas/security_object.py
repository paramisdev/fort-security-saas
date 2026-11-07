"""Pydantic-схемы охраняемых объектов."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ObjectType


class ObjectCreate(BaseModel):
    """Создание объекта охраны."""

    name: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=500)
    type: ObjectType


class ObjectUpdate(BaseModel):
    """Частичное обновление объекта охраны."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, min_length=1, max_length=500)
    type: ObjectType | None = None


class ObjectRead(BaseModel):
    """Объект охраны в ответах API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    address: str
    type: ObjectType
    created_at: datetime

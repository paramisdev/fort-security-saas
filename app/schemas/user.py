"""Pydantic-схемы пользователей."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class UserCreate(BaseModel):
    """Данные для создания пользователя внутри тенанта."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.CLIENT


class TenantAdminCreate(BaseModel):
    """Данные первого пользователя при регистрации тенанта."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=255)


class UserRead(BaseModel):
    """Пользователь в ответах API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    tenant_id: uuid.UUID | None
    is_active: bool
    created_at: datetime

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TariffBase(BaseModel):
    code: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=255)
    price_monthly: float = Field(ge=0)
    max_objects: int = Field(ge=1)
    max_devices: int = Field(ge=1)
    features: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class TariffCreate(TariffBase): ...


class TariffUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    price_monthly: float | None = Field(default=None, ge=0)
    max_objects: int | None = Field(default=None, ge=1)
    max_devices: int | None = Field(default=None, ge=1)
    features: dict[str, Any] | None = None
    is_active: bool | None = None


class TariffRead(TariffBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime

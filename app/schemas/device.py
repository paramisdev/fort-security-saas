import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DeviceStatus, DeviceType


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: DeviceType
    serial_number: str = Field(min_length=1, max_length=100)
    object_id: uuid.UUID | None = None


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: DeviceType | None = None
    object_id: uuid.UUID | None = None


class DeviceStatusUpdate(BaseModel):
    status: DeviceStatus


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    object_id: uuid.UUID | None
    name: str
    type: DeviceType
    status: DeviceStatus
    serial_number: str
    last_seen_at: datetime | None
    created_at: datetime

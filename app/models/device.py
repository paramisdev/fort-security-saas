"""Модель устройства (датчик, камера, замок)."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.security_object import SecurityObject
    from app.models.tenant import Tenant


class Device(Base, UUIDPkMixin, TimestampMixin):
    """Оборудование тенанта. Серийный номер уникален в рамках тенанта."""

    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "serial_number", name="uq_devices_tenant_serial"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    object_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("objects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="offline", server_default="offline")
    serial_number: Mapped[str] = mapped_column(String(100))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="devices")
    object: Mapped["SecurityObject | None"] = relationship(back_populates="devices")

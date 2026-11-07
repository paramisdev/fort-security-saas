"""Модель охраняемого объекта (квартира, офис и т.д.)."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.tenant import Tenant


class SecurityObject(Base, UUIDPkMixin, TimestampMixin):
    """Объект охраны, принадлежащий тенанту."""

    __tablename__ = "objects"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(500))
    type: Mapped[str] = mapped_column(String(20))

    tenant: Mapped["Tenant"] = relationship(back_populates="objects")
    devices: Mapped[list["Device"]] = relationship(back_populates="object")

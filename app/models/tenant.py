"""Модель компании-тенанта."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.security_object import SecurityObject
    from app.models.subscription import Subscription
    from app.models.user import User


class Tenant(Base, UUIDPkMixin, TimestampMixin):
    """Компания-арендатор (tenant) — корень изоляции данных."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="tenant")
    objects: Mapped[list["SecurityObject"]] = relationship(back_populates="tenant")
    devices: Mapped[list["Device"]] = relationship(back_populates="tenant")

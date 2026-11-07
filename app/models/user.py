"""Модель пользователя."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPkMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class User(Base, UUIDPkMixin, TimestampMixin):
    """Пользователь платформы. У SuperAdmin tenant_id отсутствует."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(String(20))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    tenant: Mapped["Tenant | None"] = relationship(back_populates="users")

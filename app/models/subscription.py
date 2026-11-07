import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.tariff import Tariff
    from app.models.tenant import Tenant


class Subscription(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "subscriptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    tariff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tariffs.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(20), index=True)
    period_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    period_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="subscriptions")
    tariff: Mapped["Tariff"] = relationship()
    payments: Mapped[list["Payment"]] = relationship(back_populates="subscription")

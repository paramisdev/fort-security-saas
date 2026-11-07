"""Модель платежа (заглушка оплаты)."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPkMixin

if TYPE_CHECKING:
    from app.models.subscription import Subscription
    from app.models.tariff import Tariff


class Payment(Base, UUIDPkMixin, TimestampMixin):
    """Платёж по подписке. В MVP создаётся заглушкой со статусом succeeded."""

    __tablename__ = "payments"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"), index=True
    )
    tariff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tariffs.id", ondelete="RESTRICT"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), index=True)

    subscription: Mapped["Subscription"] = relationship(back_populates="payments")
    tariff: Mapped["Tariff"] = relationship()

"""Репозитории подписок и платежей."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models.enums import PaymentStatus, SubscriptionStatus
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.repositories.base import BaseRepository

SUBSCRIPTION_PERIOD_DAYS = 30


class SubscriptionRepository(BaseRepository[Subscription]):
    """Доступ к данным подписок."""

    model = Subscription

    async def get_active(self, tenant_id: uuid.UUID) -> Subscription | None:
        """Возвращает активную подписку тенанта (благодаря unique-индексу их <= 1)."""
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.tenant_id == tenant_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def create_active(self, tenant_id: uuid.UUID, tariff_id: uuid.UUID) -> Subscription:
        """Создаёт новую активную подписку на период 30 дней."""
        subscription = Subscription(
            tenant_id=tenant_id,
            tariff_id=tariff_id,
            status=SubscriptionStatus.ACTIVE,
            period_started_at=datetime.now(UTC),
            period_expires_at=datetime.now(UTC) + timedelta(days=SUBSCRIPTION_PERIOD_DAYS),
        )
        self.session.add(subscription)
        await self.session.flush()
        return subscription


class PaymentRepository(BaseRepository[Payment]):
    """Доступ к данным платежей."""

    model = Payment

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        subscription_id: uuid.UUID,
        tariff_id: uuid.UUID,
        amount: float,
        status: PaymentStatus,
    ) -> Payment:
        """Создаёт запись о платеже."""
        payment = Payment(
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            tariff_id=tariff_id,
            amount=amount,
            status=status,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[Payment]:
        """Все платежи тенанта."""
        result = await self.session.execute(
            select(Payment).where(Payment.tenant_id == tenant_id).order_by(Payment.created_at)
        )
        return list(result.scalars().all())

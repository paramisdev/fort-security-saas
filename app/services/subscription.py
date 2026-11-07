import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PaymentStatus, SubscriptionStatus
from app.models.subscription import Subscription
from app.repositories.subscription import PaymentRepository, SubscriptionRepository
from app.repositories.tariff import TariffRepository
from app.services.errors import NotFoundError


async def get_current_subscription(session: AsyncSession, tenant_id: uuid.UUID) -> Subscription:
    subscription = await SubscriptionRepository(session).get_active(tenant_id)
    if subscription is None:
        raise NotFoundError("No active subscription")
    await session.refresh(subscription, ["tariff"])
    return subscription


async def change_tariff(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    tariff_code: str,
) -> Subscription:
    """Меняет тариф тенанта: фиксирует оплату, запись платежа и новую подписку."""
    tariff = await TariffRepository(session).get_by_code(tariff_code)
    if tariff is None or not tariff.is_active:
        raise NotFoundError(f"Tariff '{tariff_code}' not found")

    subscription_repo = SubscriptionRepository(session)
    payment_repo = PaymentRepository(session)

    # Оплата за новый период (в MVP всегда успешна).
    payment_status = PaymentStatus.SUCCEEDED

    # Деактивируем прежнюю активную подписку (unique-индекс не даст двух активных).
    old_subscription = await subscription_repo.get_active(tenant_id)
    if old_subscription is not None:
        old_subscription.status = SubscriptionStatus.CANCELLED

    new_subscription = await subscription_repo.create_active(tenant_id, tariff.id)
    await payment_repo.create(
        tenant_id=tenant_id,
        subscription_id=new_subscription.id,
        tariff_id=tariff.id,
        amount=float(tariff.price_monthly),
        status=payment_status,
    )
    await session.commit()
    await session.refresh(new_subscription, ["tariff"])
    return new_subscription

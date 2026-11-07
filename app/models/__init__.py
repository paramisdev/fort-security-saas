"""Импорт всех моделей для регистрации метаданных (нужно Alembic autogenerate)."""

from app.models.base import Base
from app.models.device import Device
from app.models.enums import (
    DeviceStatus,
    DeviceType,
    ObjectType,
    PaymentStatus,
    SubscriptionStatus,
    TenantStatus,
    UserRole,
)
from app.models.payment import Payment
from app.models.security_object import SecurityObject
from app.models.subscription import Subscription
from app.models.tariff import Tariff
from app.models.tenant import Tenant
from app.models.user import User

__all__ = [
    "Base",
    "Device",
    "DeviceStatus",
    "DeviceType",
    "ObjectType",
    "Payment",
    "PaymentStatus",
    "SecurityObject",
    "Subscription",
    "SubscriptionStatus",
    "Tariff",
    "Tenant",
    "TenantStatus",
    "User",
    "UserRole",
]

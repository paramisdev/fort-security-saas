"""Перечисления, используемые в моделях и схемах."""

from enum import StrEnum


class UserRole(StrEnum):
    """Роли пользователей платформы."""

    SUPERADMIN = "superadmin"
    TENANT_ADMIN = "tenant_admin"
    CLIENT = "client"


class TenantStatus(StrEnum):
    """Статус компании-тенанта."""

    ACTIVE = "active"
    BLOCKED = "blocked"


class SubscriptionStatus(StrEnum):
    """Статус подписки тенанта на тариф."""

    ACTIVE = "active"
    PENDING = "pending"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(StrEnum):
    """Статус платежа (в MVP — заглушка)."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ObjectType(StrEnum):
    """Тип охраняемого объекта."""

    APARTMENT = "apartment"
    OFFICE = "office"
    HOUSE = "house"
    OTHER = "other"


class DeviceType(StrEnum):
    """Тип оборудования."""

    SENSOR = "sensor"
    CAMERA = "camera"
    LOCK = "lock"


class DeviceStatus(StrEnum):
    """Статус оборудования."""

    ONLINE = "online"
    OFFLINE = "offline"

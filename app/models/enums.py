from enum import StrEnum


class UserRole(StrEnum):
    SUPERADMIN = "superadmin"
    TENANT_ADMIN = "tenant_admin"
    CLIENT = "client"


class TenantStatus(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PENDING = "pending"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ObjectType(StrEnum):
    APARTMENT = "apartment"
    OFFICE = "office"
    HOUSE = "house"
    OTHER = "other"


class DeviceType(StrEnum):
    SENSOR = "sensor"
    CAMERA = "camera"
    LOCK = "lock"


class DeviceStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"

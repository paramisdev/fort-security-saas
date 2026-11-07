"""Общие ошибки сервисов (маппятся на HTTP-коды на уровне роутов)."""


class ServiceError(Exception):
    """Базовая ошибка сервисного слоя."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ServiceError):
    """Сущность не найдена."""

    status_code = 404


class LimitExceededError(ServiceError):
    """Превышен лимит активного тарифа."""

    status_code = 403


class NoActiveSubscriptionError(ServiceError):
    """У тенанта нет активной подписки."""

    status_code = 403


class ConflictError(ServiceError):
    """Конфликт данных (например, дубликат серийного номера)."""

    status_code = 409

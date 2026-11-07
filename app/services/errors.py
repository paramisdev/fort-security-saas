class ServiceError(Exception):
    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ServiceError):
    status_code = 404


class LimitExceededError(ServiceError):
    status_code = 403


class NoActiveSubscriptionError(ServiceError):
    status_code = 403


class ConflictError(ServiceError):
    status_code = 409

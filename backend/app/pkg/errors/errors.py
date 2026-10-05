"""Domain error hierarchy. The API layer maps these to HTTP statuses."""


class DomainError(Exception):
    """Base class; `message` is safe to show to clients."""

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.default_message)
        self.message = message or self.default_message

    default_message = "Domain error"


class NotFound(DomainError):
    default_message = "Resource not found"


class Conflict(DomainError):
    default_message = "Resource already exists"


class Unauthorized(DomainError):
    default_message = "Authentication required"


class Forbidden(DomainError):
    default_message = "Not enough permissions"


class ValidationFailed(DomainError):
    default_message = "Validation failed"


class PayloadTooLarge(DomainError):
    default_message = "Payload too large"


class ServiceUnavailable(DomainError):
    default_message = "Service unavailable"

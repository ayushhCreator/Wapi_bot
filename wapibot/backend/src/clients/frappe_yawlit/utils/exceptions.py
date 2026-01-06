"""Exception classes for Frappe API client.

Provides specific exception types for different error scenarios.
"""


class FrappeAPIError(Exception):
    """Base exception for all Frappe API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict | None = None,
    ):
        """Initialize exception with detailed error information.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
            response_data: Raw response data from API
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(FrappeAPIError):
    """Authentication failed (401, 403)."""

    pass


class ValidationError(FrappeAPIError):
    """Request validation failed (422)."""

    pass


class NotFoundError(FrappeAPIError):
    """Resource not found (404)."""

    pass


class ServerError(FrappeAPIError):
    """Server error (500+)."""

    pass


class NetworkError(FrappeAPIError):
    """Network/connection error."""

    pass


class TimeoutError(FrappeAPIError):
    """Request timeout error."""

    pass

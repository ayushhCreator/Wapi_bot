"""Async HTTP client for Frappe API.

Provides async HTTP methods with retry logic, logging, and error handling.
"""

import logging
from typing import Any, Dict, Set
import httpx

from clients.frappe_yawlit.config import FrappeClientConfig
from clients.frappe_yawlit.utils.exceptions import (
    AuthenticationError,
    NetworkError,
    NotFoundError,
    ServerError,
    TimeoutError,
    ValidationError,
    FrappeAPIError
)

logger = logging.getLogger(__name__)

# Sensitive fields that should never be logged
SENSITIVE_FIELDS: Set[str] = {
    "password", "api_key", "api_secret", "token", "secret",
    "authorization", "cookie", "session", "sid", "otp",
    "credit_card", "cvv", "ssn", "phone_number", "email"
}


def _sanitize_for_logging(data: Any, depth: int = 0) -> Any:
    """Recursively sanitize sensitive data for logging.

    Args:
        data: Data to sanitize (dict, list, or primitive)
        depth: Recursion depth (prevents infinite loops)

    Returns:
        Sanitized data safe for logging
    """
    if depth > 5:  # Prevent deep recursion
        return "[MAX_DEPTH]"

    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            # Check if key contains any sensitive field name
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = _sanitize_for_logging(value, depth + 1)
        return sanitized
    elif isinstance(data, list):
        return [_sanitize_for_logging(item, depth + 1) for item in data]
    else:
        return data


class AsyncHTTPClient:
    """Async HTTP client for Frappe API with retry logic."""

    def __init__(self, config: FrappeClientConfig, max_retries: int = 3):
        """Initialize HTTP client with security hardening.

        Args:
            config: Frappe client configuration
            max_retries: Maximum number of retries for failed requests
        """
        self.config = config
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            follow_redirects=False,  # Security: Prevent open redirect attacks
            verify=True  # Security: Explicitly verify SSL certificates
        )

    async def close(self) -> None:
        """Close HTTP client session."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP errors and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Raises:
            Appropriate FrappeAPIError subclass based on status code
        """
        status_code = response.status_code

        # Try to parse error message from response
        try:
            error_data = response.json()
            message = error_data.get("message") or error_data.get("error") or response.text
        except Exception:
            error_data = {}
            message = response.text or f"HTTP {status_code} error"

        # Security: Sanitize error data to prevent information leakage
        sanitized_error_data = _sanitize_for_logging(error_data)

        # Map status codes to exception types
        if status_code in (401, 403):
            raise AuthenticationError(message, status_code, sanitized_error_data)
        elif status_code == 404:
            raise NotFoundError(message, status_code, sanitized_error_data)
        elif status_code == 422:
            raise ValidationError(message, status_code, sanitized_error_data)
        elif status_code >= 500:
            raise ServerError(message, status_code, sanitized_error_data)
        else:
            raise FrappeAPIError(message, status_code, sanitized_error_data)

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] | None = None,
        params: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            NetworkError: Network/connection error
            TimeoutError: Request timeout
            FrappeAPIError: API error response
        """
        url = f"{self.config.base_url}{endpoint}"
        headers = self.config.get_auth_headers()

        logger.debug(f"{method} {url}")
        if data:
            # Security: Sanitize sensitive data before logging
            sanitized_data = _sanitize_for_logging(data)
            logger.debug(f"Request data: {sanitized_data}")

        retries = 0
        last_exception = None

        while retries < self.max_retries:
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )

                # Check for HTTP errors
                if response.status_code >= 400:
                    self._handle_error(response)

                # Parse and return response
                result = response.json()
                # Security: Sanitize sensitive data before logging
                sanitized_result = _sanitize_for_logging(result)
                logger.debug(f"Response: {sanitized_result}")
                return result

            except httpx.TimeoutException as e:
                retries += 1
                last_exception = e
                logger.warning(f"Request timeout (attempt {retries}/{self.max_retries}): {url}")
                if retries >= self.max_retries:
                    raise TimeoutError(f"Request timed out after {self.max_retries} attempts") from e

            except httpx.NetworkError as e:
                retries += 1
                last_exception = e
                logger.warning(f"Network error (attempt {retries}/{self.max_retries}): {url}")
                if retries >= self.max_retries:
                    raise NetworkError(f"Network error after {self.max_retries} attempts: {str(e)}") from e

            except FrappeAPIError:
                # Don't retry API errors (4xx, 5xx)
                raise

            except Exception as e:
                logger.error(f"Unexpected error in HTTP request: {e}")
                raise FrappeAPIError(f"Unexpected error: {str(e)}") from e

        # Should never reach here
        if last_exception:
            raise NetworkError(f"Request failed after {self.max_retries} retries") from last_exception

    async def get(self, endpoint: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Make GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Make POST request.

        Args:
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Parsed JSON response
        """
        return await self._request("POST", endpoint, data=data)

    async def put(self, endpoint: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Make PUT request.

        Args:
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Parsed JSON response
        """
        return await self._request("PUT", endpoint, data=data)

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request.

        Args:
            endpoint: API endpoint path

        Returns:
            Parsed JSON response
        """
        return await self._request("DELETE", endpoint)

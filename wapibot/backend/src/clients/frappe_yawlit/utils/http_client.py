"""Async HTTP client for Frappe API.

Provides async HTTP methods with retry logic, logging, and error handling.
"""

import logging
from typing import Any, Dict
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


class AsyncHTTPClient:
    """Async HTTP client for Frappe API with retry logic."""

    def __init__(self, config: FrappeClientConfig, max_retries: int = 3):
        """Initialize HTTP client.

        Args:
            config: Frappe client configuration
            max_retries: Maximum number of retries for failed requests
        """
        self.config = config
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            follow_redirects=True
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
            message = response.text or f"HTTP {status_code} error"

        # Map status codes to exception types
        if status_code in (401, 403):
            raise AuthenticationError(message, status_code, error_data if 'error_data' in locals() else None)
        elif status_code == 404:
            raise NotFoundError(message, status_code, error_data if 'error_data' in locals() else None)
        elif status_code == 422:
            raise ValidationError(message, status_code, error_data if 'error_data' in locals() else None)
        elif status_code >= 500:
            raise ServerError(message, status_code, error_data if 'error_data' in locals() else None)
        else:
            raise FrappeAPIError(message, status_code, error_data if 'error_data' in locals() else None)

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
            logger.debug(f"Request data: {data}")

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
                logger.debug(f"Response: {result}")
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

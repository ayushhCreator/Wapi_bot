"""Configuration for Frappe API client.

Reads from .env.txt via core.config settings.
"""

import logging
from typing import Dict

from core.config import settings

logger = logging.getLogger(__name__)


class FrappeClientConfig:
    """Configuration manager for Frappe API client."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize Frappe client configuration.

        Args:
            base_url: Frappe base URL (defaults to settings.frappe_base_url)
            api_key: API key for authentication (defaults to settings.frappe_api_key)
            api_secret: API secret (defaults to settings.frappe_api_secret)
            timeout: Request timeout in seconds
        """
        # Use provided values or fall back to settings from .env.txt
        self.base_url = (base_url or settings.frappe_base_url).rstrip("/")
        self.api_key = api_key or settings.frappe_api_key
        self.api_secret = api_secret or settings.frappe_api_secret
        self.timeout = timeout

        # Session token (set after login)
        self.session_token: str | None = None

        logger.info(f"Frappe client configured for: {self.base_url}")

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests.

        Returns:
            Dict of headers with authentication
        """
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # Use session token if available (after login)
        if self.session_token:
            headers["Cookie"] = f"sid={self.session_token}"

        # Use API key/secret if provided (for programmatic access)
        elif self.api_key and self.api_secret:
            headers["Authorization"] = f"token {self.api_key}:{self.api_secret}"

        return headers

    def set_session(self, token: str) -> None:
        """Set session token after successful login.

        Args:
            token: Session token from login response
        """
        self.session_token = token
        logger.debug("Session token updated")

    def clear_session(self) -> None:
        """Clear session token (logout)."""
        self.session_token = None
        logger.debug("Session cleared")

"""Yawlit Frappe API Client - Production-ready async client.

Improved version with async support, proper error handling, and type safety.
Reads configuration from .env.txt via core.config settings.

Example:
    >>> from clients.frappe_yawlit import YawlitClient
    >>>
    >>> # Initialize client (reads from .env.txt)
    >>> client = YawlitClient()
    >>>
    >>> # Or override configuration
    >>> client = YawlitClient(
    ...     base_url="https://yawlit.duckdns.org",
    ...     api_key="your_key",
    ...     api_secret="your_secret"
    ... )
    >>>
    >>> # Use async context manager for automatic cleanup
    >>> async with client:
    ...     # Login
    ...     result = await client.auth.login_email("user@example.com", "password")
    ...
    ...     # Get profile
    ...     profile = await client.customer_profile.get_profile()
    ...
    ...     # Create booking
    ...     booking = await client.booking_create.create_booking({
    ...         "service_id": "service_id",
    ...         "slot_id": "slot_id"
    ...     })
"""

import logging
from typing import Any

from clients.frappe_yawlit.config import FrappeClientConfig
from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient

# Auth
from clients.frappe_yawlit.auth import AuthClient

# Customer
from clients.frappe_yawlit.customer import (
    ProfileClient,
    AddressClient,
    CustomerLookupClient
)

# Booking
from clients.frappe_yawlit.booking import (
    BookingCreateClient,
    BookingManageClient,
    ServiceCatalogClient,
    SlotAvailabilityClient
)

# Subscription
from clients.frappe_yawlit.subscription import (
    SubscriptionPlansClient,
    SubscriptionManageClient,
    SubscriptionUsageClient
)

# Payment
from clients.frappe_yawlit.payment import PaymentClient

# Vendor
from clients.frappe_yawlit.vendor import VendorPortalClient

# Admin
from clients.frappe_yawlit.admin import (
    AdminDashboardClient,
    AdminBookingClient
)

logger = logging.getLogger(__name__)


class YawlitClient:
    """Main Yawlit Frappe API client.

    Provides async access to all Yawlit backend services through specialized sub-clients.
    Automatically reads configuration from .env.txt via core.config settings.

    Attributes:
        auth: Authentication operations
        customer_profile: Customer profile management
        customer_address: Customer address management
        customer_lookup: Customer lookup (chatbot integration)
        booking_create: Booking creation
        booking_manage: Booking management
        service_catalog: Service catalog browsing
        slot_availability: Slot availability checking
        subscription_plans: Subscription plans
        subscription_manage: Subscription management
        subscription_usage: Subscription usage tracking
        payment: Payment operations
        vendor_portal: Vendor portal operations
        admin_dashboard: Admin dashboard
        admin_booking: Admin booking management
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """Initialize Yawlit API client.

        Args:
            base_url: Frappe base URL (defaults to FRAPPE_BASE_URL from .env.txt)
            api_key: API key for authentication (defaults to FRAPPE_API_KEY from .env.txt)
            api_secret: API secret (defaults to FRAPPE_API_SECRET from .env.txt)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests

        Example:
            >>> # Use settings from .env.txt
            >>> client = YawlitClient()
            >>>
            >>> # Override with custom configuration
            >>> client = YawlitClient(
            ...     base_url="https://yawlit.duckdns.org",
            ...     timeout=60.0
            ... )
        """
        # Create configuration
        self.config = FrappeClientConfig(
            base_url=base_url,
            api_key=api_key,
            api_secret=api_secret,
            timeout=timeout
        )

        # Create HTTP client
        self.http_client = AsyncHTTPClient(self.config, max_retries=max_retries)

        # Initialize all sub-clients
        self.auth = AuthClient(self.http_client)
        self.customer_profile = ProfileClient(self.http_client)
        self.customer_address = AddressClient(self.http_client)
        self.customer_lookup = CustomerLookupClient(self.http_client)
        self.booking_create = BookingCreateClient(self.http_client)
        self.booking_manage = BookingManageClient(self.http_client)
        self.service_catalog = ServiceCatalogClient(self.http_client)
        self.slot_availability = SlotAvailabilityClient(self.http_client)
        self.subscription_plans = SubscriptionPlansClient(self.http_client)
        self.subscription_manage = SubscriptionManageClient(self.http_client)
        self.subscription_usage = SubscriptionUsageClient(self.http_client)
        self.payment = PaymentClient(self.http_client)
        self.vendor_portal = VendorPortalClient(self.http_client)
        self.admin_dashboard = AdminDashboardClient(self.http_client)
        self.admin_booking = AdminBookingClient(self.http_client)

        logger.info(f"YawlitClient initialized for {self.config.base_url}")

    async def close(self) -> None:
        """Close HTTP client session.

        Call this when done using the client to clean up resources.

        Example:
            >>> client = YawlitClient()
            >>> try:
            ...     result = await client.auth.login_email("user@example.com", "pass")
            ... finally:
            ...     await client.close()
        """
        await self.http_client.close()
        logger.info("YawlitClient closed")

    async def __aenter__(self):
        """Async context manager entry.

        Example:
            >>> async with YawlitClient() as client:
            ...     profile = await client.customer_profile.get_profile()
        """
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def set_session(self, token: str) -> None:
        """Set session token for authenticated requests.

        Args:
            token: Session token from login response

        Example:
            >>> client = YawlitClient()
            >>> result = await client.auth.login_email("user@example.com", "pass")
            >>> client.set_session(result["session_token"])
        """
        self.config.set_session(token)

    def clear_session(self) -> None:
        """Clear session token (logout).

        Example:
            >>> await client.auth.logout()
            >>> client.clear_session()
        """
        self.config.clear_session()


__all__ = ["YawlitClient"]

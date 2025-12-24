"""Booking creation client for Frappe API.

Handles one-time booking creation and price calculation.
"""

from typing import Dict, Any
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class BookingCreateClient:
    """Handle booking creation operations for one-time services."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize booking create client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def create_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new one-time booking.

        Args:
            booking_data: Booking information including:
                - service_id: Service to book
                - vehicle_id: Vehicle for service
                - slot_id: Time slot ID
                - date: Booking date
                - address_id: Service location address
                - optional_addons: List of addon IDs (optional)
                - special_instructions: Customer notes (optional)

        Returns:
            Created booking details with booking ID and payment info

        Example:
            >>> result = await client.booking_create.create_booking({
            ...     "service_id": "SRV-2025-001",
            ...     "vehicle_id": "VEH-2025-001",
            ...     "slot_id": "SLOT-2025-001",
            ...     "date": "2025-01-15",
            ...     "address_id": "ADDR-2025-001",
            ...     "optional_addons": ["ADDON-001", "ADDON-002"],
            ...     "special_instructions": "Please call before arrival"
            ... })
            >>> print(result["booking_id"])
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.create_booking",
                booking_data
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error creating booking: {e}")
            raise

    async def calculate_price(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate booking price before creating booking.

        Args:
            price_data: Price calculation parameters including:
                - service_id: Service ID
                - vehicle_type: Vehicle type
                - optional_addons: List of addon IDs (optional)
                - coupon_code: Discount coupon (optional)

        Returns:
            Price breakdown including:
                - base_price: Service base price
                - addon_price: Total addon cost
                - discount: Applied discount amount
                - tax: Tax amount
                - total_price: Final amount to pay

        Example:
            >>> price = await client.booking_create.calculate_price({
            ...     "service_id": "SRV-2025-001",
            ...     "vehicle_type": "Sedan",
            ...     "optional_addons": ["ADDON-001"],
            ...     "coupon_code": "FIRST20"
            ... })
            >>> print(f"Total: ₹{price['total_price']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.calculate_booking_price",
                price_data
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error calculating booking price: {e}")
            raise

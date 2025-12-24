"""Vendor portal client for Frappe API.

Handles vendor-specific operations including booking management and profile updates.
"""

from typing import Dict, Any, Optional
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class VendorPortalClient:
    """Handle vendor portal operations for service providers."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize vendor portal client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_bookings(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get vendor's assigned bookings with optional filters.

        Args:
            filters: Optional filter criteria including:
                - status: Booking status filter
                - from_date: Start date for date range
                - to_date: End date for date range
                - service_type: Filter by service type
                - limit: Number of results

        Returns:
            List of assigned bookings with:
                - booking_id: Booking identifier
                - customer_name: Customer details
                - service_name: Service information
                - vehicle_info: Vehicle details
                - slot_info: Scheduled time
                - address: Service location
                - status: Current status

        Example:
            >>> # Get all assigned bookings
            >>> bookings = await client.vendor_portal.get_bookings()
            >>>
            >>> # Get today's confirmed bookings
            >>> bookings = await client.vendor_portal.get_bookings({
            ...     "status": "Confirmed",
            ...     "from_date": "2025-01-15",
            ...     "to_date": "2025-01-15"
            ... })
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.vendor_portal.get_vendor_bookings",
                filters or {}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching vendor bookings: {e}")
            raise

    async def get_upcoming_bookings(self) -> Dict[str, Any]:
        """Get vendor's upcoming scheduled bookings.

        Returns:
            List of upcoming bookings sorted by scheduled time with:
                - booking_id: Booking identifier
                - customer_name: Customer name
                - service_name: Service type
                - scheduled_date: Service date
                - scheduled_time: Service time slot
                - vehicle_info: Vehicle details
                - address: Service location with directions

        Example:
            >>> upcoming = await client.vendor_portal.get_upcoming_bookings()
            >>> for booking in upcoming:
            ...     print(f"{booking['scheduled_date']} {booking['scheduled_time']}: {booking['customer_name']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.vendor_portal.get_upcoming_bookings"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching upcoming bookings: {e}")
            raise

    async def get_completed_bookings(self) -> Dict[str, Any]:
        """Get vendor's completed bookings history.

        Returns:
            List of completed bookings with:
                - booking_id: Booking identifier
                - customer_name: Customer name
                - service_name: Service provided
                - completion_date: Service completion date
                - rating: Customer rating (if provided)
                - feedback: Customer feedback (if provided)
                - payment_status: Payment information

        Example:
            >>> completed = await client.vendor_portal.get_completed_bookings()
            >>> for booking in completed:
            ...     rating = booking.get('rating', 'Not rated')
            ...     print(f"{booking['service_name']}: {rating}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.vendor_portal.get_completed_bookings"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching completed bookings: {e}")
            raise

    async def complete_booking(self, booking_id: str) -> Dict[str, Any]:
        """Mark booking as completed after service delivery.

        Args:
            booking_id: Booking ID to mark as complete

        Returns:
            Completion confirmation with:
                - booking_id: Booking identifier
                - completion_time: Actual completion timestamp
                - status: Updated status
                - next_steps: Instructions for vendor (e.g., payment settlement)

        Example:
            >>> result = await client.vendor_portal.complete_booking("BKG-2025-001")
            >>> print(f"Booking {result['booking_id']} completed at {result['completion_time']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.vendor_portal.complete_booking",
                {"booking_id": booking_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error completing booking {booking_id}: {e}")
            raise

    async def get_profile(self) -> Dict[str, Any]:
        """Get vendor profile information.

        Returns:
            Vendor profile details including:
                - vendor_id: Vendor identifier
                - vendor_name: Business name
                - contact_person: Contact details
                - phone: Phone number
                - email: Email address
                - address: Business address
                - service_areas: Areas covered
                - services_offered: List of services
                - rating: Average rating
                - total_bookings: Completed bookings count

        Example:
            >>> profile = await client.vendor_portal.get_profile()
            >>> print(f"Vendor: {profile['vendor_name']}")
            >>> print(f"Rating: {profile['rating']}/5.0")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.vendor_profile_api.get_vendor_profile"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching vendor profile: {e}")
            raise

    async def update_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update vendor profile information.

        Args:
            profile_data: Profile fields to update including:
                - vendor_name: Business name
                - contact_person: Contact person name
                - phone: Phone number
                - email: Email address
                - address: Business address
                - service_areas: Comma-separated areas
                - Additional editable fields

        Returns:
            Update confirmation with updated profile

        Example:
            >>> result = await client.vendor_portal.update_profile({
            ...     "phone": "9876543210",
            ...     "service_areas": "Bangalore North, Bangalore East"
            ... })
            >>> print("Profile updated successfully")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.vendor_profile_api.update_vendor_profile",
                profile_data
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error updating vendor profile: {e}")
            raise

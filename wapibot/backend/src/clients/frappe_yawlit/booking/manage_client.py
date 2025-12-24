"""Booking management client for Frappe API.

Handles booking retrieval, rescheduling, and cancellation operations.
"""

from typing import Dict, Any, Optional
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class BookingManageClient:
    """Handle booking management and lifecycle operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize booking manage client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_bookings(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get customer bookings with optional filters.

        Args:
            filters: Optional filter criteria including:
                - status: Booking status (e.g., Pending, Confirmed, Completed)
                - from_date: Start date for date range
                - to_date: End date for date range
                - service_id: Filter by specific service
                - limit: Number of results (optional)

        Returns:
            List of bookings matching filter criteria

        Example:
            >>> # Get all bookings
            >>> bookings = await client.booking_manage.get_bookings()
            >>>
            >>> # Get confirmed bookings only
            >>> bookings = await client.booking_manage.get_bookings(
            ...     {"status": "Confirmed"}
            ... )
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.get_customer_bookings",
                filters or {}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching bookings: {e}")
            raise

    async def get_booking_details(self, booking_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific booking.

        Args:
            booking_id: Booking document ID

        Returns:
            Complete booking details including:
                - booking_id: Booking identifier
                - service_name: Service details
                - vehicle_info: Vehicle information
                - slot_info: Time slot details
                - status: Current status
                - payment_status: Payment information
                - vendor_info: Assigned vendor (if any)

        Example:
            >>> details = await client.booking_manage.get_booking_details("BKG-2025-001")
            >>> print(details["service_name"])
            >>> print(details["status"])
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.get_booking_details",
                {"booking_id": booking_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching booking details for {booking_id}: {e}")
            raise

    async def reschedule_booking(self, booking_id: str, new_slot: Dict[str, Any]) -> Dict[str, Any]:
        """Reschedule existing booking to a new slot.

        Args:
            booking_id: Booking ID to reschedule
            new_slot: New slot information including:
                - slot_id: New time slot ID
                - date: New booking date
                - Additional slot parameters

        Returns:
            Reschedule confirmation with updated booking details

        Example:
            >>> result = await client.booking_manage.reschedule_booking(
            ...     "BKG-2025-001",
            ...     {
            ...         "slot_id": "SLOT-2025-100",
            ...         "date": "2025-01-20"
            ...     }
            ... )
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking_management.reschedule_booking",
                {
                    "booking_id": booking_id,
                    **new_slot
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error rescheduling booking {booking_id}: {e}")
            raise

    async def cancel_booking(self, booking_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Request cancellation of a booking.

        Args:
            booking_id: Booking ID to cancel
            reason: Cancellation reason (optional)

        Returns:
            Cancellation confirmation including refund details if applicable

        Example:
            >>> result = await client.booking_manage.cancel_booking(
            ...     "BKG-2025-001",
            ...     "Schedule conflict"
            ... )
            >>> print(result["refund_amount"])
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.cancellation.request_cancellation",
                {
                    "booking_id": booking_id,
                    "reason": reason
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error canceling booking {booking_id}: {e}")
            raise

    async def check_cancellation_eligibility(self, booking_id: str) -> Dict[str, Any]:
        """Check if booking can be cancelled and refund amount.

        Args:
            booking_id: Booking ID to check

        Returns:
            Eligibility information including:
                - can_cancel: Boolean indicating if cancellation allowed
                - refund_percentage: Percentage of refund
                - refund_amount: Actual refund amount
                - cancellation_fee: Fee charged for cancellation
                - deadline: Last date/time for cancellation

        Example:
            >>> eligibility = await client.booking_manage.check_cancellation_eligibility(
            ...     "BKG-2025-001"
            ... )
            >>> if eligibility["can_cancel"]:
            ...     print(f"Refund: ₹{eligibility['refund_amount']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.cancellation.check_cancellation_eligibility",
                {"booking_id": booking_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error checking cancellation eligibility for {booking_id}: {e}")
            raise

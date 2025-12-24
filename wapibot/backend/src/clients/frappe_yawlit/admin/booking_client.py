"""Admin booking client for Frappe API.

Handles admin-level booking management operations including vendor assignment.
"""

from typing import Dict, Any, Optional, List
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class AdminBookingClient:
    """Handle admin booking management and vendor assignment operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize admin booking client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_all_bookings(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get all bookings across all customers with filters.

        Args:
            filters: Optional filter criteria including:
                - status: Booking status filter
                - from_date: Start date for date range
                - to_date: End date for date range
                - service_id: Filter by service
                - vendor_id: Filter by assigned vendor
                - customer_id: Filter by customer
                - payment_status: Payment status filter
                - limit: Number of results

        Returns:
            List of all bookings with complete details:
                - booking_id: Booking identifier
                - customer_name: Customer name
                - service_name: Service information
                - vehicle_info: Vehicle details
                - slot_info: Scheduled time
                - vendor: Assigned vendor (if any)
                - status: Current status
                - payment_status: Payment information
                - created_at: Booking creation time

        Example:
            >>> # Get all bookings
            >>> bookings = await client.admin_booking.get_all_bookings()
            >>>
            >>> # Get pending bookings for today
            >>> bookings = await client.admin_booking.get_all_bookings({
            ...     "status": "Pending",
            ...     "from_date": "2025-01-15",
            ...     "to_date": "2025-01-15"
            ... })
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_booking_api.get_all_bookings",
                filters or {}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching all bookings: {e}")
            raise

    async def get_booking_details(self, booking_id: str) -> Dict[str, Any]:
        """Get comprehensive details for a specific booking.

        Args:
            booking_id: Booking ID to get details for

        Returns:
            Complete booking information including:
                - booking_id: Booking identifier
                - customer_info: Full customer details
                - service_details: Service information
                - vehicle_details: Vehicle information
                - slot_details: Time slot details
                - address_details: Service location
                - vendor_info: Assigned vendor (if any)
                - payment_info: Payment details
                - status_history: Status change log
                - notes: Internal notes

        Example:
            >>> details = await client.admin_booking.get_booking_details("BKG-2025-001")
            >>> print(f"Customer: {details['customer_info']['name']}")
            >>> print(f"Service: {details['service_details']['name']}")
            >>> if details.get('vendor_info'):
            ...     print(f"Vendor: {details['vendor_info']['name']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_booking_api.get_booking_details",
                {"booking_id": booking_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching booking details for {booking_id}: {e}")
            raise

    async def assign_vendor(self, booking_id: str, vendor_id: str) -> Dict[str, Any]:
        """Assign vendor to a booking.

        Args:
            booking_id: Booking ID to assign vendor to
            vendor_id: Vendor ID to assign

        Returns:
            Assignment confirmation with:
                - booking_id: Booking identifier
                - vendor_id: Assigned vendor ID
                - vendor_name: Vendor name
                - assignment_time: When vendor was assigned
                - notification_sent: Vendor notification status
                - status: Updated booking status

        Example:
            >>> result = await client.admin_booking.assign_vendor(
            ...     "BKG-2025-001",
            ...     "VND-2025-001"
            ... )
            >>> print(f"Vendor {result['vendor_name']} assigned to booking {result['booking_id']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_booking_api.assign_vendor_to_booking",
                {
                    "booking_id": booking_id,
                    "vendor_id": vendor_id
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error assigning vendor {vendor_id} to booking {booking_id}: {e}")
            raise

    async def update_status(self, booking_id: str, status: str) -> Dict[str, Any]:
        """Update booking status.

        Args:
            booking_id: Booking ID to update
            status: New status (e.g., "Confirmed", "In Progress", "Completed", "Cancelled")

        Returns:
            Status update confirmation with:
                - booking_id: Booking identifier
                - old_status: Previous status
                - new_status: Updated status
                - updated_at: Update timestamp
                - updated_by: Admin user who updated
                - notifications_sent: Customer/vendor notification status

        Example:
            >>> result = await client.admin_booking.update_status(
            ...     "BKG-2025-001",
            ...     "Confirmed"
            ... )
            >>> print(f"Booking status changed to {result['new_status']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_booking_api.update_booking_status",
                {
                    "booking_id": booking_id,
                    "status": status
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error updating status for booking {booking_id}: {e}")
            raise

    async def bulk_assign_vendors(self, assignments: List[Dict[str, str]]) -> Dict[str, Any]:
        """Assign multiple vendors to multiple bookings in bulk.

        Args:
            assignments: List of assignment dictionaries, each containing:
                - booking_id: Booking ID to assign
                - vendor_id: Vendor ID to assign

        Returns:
            Bulk assignment results with:
                - total: Total assignments attempted
                - successful: Number of successful assignments
                - failed: Number of failed assignments
                - results: List of individual assignment results
                - errors: List of errors (if any)

        Example:
            >>> assignments = [
            ...     {"booking_id": "BKG-2025-001", "vendor_id": "VND-2025-001"},
            ...     {"booking_id": "BKG-2025-002", "vendor_id": "VND-2025-002"},
            ...     {"booking_id": "BKG-2025-003", "vendor_id": "VND-2025-001"}
            ... ]
            >>> result = await client.admin_booking.bulk_assign_vendors(assignments)
            >>> print(f"Successfully assigned: {result['successful']}/{result['total']}")
            >>> if result['failed'] > 0:
            ...     for error in result['errors']:
            ...         print(f"Error: {error}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_booking_api.assign_vendor_bulk",
                {"assignments": assignments}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error performing bulk vendor assignment: {e}")
            raise

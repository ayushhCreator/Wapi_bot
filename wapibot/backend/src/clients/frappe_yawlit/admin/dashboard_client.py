"""Admin dashboard client for Frappe API.

Handles admin dashboard statistics, counts, and overview data.
"""

from typing import Dict, Any, Optional
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class AdminDashboardClient:
    """Handle admin dashboard data and statistics operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize admin dashboard client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics.

        Returns:
            Dashboard statistics including:
                - total_bookings: Total bookings count
                - pending_bookings: Pending bookings count
                - confirmed_bookings: Confirmed bookings count
                - completed_bookings: Completed bookings count
                - total_customers: Total customers count
                - active_subscriptions: Active subscriptions count
                - total_revenue: Total revenue amount
                - today_revenue: Today's revenue
                - Additional metrics

        Example:
            >>> stats = await client.admin_dashboard.get_stats()
            >>> print(f"Total bookings: {stats['total_bookings']}")
            >>> print(f"Revenue today: ₹{stats['today_revenue']}")
            >>> print(f"Active subscriptions: {stats['active_subscriptions']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_dashboard.get_dashboard_stats"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching dashboard stats: {e}")
            raise

    async def get_badge_counts(self) -> Dict[str, Any]:
        """Get badge notification counts for admin alerts.

        Returns:
            Badge counts for various sections:
                - pending_inquiries: New customer inquiries
                - unassigned_bookings: Bookings awaiting vendor assignment
                - pending_quotes: Subscription quotes pending approval
                - cancellation_requests: Pending cancellation requests
                - pending_payments: Payments awaiting confirmation
                - support_tickets: Open support tickets

        Example:
            >>> badges = await client.admin_dashboard.get_badge_counts()
            >>> if badges['pending_inquiries'] > 0:
            ...     print(f"New inquiries: {badges['pending_inquiries']}")
            >>> if badges['unassigned_bookings'] > 0:
            ...     print(f"Bookings need assignment: {badges['unassigned_bookings']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_dashboard.get_badge_counts"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching badge counts: {e}")
            raise

    async def get_pending_inquiries(self) -> Dict[str, Any]:
        """Get list of pending customer inquiries.

        Returns:
            List of pending inquiries with:
                - inquiry_id: Inquiry identifier
                - customer_name: Customer name
                - contact: Contact information
                - inquiry_type: Type of inquiry
                - message: Inquiry message
                - created_at: Submission timestamp
                - priority: Inquiry priority

        Example:
            >>> inquiries = await client.admin_dashboard.get_pending_inquiries()
            >>> for inquiry in inquiries:
            ...     print(f"[{inquiry['priority']}] {inquiry['customer_name']}: {inquiry['inquiry_type']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_dashboard.get_pending_inquiries"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching pending inquiries: {e}")
            raise

    async def get_recent_bookings(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get recent bookings for quick overview.

        Args:
            limit: Maximum number of bookings to return (optional)

        Returns:
            List of recent bookings with:
                - booking_id: Booking identifier
                - customer_name: Customer name
                - service_name: Service booked
                - booking_date: Scheduled date
                - status: Current status
                - vendor: Assigned vendor (if any)
                - payment_status: Payment information
                - created_at: Booking creation time

        Example:
            >>> # Get 10 most recent bookings
            >>> recent = await client.admin_dashboard.get_recent_bookings(limit=10)
            >>> for booking in recent:
            ...     print(f"{booking['booking_id']}: {booking['customer_name']} - {booking['status']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_dashboard.get_recent_bookings",
                {"limit": limit},
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching recent bookings: {e}")
            raise

    async def get_unassigned_bookings(self) -> Dict[str, Any]:
        """Get bookings that need vendor assignment.

        Returns:
            List of unassigned bookings with:
                - booking_id: Booking identifier
                - customer_name: Customer name
                - service_name: Service type
                - booking_date: Scheduled date
                - booking_time: Scheduled time
                - location: Service location
                - vehicle_type: Vehicle information
                - priority: Urgency level

        Example:
            >>> unassigned = await client.admin_dashboard.get_unassigned_bookings()
            >>> for booking in unassigned:
            ...     print(f"Urgent: {booking['booking_id']} - {booking['service_name']} on {booking['booking_date']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_dashboard.get_unassigned_bookings"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching unassigned bookings: {e}")
            raise

    async def get_pending_quotes(self) -> Dict[str, Any]:
        """Get pending subscription quotations.

        Returns:
            List of pending subscription quotes with:
                - quote_id: Quotation identifier
                - customer_name: Customer name
                - plan_name: Subscription plan
                - amount: Quotation amount
                - created_at: Quote creation time
                - valid_until: Quote expiry date
                - status: Quote status

        Example:
            >>> quotes = await client.admin_dashboard.get_pending_quotes()
            >>> for quote in quotes:
            ...     print(f"{quote['quote_id']}: {quote['customer_name']} - {quote['plan_name']} (₹{quote['amount']})")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_dashboard.get_subscription_quotations"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching pending quotes: {e}")
            raise

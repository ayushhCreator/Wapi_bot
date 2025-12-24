"""Admin management client modules."""

from clients.frappe_yawlit.admin.dashboard_client import AdminDashboardClient
from clients.frappe_yawlit.admin.booking_client import AdminBookingClient

__all__ = ["AdminDashboardClient", "AdminBookingClient"]

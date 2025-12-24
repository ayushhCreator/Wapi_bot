"""Service catalog client for Frappe API.

Handles service browsing, filtering, and vehicle type management.
"""

from typing import Dict, Any, Optional
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class ServiceCatalogClient:
    """Handle service catalog and discovery operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize service catalog client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_categories(self) -> Dict[str, Any]:
        """Get all active service categories.

        Returns:
            List of service categories with:
                - name: Category ID
                - category_name: Display name
                - category_slug: URL-friendly slug
                - icon: Category icon identifier
                - description: Category description

        Example:
            >>> categories = await client.service_catalog.get_categories()
            >>> for cat in categories:
            ...     print(cat["category_name"], cat["description"])
        """
        try:
            return await self.http.post(
                "/api/method/frappe.client.get_list",
                {
                    "doctype": "ServiceCategory",
                    "fields": ["name", "category_name", "category_slug", "icon", "description"],
                    "filters": {"active": 1},
                    "order_by": "display_order asc"
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching service categories: {e}")
            raise

    async def get_filtered_services(
        self,
        category: Optional[str] = None,
        frequency_type: Optional[str] = None,
        vehicle_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get services filtered by category, frequency, and vehicle type.

        Args:
            category: Service category filter (optional)
            frequency_type: Service frequency filter (e.g., "One-Time", "Recurring") (optional)
            vehicle_type: Vehicle type filter (e.g., "Sedan", "SUV") (optional)

        Returns:
            List of services matching filter criteria with:
                - service_id: Service identifier
                - service_name: Service display name
                - description: Service description
                - base_price: Starting price
                - duration: Estimated duration
                - category: Category information
                - vehicle_types: Supported vehicle types

        Example:
            >>> # Get all car wash services
            >>> services = await client.service_catalog.get_filtered_services(
            ...     category="Car Wash"
            ... )
            >>>
            >>> # Get one-time services for sedans
            >>> services = await client.service_catalog.get_filtered_services(
            ...     frequency_type="One-Time",
            ...     vehicle_type="Sedan"
            ... )
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.get_filtered_services",
                {
                    "category": category,
                    "frequency_type": frequency_type,
                    "vehicle_type": vehicle_type
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching filtered services: {e}")
            raise

    async def get_optional_addons(self, service_id: str) -> Dict[str, Any]:
        """Get optional add-ons available for a service.

        Args:
            service_id: Service ID to get addons for

        Returns:
            List of optional addons with:
                - addon_id: Addon identifier
                - addon_name: Display name
                - description: Addon description
                - price: Additional cost
                - duration: Additional time required

        Example:
            >>> addons = await client.service_catalog.get_optional_addons("SRV-2025-001")
            >>> for addon in addons:
            ...     print(f"{addon['addon_name']}: ₹{addon['price']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.booking.get_optional_addons",
                {"service_id": service_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching optional addons for {service_id}: {e}")
            raise

    async def get_vehicle_types(self) -> Dict[str, Any]:
        """Get list of active vehicle types.

        Returns:
            List of vehicle types with:
                - vehicle_type: Type identifier
                - display_name: Display name
                - description: Type description
                - icon: Vehicle icon (optional)

        Example:
            >>> vehicle_types = await client.service_catalog.get_vehicle_types()
            >>> for vtype in vehicle_types:
            ...     print(vtype["display_name"])
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.customer_management.doctype.vehicle_type.vehicle_type.get_active_vehicle_types_list"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching vehicle types: {e}")
            raise

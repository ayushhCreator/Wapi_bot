"""Customer address client for Frappe API.

Handles customer address operations including CRUD operations and geocoding.
"""

from typing import Dict, Any
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class CustomerAddressClient:
    """Handle customer address management operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize customer address client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_addresses(self) -> Dict[str, Any]:
        """Get all customer addresses.

        Returns:
            List of customer addresses with full details

        Example:
            >>> addresses = await client.customer_address.get_addresses()
            >>> for addr in addresses.get("addresses", []):
            ...     print(addr["address_line1"], addr["city"])
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.get_customer_addresses"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching addresses: {e}")
            raise

    async def add_address(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add new address to customer profile.

        Args:
            address_data: Address information including:
                - address_line1: Primary address line
                - address_line2: Secondary address line (optional)
                - city: City name
                - state: State name
                - pincode: PIN code
                - country: Country (default: India)
                - is_primary: Set as primary address (optional)
                - geo_latitude: Latitude (optional)
                - geo_longitude: Longitude (optional)

        Returns:
            Added address details with generated ID

        Example:
            >>> result = await client.customer_address.add_address({
            ...     "address_line1": "123 Main Street",
            ...     "address_line2": "Apt 4B",
            ...     "city": "Bangalore",
            ...     "state": "Karnataka",
            ...     "pincode": "560001",
            ...     "is_primary": True
            ... })
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.add_address",
                {"address_data": address_data},
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error adding address: {e}")
            raise

    async def update_address(
        self, address_name: str, address_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing address.

        Args:
            address_name: Address document name/ID
            address_data: Address fields to update

        Returns:
            Update confirmation with updated address

        Example:
            >>> result = await client.customer_address.update_address(
            ...     "ADDR-2025-001",
            ...     {"address_line1": "456 New Street", "pincode": "560002"}
            ... )
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.update_address",
                {"address_name": address_name, "address_data": address_data},
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error updating address {address_name}: {e}")
            raise

    async def delete_address(self, address_name: str) -> Dict[str, Any]:
        """Delete address from customer profile.

        Args:
            address_name: Address document name/ID to delete

        Returns:
            Deletion confirmation

        Example:
            >>> result = await client.customer_address.delete_address("ADDR-2025-001")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.delete_address",
                {"address_name": address_name},
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error deleting address {address_name}: {e}")
            raise

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """Get address from GPS coordinates using reverse geocoding.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Address details extracted from coordinates including:
                - address_line1: Formatted address
                - city: City name
                - state: State name
                - pincode: PIN code
                - country: Country name

        Example:
            >>> address = await client.customer_address.reverse_geocode(
            ...     12.9716,
            ...     77.5946
            ... )
            >>> print(address["city"])  # Bangalore
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.reverse_geocode",
                {"latitude": latitude, "longitude": longitude},
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error reverse geocoding ({latitude}, {longitude}): {e}")
            raise

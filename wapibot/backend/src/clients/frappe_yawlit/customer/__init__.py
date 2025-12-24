"""Customer management client modules."""

from clients.frappe_yawlit.customer.profile_client import CustomerProfileClient
from clients.frappe_yawlit.customer.address_client import CustomerAddressClient
from clients.frappe_yawlit.customer.lookup_client import CustomerLookupClient

# Aliases for backward compatibility
ProfileClient = CustomerProfileClient
AddressClient = CustomerAddressClient

__all__ = ["ProfileClient", "AddressClient", "CustomerLookupClient"]

"""Authentication client for Frappe API.

Handles user authentication, registration, and profile management.
"""

from typing import Dict, Any

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient


class AuthClient:
    """Handle authentication operations for customers and vendors."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize auth client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def login_email(self, email: str, password: str) -> Dict[str, Any]:
        """Login with email and password.

        Args:
            email: Customer email address
            password: Account password

        Returns:
            Login response with session token

        Example:
            >>> result = await client.auth.login_email("john@example.com", "password123")
            >>> print(result["message"])  # Login successful
        """
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.auth.unified_login.login_with_email_or_phone",
            {
                "username": email,
                "password": password
            }
        )

    async def login_phone(self, phone: str, password: str) -> Dict[str, Any]:
        """Login with phone number and password.

        Args:
            phone: Customer phone number (10 digits)
            password: Account password

        Returns:
            Login response with session token

        Example:
            >>> result = await client.auth.login_phone("9876543210", "password123")
        """
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.auth.phone_password.login_with_phone",
            {
                "phone_number": phone,
                "password": password
            }
        )

    async def register_unified(self, name: str, email_or_phone: str, password: str) -> Dict[str, Any]:
        """Register new customer with email or phone.

        Args:
            name: Customer full name
            email_or_phone: Email address or phone number
            password: Account password

        Returns:
            Registration response

        Example:
            >>> result = await client.auth.register_unified(
            ...     "John Doe",
            ...     "john@example.com",
            ...     "SecurePass123"
            ... )
        """
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.auth.unified_register.register_with_email_or_phone",
            {
                "customer_name": name,
                "email_or_phone": email_or_phone,
                "password": password
            }
        )

    async def complete_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete customer profile after registration.

        Args:
            profile_data: Profile information including:
                - customer_name: Full name
                - email: Email address
                - phone_number: Phone number
                - default_address: Address
                - city: City
                - state: State
                - pincode: PIN code
                - geo_latitude: Latitude (optional)
                - geo_longitude: Longitude (optional)
                - vehicles: List of vehicle dicts (optional)

        Returns:
            Profile completion response

        Example:
            >>> result = await client.auth.complete_profile({
            ...     "customer_name": "John Doe",
            ...     "email": "john@example.com",
            ...     "phone_number": "9876543210",
            ...     "default_address": "123 Main St",
            ...     "city": "Bangalore",
            ...     "state": "Karnataka",
            ...     "pincode": "560001",
            ...     "vehicles": [{
            ...         "vehicle_make": "Honda",
            ...         "vehicle_model": "City",
            ...         "vehicle_number": "KA01AB1234",
            ...         "vehicle_type": "Sedan"
            ...     }]
            ... })
        """
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.customer_portal.complete_profile",
            {"data": profile_data}
        )

    async def get_user_prefill_data(self) -> Dict[str, Any]:
        """Get user data for profile form prefill.

        Returns:
            User prefill data from system

        Example:
            >>> data = await client.auth.get_user_prefill_data()
            >>> print(data.get("email"))  # Pre-filled email
        """
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.customer_portal.get_user_prefill_data"
        )

    async def send_otp(self, phone: str) -> Dict[str, Any]:
        """Send OTP to phone number for verification.

        Args:
            phone: Phone number (10 digits)

        Returns:
            OTP send confirmation

        Example:
            >>> result = await client.auth.send_otp("9876543210")
            >>> print(result["message"])  # OTP sent successfully
        """
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.auth.phone_otp.send_otp",
            {"phone_number": phone}
        )

    async def verify_otp(self, phone: str, otp: str) -> Dict[str, Any]:
        """Verify OTP and login/register user.

        Args:
            phone: Phone number (10 digits)
            otp: OTP code received via SMS

        Returns:
            Login response with session token

        Example:
            >>> result = await client.auth.verify_otp("9876543210", "123456")
        """
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.auth.phone_otp.verify_otp_and_login",
            {
                "phone_number": phone,
                "otp": otp
            }
        )

    async def reset_password(self, email: str) -> Dict[str, Any]:
        """Send password reset link to email.

        Args:
            email: Customer email address

        Returns:
            Reset email confirmation

        Example:
            >>> result = await client.auth.reset_password("john@example.com")
            >>> print(result["message"])  # Reset link sent
        """
        return await self.http.post(
            "/api/method/yawlit_automotive_services.api.auth.password_reset.send_reset_email",
            {"email": email}
        )

    async def logout(self) -> Dict[str, Any]:
        """Logout current user and clear session.

        Returns:
            Logout confirmation

        Example:
            >>> result = await client.auth.logout()
        """
        result = await self.http.post("/api/method/logout")
        self.http.config.clear_session()
        return result

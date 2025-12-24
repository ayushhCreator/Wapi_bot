"""Payment client for Frappe API.

Handles payment order creation and verification for bookings and subscriptions.
"""

from typing import Dict, Any
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class PaymentClient:
    """Handle payment operations for bookings and subscriptions."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize payment client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def create_order(self, booking_id: str, amount: float) -> Dict[str, Any]:
        """Create payment order for one-time booking.

        Args:
            booking_id: Booking ID to create payment for
            amount: Payment amount in rupees

        Returns:
            Payment order details including:
                - order_id: Payment gateway order ID
                - amount: Order amount
                - currency: Currency code
                - payment_link: Payment URL (if applicable)
                - gateway: Payment gateway identifier

        Example:
            >>> order = await client.payment.create_order("BKG-2025-001", 1500.00)
            >>> print(f"Order ID: {order['order_id']}")
            >>> print(f"Pay here: {order['payment_link']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.payment_gateway_integration.create_payment_order",
                {
                    "booking_id": booking_id,
                    "amount": amount
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error creating payment order for booking {booking_id}: {e}")
            raise

    async def verify_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify payment completion for booking.

        Args:
            payment_data: Payment verification data including:
                - order_id: Payment gateway order ID
                - payment_id: Payment transaction ID
                - signature: Payment signature for verification
                - Additional gateway-specific fields

        Returns:
            Verification result including:
                - verified: Boolean indicating success
                - booking_id: Associated booking ID
                - payment_status: Payment status
                - transaction_id: Internal transaction ID

        Example:
            >>> result = await client.payment.verify_payment({
            ...     "order_id": "order_xyz123",
            ...     "payment_id": "pay_abc456",
            ...     "signature": "signature_hash"
            ... })
            >>> if result["verified"]:
            ...     print(f"Payment successful for booking: {result['booking_id']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.payment_gateway_integration.verify_payment",
                payment_data
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error verifying payment: {e}")
            raise

    async def create_subscription_order(self, quote_id: str) -> Dict[str, Any]:
        """Create payment order for subscription.

        Args:
            quote_id: Quotation ID for the subscription

        Returns:
            Subscription payment order details including:
                - order_id: Payment gateway order ID
                - amount: Subscription amount
                - currency: Currency code
                - payment_link: Payment URL
                - subscription_id: Associated subscription ID
                - validity: Subscription validity period

        Example:
            >>> order = await client.payment.create_subscription_order("QTN-2025-001")
            >>> print(f"Subscription payment: ₹{order['amount']}")
            >>> print(f"Payment link: {order['payment_link']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.payment_api.create_subscription_payment_order",
                {"quote_id": quote_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error creating subscription payment order for quote {quote_id}: {e}")
            raise

    async def verify_subscription_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify subscription payment completion.

        Args:
            payment_data: Payment verification data including:
                - order_id: Payment gateway order ID
                - payment_id: Payment transaction ID
                - signature: Payment signature
                - Additional verification fields

        Returns:
            Verification result including:
                - verified: Boolean indicating success
                - subscription_id: Activated subscription ID
                - payment_status: Payment status
                - activation_date: Subscription start date
                - transaction_id: Internal transaction ID

        Example:
            >>> result = await client.payment.verify_subscription_payment({
            ...     "order_id": "order_xyz123",
            ...     "payment_id": "pay_abc456",
            ...     "signature": "signature_hash"
            ... })
            >>> if result["verified"]:
            ...     print(f"Subscription activated: {result['subscription_id']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.payment_api.verify_subscription_payment",
                payment_data
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error verifying subscription payment: {e}")
            raise

    async def create_balance_payment(self, booking_id: str, amount: float) -> Dict[str, Any]:
        """Create balance payment for partial/remaining amount.

        Args:
            booking_id: Booking ID requiring balance payment
            amount: Balance amount to be paid

        Returns:
            Balance payment order details including:
                - order_id: Payment gateway order ID
                - amount: Balance amount
                - original_amount: Total booking amount
                - paid_amount: Already paid amount
                - payment_link: Payment URL

        Example:
            >>> # Customer paid 500, needs to pay remaining 1000
            >>> order = await client.payment.create_balance_payment("BKG-2025-001", 1000.00)
            >>> print(f"Balance due: ₹{order['amount']}")
            >>> print(f"Pay here: {order['payment_link']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.payment_api.create_balance_payment",
                {
                    "booking_id": booking_id,
                    "amount": amount
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error creating balance payment for booking {booking_id}: {e}")
            raise

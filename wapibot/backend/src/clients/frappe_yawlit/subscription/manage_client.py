"""Subscription management client for Frappe API.

Handles subscription lifecycle operations including creation, cancellation, and pausing.
"""

from typing import Dict, Any, Optional
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class SubscriptionManageClient:
    """Handle subscription lifecycle management operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize subscription manage client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_active_subscription(self) -> Dict[str, Any]:
        """Get customer's active subscription.

        Returns:
            Active subscription details including:
                - subscription_id: Subscription identifier
                - plan_name: Plan name
                - status: Current status
                - start_date: Subscription start date
                - end_date: Subscription end date
                - remaining_services: Services left
                - auto_renew: Auto-renewal status

        Example:
            >>> subscription = await client.subscription_manage.get_active_subscription()
            >>> if subscription.get("subscription_id"):
            ...     print(f"Active plan: {subscription['plan_name']}")
            ...     print(f"Valid until: {subscription['end_date']}")
            >>> else:
            ...     print("No active subscription")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.get_active_subscription"
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching active subscription: {e}")
            raise

    async def get_subscription_details(self, subscription_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific subscription.

        Args:
            subscription_id: Subscription ID to get details for

        Returns:
            Complete subscription details including:
                - subscription_id: Identifier
                - plan_details: Plan information
                - customer_info: Customer details
                - payment_info: Payment and billing
                - service_usage: Usage statistics
                - renewal_info: Renewal details
                - vehicles: Associated vehicles

        Example:
            >>> details = await client.subscription_manage.get_subscription_details(
            ...     "SUB-2025-001"
            ... )
            >>> print(details["plan_details"]["plan_name"])
            >>> print(f"Services used: {details['service_usage']['used_count']}/{details['service_usage']['total_count']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.subscription_api.get_subscription_details",
                {"subscription_id": subscription_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching subscription details for {subscription_id}: {e}")
            raise

    async def submit_request(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit new subscription request.

        Args:
            subscription_data: Subscription request data including:
                - plan_id: Selected plan ID
                - vehicle_ids: List of vehicle IDs
                - start_date: Desired start date
                - billing_address: Billing address ID
                - payment_method: Payment method
                - Additional optional fields

        Returns:
            Subscription request confirmation with:
                - quotation_id: Generated quotation ID
                - subscription_id: Pending subscription ID
                - payment_required: Payment amount
                - payment_link: Payment URL (if applicable)

        Example:
            >>> result = await client.subscription_manage.submit_request({
            ...     "plan_id": "PLAN-2025-001",
            ...     "vehicle_ids": ["VEH-2025-001", "VEH-2025-002"],
            ...     "start_date": "2025-02-01",
            ...     "billing_address": "ADDR-2025-001"
            ... })
            >>> print(f"Quotation ID: {result['quotation_id']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.customer_portal.submit_subscription_request",
                {"subscription_data": subscription_data}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error submitting subscription request: {e}")
            raise

    async def cancel_subscription(self, subscription_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Cancel active subscription.

        Args:
            subscription_id: Subscription ID to cancel
            reason: Cancellation reason (optional)

        Returns:
            Cancellation confirmation with:
                - cancellation_id: Cancellation request ID
                - effective_date: When cancellation takes effect
                - refund_amount: Refund amount (if applicable)
                - access_until: Last day of access

        Example:
            >>> result = await client.subscription_manage.cancel_subscription(
            ...     "SUB-2025-001",
            ...     "Moving to another city"
            ... )
            >>> print(f"Subscription will end on: {result['effective_date']}")
            >>> if result.get("refund_amount"):
            ...     print(f"Refund: ₹{result['refund_amount']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.subscription_api.cancel_my_subscription",
                {
                    "subscription_id": subscription_id,
                    "reason": reason
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error canceling subscription {subscription_id}: {e}")
            raise

    async def pause_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Pause active subscription temporarily.

        Args:
            subscription_id: Subscription ID to pause

        Returns:
            Pause confirmation with:
                - pause_id: Pause request ID
                - paused_from: Pause start date
                - can_resume_on: Earliest resume date
                - max_pause_duration: Maximum pause period

        Example:
            >>> result = await client.subscription_manage.pause_subscription("SUB-2025-001")
            >>> print(f"Subscription paused from: {result['paused_from']}")
            >>> print(f"Can resume on: {result['can_resume_on']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.admin_subscription_lifecycle.pause_subscription",
                {"subscription_id": subscription_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error pausing subscription {subscription_id}: {e}")
            raise

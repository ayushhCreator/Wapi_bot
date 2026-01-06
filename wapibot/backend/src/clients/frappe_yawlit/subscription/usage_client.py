"""Subscription usage client for Frappe API.

Handles subscription usage tracking, wash history, and analytics.
"""

from typing import Dict, Any
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class SubscriptionUsageClient:
    """Handle subscription usage tracking and analytics operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize subscription usage client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_usage(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription usage details.

        Args:
            subscription_id: Subscription ID to get usage for

        Returns:
            Usage information including:
                - total_services: Total services in plan
                - used_services: Services already consumed
                - remaining_services: Services left
                - service_breakdown: Usage by service type
                - last_service_date: Date of last service

        Example:
            >>> usage = await client.subscription_usage.get_usage("SUB-2025-001")
            >>> print(f"Used: {usage['used_services']}/{usage['total_services']}")
            >>> for service in usage['service_breakdown']:
            ...     print(f"{service['name']}: {service['used']}/{service['total']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.subscription_usage_api.get_subscription_usage",
                {"subscription_id": subscription_id},
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(
                f"Error fetching subscription usage for {subscription_id}: {e}"
            )
            raise

    async def get_wash_history(self, subscription_id: str) -> Dict[str, Any]:
        """Get wash service history for subscription.

        Args:
            subscription_id: Subscription ID to get history for

        Returns:
            List of completed wash services with:
                - wash_id: Service identifier
                - service_name: Service type
                - service_date: Date of service
                - vehicle: Vehicle serviced
                - vendor: Service provider
                - rating: Customer rating (if provided)
                - feedback: Customer feedback (if provided)

        Example:
            >>> history = await client.subscription_usage.get_wash_history("SUB-2025-001")
            >>> for wash in history:
            ...     print(f"{wash['service_date']}: {wash['service_name']} - {wash['vehicle']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.subscription_usage_api.get_wash_history",
                {"subscription_id": subscription_id},
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching wash history for {subscription_id}: {e}")
            raise

    async def get_remaining_washes(self, subscription_id: str) -> Dict[str, Any]:
        """Get remaining wash count for subscription.

        Args:
            subscription_id: Subscription ID to check

        Returns:
            Remaining wash information:
                - total_washes: Total washes in plan
                - used_washes: Washes already used
                - remaining_washes: Washes available
                - reset_date: When count resets (if applicable)
                - expires_on: Subscription expiry date

        Example:
            >>> washes = await client.subscription_usage.get_remaining_washes("SUB-2025-001")
            >>> print(f"Remaining washes: {washes['remaining_washes']}")
            >>> if washes.get('reset_date'):
            ...     print(f"Resets on: {washes['reset_date']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.subscription_usage_api.get_remaining_washes",
                {"subscription_id": subscription_id},
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching remaining washes for {subscription_id}: {e}")
            raise

    async def get_usage_summary(self, subscription_id: str) -> Dict[str, Any]:
        """Get comprehensive usage summary for subscription.

        Args:
            subscription_id: Subscription ID to get summary for

        Returns:
            Complete usage summary including:
                - subscription_info: Basic subscription details
                - usage_stats: Overall usage statistics
                - service_utilization: Usage by service type
                - upcoming_services: Scheduled services
                - recommendations: Usage optimization tips

        Example:
            >>> summary = await client.subscription_usage.get_usage_summary("SUB-2025-001")
            >>> print(f"Utilization: {summary['usage_stats']['utilization_percentage']}%")
            >>> for rec in summary.get('recommendations', []):
            ...     print(f"Tip: {rec}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.subscription_wash_cancellation.get_subscription_usage_summary",
                {"subscription_id": subscription_id},
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching usage summary for {subscription_id}: {e}")
            raise

    async def get_analytics(self, subscription_id: str) -> Dict[str, Any]:
        """Get detailed usage analytics for subscription.

        Args:
            subscription_id: Subscription ID to get analytics for

        Returns:
            Analytics data including:
                - trends: Usage trends over time
                - service_frequency: Service booking patterns
                - peak_times: Most popular booking times
                - vehicle_usage: Usage breakdown by vehicle
                - cost_savings: Estimated savings vs one-time bookings
                - recommendations: Personalized recommendations

        Example:
            >>> analytics = await client.subscription_usage.get_analytics("SUB-2025-001")
            >>> print(f"Total savings: ₹{analytics['cost_savings']['total_saved']}")
            >>> print(f"Most used service: {analytics['service_frequency'][0]['name']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.service_usage_analytics.get_subscription_usage_analytics",
                {"subscription_id": subscription_id},
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching usage analytics for {subscription_id}: {e}")
            raise

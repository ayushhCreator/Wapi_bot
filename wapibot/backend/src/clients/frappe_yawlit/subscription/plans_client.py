"""Subscription plans client for Frappe API.

Handles subscription plan browsing, details, and pricing calculations.
"""

from typing import Dict, Any, Optional
import logging

from clients.frappe_yawlit.utils.http_client import AsyncHTTPClient
from clients.frappe_yawlit.utils.exceptions import NotFoundError, FrappeAPIError

logger = logging.getLogger(__name__)


class SubscriptionPlansClient:
    """Handle subscription plan discovery and pricing operations."""

    def __init__(self, http_client: AsyncHTTPClient):
        """Initialize subscription plans client.

        Args:
            http_client: Async HTTP client instance
        """
        self.http = http_client

    async def get_plans(self, vehicle_type: Optional[str] = None) -> Dict[str, Any]:
        """Get available subscription plans.

        Args:
            vehicle_type: Filter plans by vehicle type (optional)

        Returns:
            List of subscription plans with:
                - plan_id: Plan identifier
                - plan_name: Plan display name
                - description: Plan description
                - duration: Subscription duration
                - price: Base price
                - features: Included features
                - service_count: Number of services included

        Example:
            >>> # Get all plans
            >>> plans = await client.subscription_plans.get_plans()
            >>> for plan in plans:
            ...     print(f"{plan['plan_name']}: ₹{plan['price']}")
            >>>
            >>> # Get plans for specific vehicle type
            >>> sedan_plans = await client.subscription_plans.get_plans("Sedan")
        """
        try:
            endpoint = "/api/method/yawlit_automotive_services.api.subscription_flow_api.get_subscription_plans"
            if vehicle_type:
                endpoint = "/api/method/yawlit_automotive_services.api.subscription_flow_api.get_plans_by_vehicle_type"
                return await self.http.post(endpoint, {"vehicle_type": vehicle_type})
            return await self.http.post(endpoint)
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching subscription plans: {e}")
            raise

    async def get_plan_details(self, plan_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific plan.

        Args:
            plan_id: Plan ID to get details for

        Returns:
            Complete plan details including:
                - plan_id: Plan identifier
                - plan_name: Plan name
                - description: Full description
                - price: Pricing information
                - duration: Plan duration
                - services: Detailed service breakdown
                - terms: Terms and conditions
                - benefits: List of benefits

        Example:
            >>> details = await client.subscription_plans.get_plan_details("PLAN-2025-001")
            >>> print(details["plan_name"])
            >>> for service in details["services"]:
            ...     print(service["service_name"], service["frequency"])
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.product_form.get_plan_details",
                {"plan_id": plan_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching plan details for {plan_id}: {e}")
            raise

    async def get_plan_services(self, plan_id: str) -> Dict[str, Any]:
        """Get services included in a subscription plan.

        Args:
            plan_id: Plan ID to get services for

        Returns:
            List of services included in plan:
                - service_id: Service identifier
                - service_name: Service name
                - frequency: How often service is available
                - quantity: Number of times included
                - description: Service description

        Example:
            >>> services = await client.subscription_plans.get_plan_services("PLAN-2025-001")
            >>> for service in services:
            ...     print(f"{service['service_name']}: {service['quantity']}x {service['frequency']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.subscription_flow_api.get_plan_services",
                {"plan_id": plan_id}
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error fetching plan services for {plan_id}: {e}")
            raise

    async def calculate_price(self, plan_id: str, vehicle_count: int, **kwargs) -> Dict[str, Any]:
        """Calculate subscription price based on plan and parameters.

        Args:
            plan_id: Plan ID to calculate price for
            vehicle_count: Number of vehicles to include
            **kwargs: Additional pricing parameters:
                - coupon_code: Discount coupon (optional)
                - addon_services: Additional services (optional)
                - billing_frequency: Annual/Monthly (optional)

        Returns:
            Price breakdown including:
                - base_price: Plan base price
                - vehicle_price: Additional vehicle charges
                - addon_price: Optional addon costs
                - discount: Applied discounts
                - tax: Tax amount
                - total_price: Final amount

        Example:
            >>> price = await client.subscription_plans.calculate_price(
            ...     "PLAN-2025-001",
            ...     2,
            ...     coupon_code="SAVE20"
            ... )
            >>> print(f"Total: ₹{price['total_price']}")
            >>> print(f"Discount: ₹{price['discount']}")
        """
        try:
            return await self.http.post(
                "/api/method/yawlit_automotive_services.api.subscription_pricing.calculate_subscription_price_v2",
                {
                    "plan_id": plan_id,
                    "vehicle_count": vehicle_count,
                    **kwargs
                }
            )
        except (NotFoundError, FrappeAPIError) as e:
            logger.error(f"Error calculating price for plan {plan_id}: {e}")
            raise

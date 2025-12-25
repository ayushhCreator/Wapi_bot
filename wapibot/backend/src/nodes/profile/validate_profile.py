"""Profile validation and routing logic."""

import logging
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)


async def route_after_profile_fetch(state: BookingState) -> str:
    """Route based on profile fetch results.

    Returns:
        - "customer_not_found": New user, redirect to registration
        - "profile_incomplete": Missing required fields
        - "no_vehicles": No vehicles registered
        - "vehicle_selection_required": Multiple vehicles, need choice
        - "profile_ready": Ready to proceed
    """
    customer = state.get("customer")
    if not customer:
        logger.info("🔀 Route: customer_not_found")
        return "customer_not_found"

    profile_complete = state.get("profile_complete", False)
    if not profile_complete:
        logger.info("🔀 Route: profile_incomplete")
        return "profile_incomplete"

    # Profile is complete, check vehicles
    vehicle_options = state.get("vehicle_options", [])
    vehicle_selected = state.get("vehicle_selected", False)

    if state.get("vehicle") is None and len(vehicle_options) == 0:
        logger.info("🔀 Route: no_vehicles")
        return "no_vehicles"

    if not vehicle_selected and len(vehicle_options) > 0:
        logger.info("🔀 Route: vehicle_selection_required")
        return "vehicle_selection_required"

    logger.info("🔀 Route: profile_ready")
    return "profile_ready"

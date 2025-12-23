"""Conditional routing functions for workflows.

Provides routing logic to determine next node based on current state.
Used by LangGraph's add_conditional_edges() method.
"""

from .state import BookingState


def route_after_name(state: BookingState) -> str:
    """Route after name extraction based on completeness."""
    if state.get("customer") and state["customer"].get("first_name"):
        # Name extracted, move to phone
        return "extract_phone"
    else:
        # Name missing, ask user
        return "generate_response"


def route_after_phone(state: BookingState) -> str:
    """Route after phone extraction."""
    if state.get("customer") and state["customer"].get("phone"):
        # Phone extracted, move to vehicle
        return "extract_vehicle"
    else:
        # Phone missing, ask user
        return "generate_response"


def route_after_vehicle(state: BookingState) -> str:
    """Route after vehicle extraction."""
    if state.get("vehicle") and state["vehicle"].get("brand"):
        # Vehicle extracted, move to date
        return "extract_date"
    else:
        # Vehicle missing, ask user
        return "generate_response"


def route_after_date(state: BookingState) -> str:
    """Route after date extraction."""
    if state.get("appointment") and state["appointment"].get("date"):
        # Date extracted, validate completeness
        return "validate_completeness"
    else:
        # Date missing, ask user
        return "generate_response"


def route_after_validation(state: BookingState) -> str:
    """Route after completeness validation."""
    if state.get("completeness", 0.0) >= 1.0:
        # All data collected, show confirmation
        return "confirm_booking"
    else:
        # Still missing data, ask user
        return "generate_response"


def route_after_confirmation(state: BookingState) -> str:
    """Route after confirmation decision."""
    if state.get("should_confirm"):
        # User confirmed, create service request
        return "create_service_request"
    else:
        # User wants to edit, generate response
        return "generate_response"


def route_after_sentiment(state: BookingState) -> str:
    """Route based on sentiment analysis."""
    sentiment = state.get("sentiment", {})

    # Check if should disengage (high anger/disgust)
    if sentiment.get("anger", 0) >= 8.0 or sentiment.get("disgust", 0) >= 8.0:
        return "generate_disengagement_response"

    # Check if should proceed normally
    if sentiment.get("interest", 0) >= 4.0:
        return "classify_intent"

    # Low interest, needs engagement
    return "generate_engagement_response"

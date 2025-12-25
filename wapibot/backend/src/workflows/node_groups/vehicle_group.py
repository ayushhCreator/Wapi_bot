"""Vehicle selection node group.

Handles:
- Displaying vehicle options (if multiple)
- Processing user selection
- Error handling for invalid selections

Replaces 6 old nodes:
- send_vehicle_options
- await_vehicle_selection
- process_vehicle_selection
- handle_vehicle_selection_error
- validate_vehicle_selection
- route_vehicle_selection
"""

from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.selection.generic_handler import handle_selection, route_after_selection
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.vehicle_options import VehicleOptionsBuilder


async def show_vehicle_options(state: BookingState) -> BookingState:
    """Display vehicle options to user."""
    return await send_message_node(state, VehicleOptionsBuilder())


async def process_vehicle_selection(state: BookingState) -> BookingState:
    """Process vehicle selection from user."""
    return await handle_selection(
        state,
        selection_type="vehicle",
        options_key="vehicle_options",
        selected_key="vehicle"
    )


async def send_vehicle_error(state: BookingState) -> BookingState:
    """Send error message for invalid vehicle selection."""
    error_msg = state.get("selection_error", "Invalid selection. Please try again.")
    result = await send_message_node(state, lambda s: error_msg)
    result["should_proceed"] = False  # Stop and wait for next user message
    return result


def check_if_vehicle_needed(state: BookingState) -> str:
    """Check if vehicle selection is needed.

    Returns:
        - "skip": Vehicle already selected, no action needed
        - "select": Need to show options and get user selection
    """
    # If vehicle already selected, skip this group
    if state.get("vehicle_selected", False):
        return "skip"

    # If no vehicle options, skip (shouldn't happen)
    vehicle_options = state.get("vehicle_options", [])
    if len(vehicle_options) == 0:
        return "skip"

    return "select"


async def skip_vehicle_selection(state: BookingState) -> BookingState:
    """Skip vehicle selection (already done)."""
    state["should_proceed"] = True
    return state


def create_vehicle_group() -> StateGraph:
    """Create vehicle selection node group.

    Inputs:
    - state["vehicle_options"]: List of vehicles

    Outputs:
    - state["vehicle"]: Selected vehicle
    - state["vehicle_selected"]: True when done
    """
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("skip_selection", skip_vehicle_selection)
    workflow.add_node("show_options", show_vehicle_options)
    workflow.add_node("process_selection", process_vehicle_selection)
    workflow.add_node("send_error", send_vehicle_error)

    # Entry point: check if selection is needed
    workflow.set_entry_point("skip_selection")

    # Conditional routing based on whether vehicle is already selected
    workflow.add_conditional_edges(
        "skip_selection",
        check_if_vehicle_needed,
        {
            "skip": END,  # Vehicle already selected, end immediately
            "select": "show_options"  # Need to show options
        }
    )

    # Show options, then process selection
    workflow.add_edge("show_options", "process_selection")

    # After processing selection
    workflow.add_conditional_edges(
        "process_selection",
        route_after_selection,
        {
            "selection_error": "send_error",  # Invalid selection
            "selection_success": END  # Valid selection, done
        }
    )

    # Error path: send error and END (don't loop!)
    workflow.add_edge("send_error", END)

    return workflow.compile()

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
    error_msg = state.get("error", "Invalid selection. Please try again.")
    return await send_message_node(state, lambda s: error_msg)


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
    workflow.add_node("show_options", show_vehicle_options)
    workflow.add_node("process_selection", process_vehicle_selection)
    workflow.add_node("send_error", send_vehicle_error)

    # Flow
    workflow.set_entry_point("show_options")
    workflow.add_edge("show_options", "process_selection")

    workflow.add_conditional_edges(
        "process_selection",
        route_after_selection,
        {
            "selection_error": "send_error",
            "selection_success": END
        }
    )

    workflow.add_edge("send_error", "show_options")  # Re-prompt

    return workflow.compile()

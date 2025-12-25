"""Slot selection node group.

Handles:
- Fetching available slots
- Displaying slots to user
- Processing slot selection
- Error handling

Replaces 6 old nodes:
- fetch_slots
- format_slots
- send_slots
- await_slot_selection
- process_slot_selection
- handle_slot_selection_error
"""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.selection.generic_handler import handle_selection, route_after_selection
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.transform import node as transform_node
from nodes.transformers.format_slot_options import FormatSlotOptions

logger = logging.getLogger(__name__)


async def fetch_slots(state: BookingState) -> BookingState:
    """Fetch available appointment slots.

    For MVP, using mock slots. In production, call Frappe slot API.
    """
    # Mock slots for MVP
    state["slot_options"] = [
        {"date": "2025-12-26", "time_slot": "10:00 AM - 12:00 PM", "slot_id": "SLOT-001"},
        {"date": "2025-12-26", "time_slot": "2:00 PM - 4:00 PM", "slot_id": "SLOT-002"},
        {"date": "2025-12-27", "time_slot": "10:00 AM - 12:00 PM", "slot_id": "SLOT-003"},
        {"date": "2025-12-27", "time_slot": "2:00 PM - 4:00 PM", "slot_id": "SLOT-004"}
    ]

    logger.info(f"📅 Fetched {len(state['slot_options'])} slot(s)")
    return state


async def format_and_send_slots(state: BookingState) -> BookingState:
    """Format and send slots to customer."""
    # Format slots
    formatted = await transform_node(
        state,
        FormatSlotOptions(),
        "slot_options",
        "formatted_slots_message"
    )

    # Send formatted message
    def slots_message(s):
        return s.get("formatted_slots_message", "No slots available")

    return await send_message_node(formatted, slots_message)


async def process_slot_selection(state: BookingState) -> BookingState:
    """Process slot selection from user."""
    return await handle_selection(
        state,
        selection_type="slot",
        options_key="slot_options",
        selected_key="slot"
    )


async def send_slot_error(state: BookingState) -> BookingState:
    """Send error message for invalid slot selection."""
    error_msg = state.get("selection_error", "Invalid selection. Please try again.")
    result = await send_message_node(state, lambda s: error_msg)
    result["should_proceed"] = False  # Stop and wait for next user message
    return result


def create_slot_group() -> StateGraph:
    """Create slot selection node group."""
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("fetch_slots", fetch_slots)
    workflow.add_node("show_slots", format_and_send_slots)
    workflow.add_node("process_selection", process_slot_selection)
    workflow.add_node("send_error", send_slot_error)

    # Flow
    workflow.set_entry_point("fetch_slots")
    workflow.add_edge("fetch_slots", "show_slots")
    workflow.add_edge("show_slots", "process_selection")

    workflow.add_conditional_edges(
        "process_selection",
        route_after_selection,
        {
            "selection_error": "send_error",
            "selection_success": END
        }
    )

    # Error path: send error and END (don't loop!)
    workflow.add_edge("send_error", END)

    return workflow.compile()

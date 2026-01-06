"""Slot selection - fetch, filter by preference, group by time, display, process selection."""

import logging
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.selection.generic_handler import handle_selection, route_after_selection
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.transform import node as transform_node
from nodes.transformers.filter_slots_by_preference import FilterSlotsByPreference
from nodes.transformers.group_slots_by_time import GroupSlotsByTime
from nodes.message_builders.grouped_slots import GroupedSlotsBuilder
from nodes.routing.resume_router import create_resume_router
from nodes.error_handling.selection_error_handler import handle_selection_error
from clients.frappe_yawlit import get_yawlit_client

logger = logging.getLogger(__name__)


async def fetch_slots(state: BookingState) -> BookingState:
    """Fetch available appointment slots from Frappe API for next 7 days."""
    client = get_yawlit_client()
    selected_service = state.get("selected_service")
    service_id = selected_service.get("name") if selected_service else None
    vehicle = state.get("vehicle", {})
    vehicle_type = vehicle.get("vehicle_type") if vehicle else None
    if not service_id:
        logger.warning("⚠️ No service selected, cannot fetch slots")
        state["slot_options"] = []
        return state
    all_slots = []
    today = datetime.now().date()
    preferred_date = state.get("preferred_date", "")
    if preferred_date:
        try:
            start_date = datetime.fromisoformat(preferred_date).date()
            logger.info(f"📅 Fetching slots for preferred date: {preferred_date}")
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Invalid preferred_date: {preferred_date}, using today")
            start_date = today
    else:
        start_date = today
    for i in range(7):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        try:
            response = await client.slot_availability.get_available_slots_enhanced(
                service_id=service_id, date=date_str, vehicle_type=vehicle_type
            )
            slots = response.get("message", {}).get("slots", [])
            if not slots:
                slots = response.get("slots", [])
            if not slots and isinstance(response.get("message"), list):
                slots = response["message"]
            available_slots = [
                slot for slot in slots if slot.get("available", True) is not False
            ]
            logger.info(f"📅 {len(available_slots)} available slot(s) for {date_str}")
            for slot in available_slots:
                slot["date"] = date_str
                slot["available"] = True
                if "time_slot" not in slot:
                    start = slot.get("start_time", "")
                    end = slot.get("end_time", "")
                    if start and end:
                        slot["time_slot"] = f"{start} - {end}"
            all_slots.extend(available_slots)
        except Exception as e:
            logger.error(f"❌ Failed to fetch slots for {date_str}: {e}")
            continue
    state["slot_options"] = all_slots
    logger.info(f"📅 Fetched {len(all_slots)} slot(s) total")
    return state


async def format_and_send_slots(state: BookingState) -> BookingState:
    """Filter, group, and send slots to customer, then pause for user input."""
    filtered = await transform_node(
        state, FilterSlotsByPreference(), "slot_options", "filtered_slot_options"
    )
    grouped = await transform_node(
        filtered, GroupSlotsByTime(), "filtered_slot_options", "grouped_slots"
    )
    result = await send_message_node(grouped, GroupedSlotsBuilder())
    result["should_proceed"] = False
    result["current_step"] = "awaiting_slot_selection"
    return result


async def ensure_filtered_slots(state: BookingState) -> BookingState:
    """Ensure filtered_slot_options exists (regenerate if missing on resume)."""
    if not state.get("filtered_slot_options") and state.get("slot_options"):
        logger.info("🔄 Regenerating filtered_slot_options on resume")
        state = await transform_node(
            state, FilterSlotsByPreference(), "slot_options", "filtered_slot_options"
        )
    return state


async def process_slot_selection(state: BookingState) -> BookingState:
    """Process slot selection from user."""
    # Ensure filtered_slot_options exists (regenerate if missing on resume)
    state = await ensure_filtered_slots(state)

    # Validate state before processing
    slot_opts = state.get("slot_options", [])
    filtered_opts = state.get("filtered_slot_options", [])
    logger.info(f"📊 Slot state: {len(slot_opts)} raw, {len(filtered_opts)} filtered")

    if len(filtered_opts) == 0 and len(slot_opts) > 0:
        logger.error("⚠️ BUG: filtered_slot_options empty but slot_options exists!")
        # Regenerate filtered options as fallback
        state = await ensure_filtered_slots(state)
        filtered_opts = state.get("filtered_slot_options", [])

    result = await handle_selection(
        state,
        selection_type="slot",
        options_key="filtered_slot_options",
        selected_key="slot",
    )
    if result.get("slot"):
        result["current_step"] = ""
        result["should_proceed"] = True
    return result


async def send_slot_error(state: BookingState) -> BookingState:
    """Send error message for invalid slot selection."""
    return await handle_selection_error(state, awaiting_step="awaiting_slot_selection")


# Create resume router for entry point
route_slot_entry = create_resume_router(
    awaiting_step="awaiting_slot_selection",
    resume_node="process_selection",
    fresh_node="fetch_slots",
    readiness_check=lambda s: bool(s.get("filtered_slot_options")),
    router_name="slot_entry",
)


def create_slot_group() -> StateGraph:
    """Create slot selection workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("entry", lambda s: s)
    workflow.add_node("fetch_slots", fetch_slots)
    workflow.add_node("show_slots", format_and_send_slots)
    workflow.add_node("process_selection", process_slot_selection)
    workflow.add_node("send_error", send_slot_error)
    workflow.set_entry_point("entry")
    workflow.add_conditional_edges(
        "entry",
        route_slot_entry,
        {"fetch_slots": "fetch_slots", "process_selection": "process_selection"},
    )
    workflow.add_edge("fetch_slots", "show_slots")
    workflow.add_edge("show_slots", END)
    workflow.add_conditional_edges(
        "process_selection",
        route_after_selection,
        {"selection_error": "send_error", "selection_success": END},
    )
    workflow.add_edge("send_error", END)
    return workflow.compile()

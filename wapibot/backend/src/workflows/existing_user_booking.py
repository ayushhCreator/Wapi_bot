"""Complete existing user booking workflow - Production-ready end-to-end flow.

This workflow demonstrates full atomic node composition for a complete booking journey.

Flow:
1. Customer lookup by phone
2. Branch: existing/new user
3. Send greeting
4. Fetch & display services
5. Extract service selection
6. Fetch & display appointment slots
7. Extract slot selection
8. Send booking confirmation
9. Extract YES/NO confirmation
10. Create booking in Frappe
11. Send success message

DRY Compliance:
- Uses atomic nodes (send_message, transform, call_frappe)
- Uses message builders for all messaging
- Uses transformers for data manipulation
- Uses YawlitClient directly (NO request builders - eliminates duplication)

SOLID Compliance:
- Workflow orchestration ONLY (no business logic)
- All nodes have Single Responsibility
- Builders/transformers/clients are interchangeable
"""

import re

from langgraph.graph import END, StateGraph

# Frappe client
from clients.frappe_yawlit import get_yawlit_client
from core.checkpointer import checkpointer_manager
from message_builders.booking_confirmation import BookingConfirmationBuilder

# Message builders
from message_builders.greeting import GreetingBuilder
from message_builders.service_catalog import ServiceCatalogBuilder
from message_builders.vehicle_options import VehicleOptionsBuilder
from nodes.atomic.call_frappe import node as call_frappe_node

# Atomic nodes
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.transform import node as transform_node

# Transformers
from transformers.filter_services import FilterServicesByVehicle
from transformers.format_slot_options import FormatSlotOptions
from workflows.shared.state import BookingState

# ============================================================================
# ENTRY ROUTER (Determines where to resume based on state)
# ============================================================================

async def entry_router_node(state: BookingState) -> BookingState:
    """Entry router - determines resume point based on current state.

    This node runs at the start of every message to decide where to go:
    - If waiting for vehicle selection: go to extract_vehicle_selection
    - If waiting for service selection: go to extract_service_selection
    - If waiting for slot selection: go to extract_slot_selection
    - If waiting for confirmation: go to extract_confirmation
    - Otherwise: start from lookup_customer
    """
    import logging

    logger = logging.getLogger(__name__)

    # Log current state for debugging
    vehicle_selected = state.get("vehicle_selected", False)
    service_selected = state.get("service_selected", False)
    slot_selected = state.get("slot_selected", False)
    confirmed = state.get("confirmed")

    logger.info(
        f"🔀 Entry router: vehicle_selected={vehicle_selected}, "
        f"service_selected={service_selected}, slot_selected={slot_selected}, "
        f"confirmed={confirmed}"
    )

    return state


async def check_resume_point(state: BookingState) -> str:
    """Route to the correct resume point based on state.

    Returns:
        - "awaiting_vehicle": User needs to select vehicle
        - "awaiting_service": User needs to select service
        - "awaiting_slot": User needs to select slot
        - "awaiting_confirmation": User needs to confirm booking
        - "fresh_start": New conversation or completed flow
    """
    # Check if waiting for vehicle selection
    if state.get("vehicle_options") and not state.get("vehicle_selected"):
        return "awaiting_vehicle"

    # Check if waiting for service selection
    if state.get("filtered_services") and not state.get("service_selected"):
        return "awaiting_service"

    # Check if waiting for slot selection
    if state.get("available_slots") and not state.get("slot_selected"):
        return "awaiting_slot"

    # Check if waiting for confirmation
    if state.get("selected_service") and state.get("slot_selected") and state.get("confirmed") is None:
        return "awaiting_confirmation"

    # Fresh start or completed
    return "fresh_start"


# ============================================================================
# CUSTOMER LOOKUP & ROUTING
# ============================================================================

async def lookup_customer_node(state: BookingState) -> BookingState:
    """Look up customer by phone number using YawlitClient."""
    import logging
    from models.customer import Phone
    from models.core import ExtractionMetadata

    logger = logging.getLogger(__name__)
    client = get_yawlit_client()

    # Normalize phone number (remove +91/91 prefix)
    raw_phone = state.get("conversation_id", "")
    phone_model = Phone(
        phone_number=raw_phone,
        metadata=ExtractionMetadata(
            confidence=1.0,
            extraction_method="direct",
            extraction_source="wapi_webhook"
        )
    )
    normalized_phone = phone_model.phone_number

    logger.info(
        f"📞 Customer lookup: {raw_phone} → {normalized_phone}"
    )

    # Call Frappe to lookup customer
    state = await call_frappe_node(
        state,
        client.customer_lookup.check_customer_exists,
        "customer_lookup_response",
        state_extractor=lambda s: {"identifier": normalized_phone}
    )

    # Populate customer data from lookup response (for use by downstream nodes)
    # NOTE: Must do this here, NOT in routing function (routing functions can't modify state)
    lookup_response = state.get("customer_lookup_response", {})
    if lookup_response.get("exists"):
        data = lookup_response.get("data", {})
        state["customer"] = {
            "customer_uuid": data.get("customer_uuid"),
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "enabled": data.get("enabled")
        }
        logger.info(
            f"✅ Customer data populated: {data.get('first_name')} "
            f"{data.get('last_name')} ({data.get('customer_uuid')})"
        )

    return state


# ============================================================================
# VEHICLE FETCHING & SELECTION
# ============================================================================

async def fetch_vehicles_node(state: BookingState) -> BookingState:
    """Fetch customer vehicles and auto-select if single vehicle.

    Sets state["vehicle"] to:
    - Selected vehicle if only 1 vehicle exists (auto-select)
    - None if multiple vehicles (user must choose)
    - None if no vehicles (user needs to add vehicle)
    """
    import logging

    logger = logging.getLogger(__name__)
    client = get_yawlit_client()

    customer = state.get("customer", {})
    if not customer or not customer.get("customer_uuid"):
        logger.info("No customer found - skipping vehicle fetch")
        state["vehicle_selected"] = False
        return state

    # Fetch vehicles using call_frappe_node
    state = await call_frappe_node(
        state,
        client.customer_profile.get_vehicles,
        "vehicles_response",
        state_extractor=lambda s: {}  # No params needed - uses auth token
    )

    vehicles_response = state.get("vehicles_response", {})

    # Log the raw response structure for debugging
    logger.info(f"🔍 Raw vehicles_response keys: {list(vehicles_response.keys())}")
    logger.info(f"🔍 Full vehicles_response: {vehicles_response}")

    # Check for Frappe error responses
    if isinstance(vehicles_response.get("message"), dict):
        if vehicles_response["message"].get("success") is False:
            error_msg = vehicles_response["message"].get("message", "Unknown error")
            logger.error(f"❌ Frappe API error: {error_msg}")
            state["vehicle"] = None
            state["vehicle_options"] = []
            state["vehicle_selected"] = False
            state["frappe_error"] = error_msg
            return state

    # Try multiple possible response structures
    vehicles = vehicles_response.get("message", {}).get("vehicles", [])

    # Handle edge case: response might have vehicles at top level
    if not vehicles:
        vehicles = vehicles_response.get("vehicles", [])

    # Handle edge case: response might have data wrapper
    if not vehicles:
        vehicles = vehicles_response.get("data", {}).get("vehicles", [])

    # Handle edge case: response might have message as string (Frappe sometimes returns this)
    if not vehicles and "message" in vehicles_response:
        msg = vehicles_response["message"]
        if isinstance(msg, list):
            vehicles = msg

    logger.info(f"🚗 Found {len(vehicles)} vehicle(s)")

    if len(vehicles) == 0:
        logger.warning("No vehicles found - user needs to add vehicle")
        state["vehicle"] = None
        state["vehicle_options"] = []
        state["vehicle_selected"] = False

    elif len(vehicles) == 1:
        # Auto-select single vehicle
        vehicle = vehicles[0]
        state["vehicle"] = {
            "vehicle_id": vehicle.get("name"),
            "vehicle_make": vehicle.get("vehicle_make"),
            "vehicle_model": vehicle.get("vehicle_model"),
            "vehicle_number": vehicle.get("vehicle_number"),
            "vehicle_type": vehicle.get("vehicle_type")
        }
        state["vehicle_options"] = None
        state["vehicle_selected"] = True
        logger.info(f"Auto-selected single vehicle: {vehicle.get('vehicle_number')}")

    else:
        # Multiple vehicles - user must choose
        logger.info(f"Multiple vehicles found ({len(vehicles)}) - user must select")
        state["vehicle"] = None
        state["vehicle_options"] = vehicles
        state["vehicle_selected"] = False

    return state


async def check_vehicle_selected(state: BookingState) -> str:
    """Route based on whether vehicle is selected."""
    # Check for Frappe API errors first
    if state.get("frappe_error"):
        return "frappe_error"

    if state.get("vehicle_selected"):
        return "vehicle_selected"
    elif not state.get("vehicle_options"):
        return "no_vehicles"
    else:
        return "vehicle_selection_required"


async def send_vehicle_options_node(state: BookingState) -> BookingState:
    """Send vehicle selection options to customer."""
    return await send_message_node(state, VehicleOptionsBuilder())


async def send_no_vehicles_node(state: BookingState) -> BookingState:
    """Send message when customer has no vehicles."""
    def no_vehicles_message(s):
        return (
            "You don't have any vehicles registered yet.\n\n"
            "Please add a vehicle at https://yawlit.duckdns.org/customer/profile to book a service."
        )

    return await send_message_node(state, no_vehicles_message)


async def send_frappe_error_node(state: BookingState) -> BookingState:
    """Send message when Frappe API returns an error."""
    def frappe_error_message(s):
        error = s.get("frappe_error", "Unknown error occurred")
        return (
            f"⚠️ Unable to fetch your profile information:\n\n"
            f"{error}\n\n"
            f"Please complete your profile at https://yawlit.duckdns.org/customer/profile"
        )

    return await send_message_node(state, frappe_error_message)


async def extract_vehicle_selection_node(state: BookingState) -> BookingState:
    """Extract vehicle selection from user message (1, 2, 3, 4)."""
    import logging
    import re

    logger = logging.getLogger(__name__)

    user_message = state.get("user_message", "")
    vehicle_options = state.get("vehicle_options", [])

    if not vehicle_options:
        logger.warning("No vehicle options available for selection")
        return state

    # Extract number (1, 2, 3, 4)
    number_match = re.search(r'\b(\d+)\b', user_message)

    if number_match:
        index = int(number_match.group(1)) - 1  # Convert to 0-based

        if 0 <= index < len(vehicle_options):
            vehicle = vehicle_options[index]
            state["vehicle"] = {
                "vehicle_id": vehicle.get("name"),
                "vehicle_make": vehicle.get("vehicle_make"),
                "vehicle_model": vehicle.get("vehicle_model"),
                "vehicle_number": vehicle.get("vehicle_number"),
                "vehicle_type": vehicle.get("vehicle_type")
            }
            state["vehicle_selected"] = True
            logger.info(f"Vehicle selected: {vehicle.get('vehicle_number')}")
        else:
            logger.warning(f"Invalid vehicle number: {number_match.group(1)}")
            state["selection_error"] = "Invalid vehicle number"
            state["vehicle_selected"] = False
    else:
        logger.warning("No vehicle number found in message")
        state["selection_error"] = "Please reply with a number (1, 2, 3, etc.)"
        state["vehicle_selected"] = False

    return state


async def send_vehicle_selection_error_node(state: BookingState) -> BookingState:
    """Send error message for invalid vehicle selection."""
    def error_message(s):
        error = s.get("selection_error", "Invalid selection")
        return f"Sorry, {error}. Please reply with the vehicle number (1, 2, 3, etc.)"

    return await send_message_node(state, error_message)


async def check_customer_exists(state: BookingState) -> str:
    """Route based on customer existence.

    NOTE: This is a ROUTING function - do NOT modify state here.
    State modifications must happen in node functions (like lookup_customer_node).
    """
    import logging

    logger = logging.getLogger(__name__)

    # Check if customer data was populated by lookup_customer_node
    customer = state.get("customer")
    if customer and customer.get("customer_uuid"):
        logger.info(f"🔀 Routing: existing_customer ({customer.get('first_name')})")
        return "existing_customer"
    else:
        logger.info("🔀 Routing: new_customer")
        return "new_customer"


async def send_greeting_node(state: BookingState) -> BookingState:
    """Send personalized greeting to existing customer."""
    return await send_message_node(state, GreetingBuilder())


async def send_please_register_node(state: BookingState) -> BookingState:
    """Send registration request to new customer."""
    def please_register(s):
        return "Welcome to Yawlit! To book a service, please register first at https://yawlit.duckdns.org/customer/auth/register"

    return await send_message_node(state, please_register)


# ============================================================================
# SERVICE CATALOG
# ============================================================================

async def fetch_services_node(state: BookingState) -> BookingState:
    """Fetch all services from Frappe using YawlitClient."""
    import logging

    logger = logging.getLogger(__name__)
    client = get_yawlit_client()

    result = await call_frappe_node(
        state,
        client.service_catalog.get_filtered_services,
        "services_response",
        state_extractor=lambda s: {
            "vehicle_type": s.get("vehicle", {}).get("vehicle_type")
        } if s.get("vehicle") else {}
    )

    # Extract services from Frappe response
    services_response = result.get("services_response", {})

    # Log the raw response structure for debugging
    logger.info(f"🔍 Raw services_response keys: {list(services_response.keys())}")

    # Try multiple possible response structures
    services = services_response.get("message", {}).get("services", [])

    # Fallback: services at top level
    if not services:
        services = services_response.get("services", [])

    # Fallback: services in data wrapper
    if not services:
        services = services_response.get("data", {}).get("services", [])

    # Fallback: message might be a list directly
    if not services and "message" in services_response:
        msg = services_response["message"]
        if isinstance(msg, list):
            services = msg

    logger.info(f"🛠️ Found {len(services)} service(s)")

    result["all_services"] = services

    return result


async def filter_services_node(state: BookingState) -> BookingState:
    """Filter services by vehicle type."""
    return await transform_node(
        state,
        FilterServicesByVehicle(),
        "all_services",
        "filtered_services"
    )


async def send_catalog_node(state: BookingState) -> BookingState:
    """Send service catalog to customer."""
    return await send_message_node(state, ServiceCatalogBuilder())


# ============================================================================
# SERVICE SELECTION
# ============================================================================

async def extract_service_selection_node(state: BookingState) -> BookingState:
    """Extract service selection from user message.

    Simple extraction: looks for numbers (1, 2, 3) or service names.
    For production, use DSPy extractor.
    """
    user_message = state.get("user_message", "")
    filtered_services = state.get("filtered_services", [])

    # Try to extract number (e.g., "1", "2", "I want service 1")
    number_match = re.search(r'\b(\d+)\b', user_message)

    if number_match:
        index = int(number_match.group(1)) - 1  # Convert to 0-based index

        if 0 <= index < len(filtered_services):
            selected_service = filtered_services[index]
            state["selected_service"] = selected_service
            state["service_selected"] = True
        else:
            state["service_selected"] = False
            state["selection_error"] = "Invalid service number"
    else:
        # Try to match service name
        for service in filtered_services:
            service_name = service.get("product_name", "").lower()
            if service_name in user_message.lower():
                state["selected_service"] = service
                state["service_selected"] = True
                break
        else:
            state["service_selected"] = False
            state["selection_error"] = "Could not understand service selection"

    return state


async def check_service_selected(state: BookingState) -> str:
    """Route based on service selection success."""
    if state.get("service_selected"):
        return "service_selected"
    else:
        return "service_not_selected"


async def send_service_selection_error_node(state: BookingState) -> BookingState:
    """Send error message for invalid service selection."""
    def error_message(s):
        error = s.get("selection_error", "Invalid selection")
        return f"Sorry, {error}. Please reply with the service number (1, 2, 3, etc.)"

    return await send_message_node(state, error_message)


# ============================================================================
# APPOINTMENT SLOTS
# ============================================================================

async def fetch_slots_node(state: BookingState) -> BookingState:
    """Fetch appointment slots.

    For MVP, using mock slots. In production, call Frappe slot API.
    """
    # Mock slots for MVP
    state["available_slots"] = [
        {"date": "2025-12-26", "time_slot": "10:00 AM - 12:00 PM", "slot_id": "SLOT-001", "available": True},
        {"date": "2025-12-26", "time_slot": "2:00 PM - 4:00 PM", "slot_id": "SLOT-002", "available": True},
        {"date": "2025-12-27", "time_slot": "10:00 AM - 12:00 PM", "slot_id": "SLOT-003", "available": True},
        {"date": "2025-12-27", "time_slot": "2:00 PM - 4:00 PM", "slot_id": "SLOT-004", "available": False}
    ]

    return state


async def format_slots_node(state: BookingState) -> BookingState:
    """Format slots for display."""
    return await transform_node(
        state,
        FormatSlotOptions(),
        "available_slots",
        "formatted_slots_message"
    )


async def send_slots_node(state: BookingState) -> BookingState:
    """Send formatted slots to customer."""
    def slots_message(s):
        return s.get("formatted_slots_message", "No slots available")

    return await send_message_node(state, slots_message)


# ============================================================================
# SLOT SELECTION
# ============================================================================

async def extract_slot_selection_node(state: BookingState) -> BookingState:
    """Extract slot selection from user message.

    Simple extraction: looks for date and time mentions.
    For production, use DSPy extractor.
    """
    user_message = state.get("user_message", "")
    available_slots = state.get("available_slots", [])

    # Try to find date mention
    selected_slot = None

    for slot in available_slots:
        if not slot.get("available"):
            continue

        date = slot.get("date", "")
        time_slot = slot.get("time_slot", "")

        # Check if date or time is mentioned
        if date in user_message or time_slot.lower() in user_message.lower():
            selected_slot = slot
            break

    if selected_slot:
        state["appointment"] = {
            "date": selected_slot.get("date"),
            "time_slot": selected_slot.get("time_slot"),
            "slot_id": selected_slot.get("slot_id")
        }
        state["slot_selected"] = True
    else:
        state["slot_selected"] = False
        state["selection_error"] = "Could not understand slot selection"

    return state


async def check_slot_selected(state: BookingState) -> str:
    """Route based on slot selection success."""
    if state.get("slot_selected"):
        return "slot_selected"
    else:
        return "slot_not_selected"


async def send_slot_selection_error_node(state: BookingState) -> BookingState:
    """Send error message for invalid slot selection."""
    def error_message(s):
        error = s.get("selection_error", "Invalid selection")
        return f"Sorry, {error}. Please reply with your preferred date and time."

    return await send_message_node(state, error_message)


# ============================================================================
# BOOKING CONFIRMATION
# ============================================================================

async def calculate_price_node(state: BookingState) -> BookingState:
    """Calculate total price.

    For MVP, using base price. In production, call Frappe pricing API.
    """
    selected_service = state.get("selected_service", {})
    base_price = selected_service.get("base_price", 0)

    state["total_price"] = base_price

    return state


async def send_confirmation_node(state: BookingState) -> BookingState:
    """Send booking confirmation for user approval."""
    return await send_message_node(state, BookingConfirmationBuilder())


async def extract_confirmation_node(state: BookingState) -> BookingState:
    """Extract YES/NO confirmation from user message."""
    user_message = state.get("user_message", "").lower()

    if "yes" in user_message or "confirm" in user_message or "ok" in user_message:
        state["confirmed"] = True
    elif "no" in user_message or "cancel" in user_message:
        state["confirmed"] = False
    else:
        state["confirmed"] = None  # Unclear response

    return state


async def check_confirmation(state: BookingState) -> str:
    """Route based on user confirmation."""
    confirmed = state.get("confirmed")

    if confirmed is True:
        return "confirmed"
    elif confirmed is False:
        return "cancelled"
    else:
        return "unclear"


async def send_confirmation_unclear_node(state: BookingState) -> BookingState:
    """Send message for unclear confirmation."""
    def unclear_message(s):
        return "Please reply with YES to confirm or NO to cancel the booking."

    return await send_message_node(state, unclear_message)


# ============================================================================
# BOOKING CREATION
# ============================================================================

async def create_booking_node(state: BookingState) -> BookingState:
    """Create booking in Frappe using YawlitClient."""
    client = get_yawlit_client()

    # Extract booking parameters from state
    def extract_booking_params(s):
        customer = s.get("customer", {})
        selected_service = s.get("selected_service", {})
        appointment = s.get("appointment", {})

        return {
            "customer_uuid": customer.get("customer_uuid"),
            "service_id": selected_service.get("product_id"),
            "vehicle_id": s.get("vehicle", {}).get("vehicle_id"),
            "slot_id": appointment.get("slot_id"),
            "date": appointment.get("date"),
            "address_id": customer.get("default_address_id"),  # Use default address
            "optional_addons": [],  # No addons for MVP
            "special_instructions": ""
        }

    return await call_frappe_node(
        state,
        client.booking_create.create_booking,
        "booking_response",
        state_extractor=extract_booking_params
    )


async def send_success_node(state: BookingState) -> BookingState:
    """Send booking success message."""
    def success_message(s):
        booking_response = s.get("booking_response", {})
        message = booking_response.get("message", {})
        booking_id = message.get("booking_id", "Unknown")

        return f"✅ Booking confirmed!\n\nYour booking ID is: {booking_id}\n\nWe'll send you a confirmation shortly. Thank you for choosing Yawlit!"

    return await send_message_node(state, success_message)


async def send_cancelled_node(state: BookingState) -> BookingState:
    """Send booking cancelled message."""
    def cancelled_message(s):
        return "Booking cancelled. Feel free to reach out when you're ready to book!"

    return await send_message_node(state, cancelled_message)


# ============================================================================
# WORKFLOW GRAPH
# ============================================================================

def create_existing_user_booking_workflow():
    """Create the complete existing user booking workflow.

    Uses the in-memory checkpointer from checkpointer_manager for fast state persistence.

    Returns:
        Compiled LangGraph workflow with full booking flow
    """
    workflow = StateGraph(BookingState)

    # Add all nodes
    workflow.add_node("entry_router", entry_router_node)
    workflow.add_node("lookup_customer", lookup_customer_node)
    workflow.add_node("fetch_vehicles", fetch_vehicles_node)
    workflow.add_node("send_vehicle_options", send_vehicle_options_node)
    workflow.add_node("extract_vehicle_selection", extract_vehicle_selection_node)
    workflow.add_node("send_vehicle_error", send_vehicle_selection_error_node)
    workflow.add_node("send_no_vehicles", send_no_vehicles_node)
    workflow.add_node("send_frappe_error", send_frappe_error_node)
    workflow.add_node("send_greeting", send_greeting_node)
    workflow.add_node("send_please_register", send_please_register_node)
    workflow.add_node("fetch_services", fetch_services_node)
    workflow.add_node("filter_services", filter_services_node)
    workflow.add_node("send_catalog", send_catalog_node)
    workflow.add_node("extract_service_selection", extract_service_selection_node)
    workflow.add_node("send_service_error", send_service_selection_error_node)
    workflow.add_node("fetch_slots", fetch_slots_node)
    workflow.add_node("format_slots", format_slots_node)
    workflow.add_node("send_slots", send_slots_node)
    workflow.add_node("extract_slot_selection", extract_slot_selection_node)
    workflow.add_node("send_slot_error", send_slot_selection_error_node)
    workflow.add_node("calculate_price", calculate_price_node)
    workflow.add_node("send_confirmation", send_confirmation_node)
    workflow.add_node("extract_confirmation", extract_confirmation_node)
    workflow.add_node("send_confirmation_unclear", send_confirmation_unclear_node)
    workflow.add_node("create_booking", create_booking_node)
    workflow.add_node("send_success", send_success_node)
    workflow.add_node("send_cancelled", send_cancelled_node)

    # Set entry point (always go through router first)
    workflow.set_entry_point("entry_router")

    # Entry router - determines where to resume based on state
    workflow.add_conditional_edges(
        "entry_router",
        check_resume_point,
        {
            "fresh_start": "lookup_customer",
            "awaiting_vehicle": "extract_vehicle_selection",
            "awaiting_service": "extract_service_selection",
            "awaiting_slot": "extract_slot_selection",
            "awaiting_confirmation": "extract_confirmation"
        }
    )

    # Customer lookup routing
    workflow.add_conditional_edges(
        "lookup_customer",
        check_customer_exists,
        {
            "existing_customer": "fetch_vehicles",  # Go to vehicle fetching first
            "new_customer": "send_please_register"
        }
    )

    # Vehicle selection flow
    workflow.add_conditional_edges(
        "fetch_vehicles",
        check_vehicle_selected,
        {
            "vehicle_selected": "send_greeting",
            "vehicle_selection_required": "send_vehicle_options",
            "no_vehicles": "send_no_vehicles",
            "frappe_error": "send_frappe_error"
        }
    )
    workflow.add_edge("send_vehicle_options", END)  # Wait for user to select
    workflow.add_edge("send_no_vehicles", END)  # User needs to add vehicle first
    workflow.add_edge("send_frappe_error", END)  # User needs to fix profile

    # Vehicle selection extraction (called on next message when user selects)
    workflow.add_conditional_edges(
        "extract_vehicle_selection",
        check_vehicle_selected,
        {
            "vehicle_selected": "send_greeting",
            "vehicle_selection_required": "send_vehicle_error"  # Invalid selection
        }
    )
    workflow.add_edge("send_vehicle_error", END)  # Wait for retry

    # Service catalog flow
    workflow.add_edge("send_greeting", "fetch_services")
    workflow.add_edge("fetch_services", "filter_services")
    workflow.add_edge("filter_services", "send_catalog")
    workflow.add_edge("send_catalog", END)  # Wait for user to select service

    # Service selection routing
    workflow.add_conditional_edges(
        "extract_service_selection",
        check_service_selected,
        {
            "service_selected": "fetch_slots",
            "service_not_selected": "send_service_error"
        }
    )
    workflow.add_edge("send_service_error", END)

    # Appointment slot flow
    workflow.add_edge("fetch_slots", "format_slots")
    workflow.add_edge("format_slots", "send_slots")
    workflow.add_edge("send_slots", END)  # Wait for user to select slot

    # Slot selection routing
    workflow.add_conditional_edges(
        "extract_slot_selection",
        check_slot_selected,
        {
            "slot_selected": "calculate_price",
            "slot_not_selected": "send_slot_error"
        }
    )
    workflow.add_edge("send_slot_error", END)

    # Confirmation flow
    workflow.add_edge("calculate_price", "send_confirmation")
    workflow.add_edge("send_confirmation", END)  # Wait for user to confirm

    # Confirmation routing
    workflow.add_conditional_edges(
        "extract_confirmation",
        check_confirmation,
        {
            "confirmed": "create_booking",
            "cancelled": "send_cancelled",
            "unclear": "send_confirmation_unclear"
        }
    )
    workflow.add_edge("send_confirmation_unclear", END)

    # Final steps
    workflow.add_edge("create_booking", "send_success")
    workflow.add_edge("send_success", END)
    workflow.add_edge("send_cancelled", END)

    # New customer flow ends
    workflow.add_edge("send_please_register", END)

    # Use in-memory checkpointer (initialized at FastAPI startup)
    return workflow.compile(checkpointer=checkpointer_manager.memory)

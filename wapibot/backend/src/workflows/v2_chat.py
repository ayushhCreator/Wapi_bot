"""V2 Chat workflow using atomic nodes.

Demonstrates the new atomic node architecture:
- Same extract node configured for different data
- Atomic nodes replace domain-specific nodes
- Configuration over specialization

Flow: extract_name → validate_name → END
"""

from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic import extract_node
from dspy_modules.extractors.name_extractor import NameExtractor
from fallbacks.name_fallback import RegexNameExtractor


# Configure extractor instances
name_extractor = NameExtractor()
regex_fallback = RegexNameExtractor()


# Wrapper functions for atomic nodes with specific configurations
async def extract_name(state: BookingState) -> BookingState:
    """Extract name using atomic extract node.

    This is the SAME atomic node used for phone, vehicle, etc.
    Just configured differently!
    """
    return await extract_node(
        state=state,
        extractor=name_extractor,
        field_path="customer.first_name",
        fallback_fn=lambda msg: regex_fallback.extract(msg),
        metadata_path="customer.extraction_metadata",
    )


async def generate_response(state: BookingState) -> BookingState:
    """Generate response message based on extracted data.

    Simple response node for MVP.
    """
    customer = state.get("customer", {})
    first_name = customer.get("first_name", "")

    if first_name:
        state["response"] = f"Nice to meet you, {first_name}! 👋"
        state["completeness"] = 0.3
    else:
        state["response"] = "I didn't catch your name. What's your name?"
        state["completeness"] = 0.0

    return state


def create_v2_workflow() -> StateGraph:
    """Create V2 workflow using atomic nodes.

    Flow:
        extract_name → generate_response → END

    This demonstrates:
    - Atomic extract node (works with ANY extractor)
    - Configuration over specialization
    - Simple MVP flow

    Note: Validation skipped for MVP to keep it simple.
    Will add atomic validate node in next iteration.
    """
    workflow = StateGraph(BookingState)

    # Add atomic nodes configured for name extraction
    workflow.add_node("extract_name", extract_name)
    workflow.add_node("generate_response", generate_response)

    # Simple linear flow for MVP
    workflow.set_entry_point("extract_name")
    workflow.add_edge("extract_name", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow


# Compile workflow
v2_chat_workflow = create_v2_workflow().compile()

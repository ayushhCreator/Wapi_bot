"""Simple chat workflow for MVP.

Just name extraction for now - proves the concept works.
"""

from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.extraction.extract_name import node as extract_name_node


def create_simple_workflow() -> StateGraph:
    """Create minimal working workflow for MVP.

    Flow: extract_name → END
    """
    workflow = StateGraph(BookingState)

    # Add name extraction node
    workflow.add_node("extract_name", extract_name_node)

    # Simple linear flow for MVP
    workflow.set_entry_point("extract_name")
    workflow.add_edge("extract_name", END)

    return workflow


# Compile workflow (no checkpoint for MVP simplicity)
simple_chat_workflow = create_simple_workflow().compile()

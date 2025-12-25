"""Existing user booking workflow - Blender-style composition.

This workflow is a COMPOSITION of 5 node groups:
1. Profile Group: Customer lookup + validation
2. Vehicle Group: Vehicle selection (if needed)
3. Service Group: Service catalog + selection
4. Slot Group: Appointment slot selection
5. Booking Group: Price calculation + confirmation + creation

Each group is a mini-workflow (subgraph) that can be:
- Tested independently
- Reused in other workflows
- Modified without affecting others

This file is just the orchestrator - it chains groups together.
Total: ~700 lines across 14 files vs 1,158 lines in 1 monolith.
"""

from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from core.checkpointer import checkpointer_manager

# Import node groups (mini-workflows)
from workflows.node_groups.profile_group import create_profile_group
from workflows.node_groups.vehicle_group import create_vehicle_group
from workflows.node_groups.service_group import create_service_group
from workflows.node_groups.slot_group import create_slot_group
from workflows.node_groups.booking_group import create_booking_group


def create_booking_workflow():
    """Create existing user booking workflow.

    Architecture:
    - 5 composable node groups (like Blender's Geometry Nodes)
    - Each group is self-contained mini-workflow
    - Main graph just chains groups together
    """
    workflow = StateGraph(BookingState)

    # Add node groups as composable units
    workflow.add_node("profile_check", create_profile_group())
    workflow.add_node("vehicle_selection", create_vehicle_group())
    workflow.add_node("service_selection", create_service_group())
    workflow.add_node("slot_selection", create_slot_group())
    workflow.add_node("booking_confirmation", create_booking_group())

    # Chain groups sequentially
    workflow.set_entry_point("profile_check")
    workflow.add_edge("profile_check", "vehicle_selection")
    workflow.add_edge("vehicle_selection", "service_selection")
    workflow.add_edge("service_selection", "slot_selection")
    workflow.add_edge("slot_selection", "booking_confirmation")
    workflow.add_edge("booking_confirmation", END)

    # Compile with checkpointing (checkpointer initialized in main.py lifespan)
    return workflow.compile(checkpointer=checkpointer_manager.memory)

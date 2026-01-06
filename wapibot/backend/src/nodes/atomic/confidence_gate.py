"""Atomic confidence gate node - works with ANY confidence function.

Gates workflow based on confidence scores. Can use:
- Simple threshold: confidence > 0.8
- LLM-based confidence: Ask LLM to score extraction
- Custom function: Any callable that returns bool

Usage:
    # Simple threshold
    confidence_gate.node(state, "customer.confidence", threshold=0.8)

    # Custom function
    confidence_gate.node(state, "customer", confidence_fn=is_name_valid)

    # LLM-based
    confidence_gate.node(state, "customer", confidence_fn=llm_confidence_scorer)
"""

import logging
from typing import Any, Callable, Optional
from workflows.shared.state import BookingState
from core.config import settings

logger = logging.getLogger(__name__)


def get_nested_field(state: BookingState, field_path: str) -> Any:
    """Get nested field from state using dot notation."""
    parts = field_path.split(".")
    current = state

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


async def node(
    state: BookingState,
    confidence_path: str,
    threshold: Optional[float] = None,
    confidence_fn: Optional[Callable[[Any], bool]] = None,
    gate_name: str = "confidence_check",
) -> BookingState:
    """Atomic confidence gate - routes workflow based on confidence.

    This node doesn't modify state, it just returns a gate decision
    that LangGraph conditional edges can use.

    Args:
        state: Current booking state
        confidence_path: Path to confidence value OR path to data to check
        threshold: Simple threshold (e.g., 0.8). Uses config default if None.
        confidence_fn: Custom function that takes data and returns bool
        gate_name: Name for logging

    Returns:
        State with gate decision stored

    Example:
        # Simple threshold gating
        state = await confidence_gate.node(
            state,
            "customer.confidence",
            threshold=0.8
        )
        # state["gate_decision"] = "high_confidence" or "low_confidence"

        # Custom function (e.g., check if vehicle brand is valid)
        def is_valid_brand(data):
            return data.get("brand") not in VEHICLE_BRANDS

        state = await confidence_gate.node(
            state,
            "customer",
            confidence_fn=is_valid_brand
        )

        # LLM-based confidence
        def llm_scorer(data):
            # Ask LLM: "Is this a valid customer name?"
            return llm_confidence > 0.8

        state = await confidence_gate.node(
            state,
            "customer",
            confidence_fn=llm_scorer
        )
    """
    # Use custom function if provided
    if confidence_fn is not None:
        try:
            data = get_nested_field(state, confidence_path)

            if data is None:
                logger.warning(f"⚠️ No data at {confidence_path} for confidence check")
                state["gate_decision"] = "low_confidence"
                return state

            # Call custom confidence function
            is_confident = confidence_fn(data)

            if is_confident:
                logger.info(f"✅ {gate_name}: Custom function passed")
                state["gate_decision"] = "high_confidence"
            else:
                logger.info(f"⚠️ {gate_name}: Custom function failed")
                state["gate_decision"] = "low_confidence"

            return state

        except Exception as e:
            logger.error(f"❌ Confidence function error: {e}")
            state["gate_decision"] = "low_confidence"
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"confidence_gate_error_{gate_name}")
            return state

    # Simple threshold check
    else:
        confidence_value = get_nested_field(state, confidence_path)

        if confidence_value is None:
            logger.warning(f"⚠️ No confidence value at {confidence_path}")
            state["gate_decision"] = "low_confidence"
            return state

        # Use threshold from parameter or config
        threshold_value = (
            threshold if threshold is not None else settings.confidence_high
        )

        if confidence_value >= threshold_value:
            logger.info(
                f"✅ {gate_name}: {confidence_value:.2f} >= {threshold_value:.2f}"
            )
            state["gate_decision"] = "high_confidence"
        else:
            logger.info(
                f"⚠️ {gate_name}: {confidence_value:.2f} < {threshold_value:.2f}"
            )
            state["gate_decision"] = "low_confidence"

        return state


def get_gate_decision(state: BookingState) -> str:
    """Helper function for LangGraph conditional edges.

    Returns the gate decision for routing.

    Usage in LangGraph:
        workflow.add_conditional_edges(
            "confidence_gate",
            confidence_gate.get_gate_decision,
            {
                "high_confidence": "next_step",
                "low_confidence": "ask_user"
            }
        )
    """
    return state.get("gate_decision", "low_confidence")

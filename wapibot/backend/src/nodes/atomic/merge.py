"""Atomic merge node - confidence-based data merging.

Prevents V1's critical bug: "Shukriya" overwriting "Sneha Reddy".
Only merge new data if confidence is HIGHER than existing data.

Usage:
    # Merge new name data (only if more confident)
    merge.node(state, new_data, "customer", 0.9)

    # Merge vehicle data (SAME node, different path!)
    merge.node(state, new_vehicle, "vehicle", 0.8)

    # Custom merge function
    merge.node(state, new_data, "customer", merge_fn=custom_merger)
"""

import logging
from typing import Any, Callable, Optional, Dict
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


def set_nested_field(state: BookingState, field_path: str, value: Any) -> None:
    """Set nested field in state using dot notation."""
    parts = field_path.split(".")
    current = state

    for part in parts[:-1]:
        if part not in current or current[part] is None:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value


def default_merge_strategy(
    existing: Dict[str, Any],
    new: Dict[str, Any],
    existing_confidence: float,
    new_confidence: float
) -> Dict[str, Any]:
    """Default merge strategy: only accept if new confidence is higher.

    This prevents V1's critical bug where "Shukriya" overwrote "Sneha Reddy".

    Args:
        existing: Current data in state
        new: New data to potentially merge
        existing_confidence: Confidence of existing data
        new_confidence: Confidence of new data

    Returns:
        Data to use (either existing or new)
    """
    if new_confidence > existing_confidence:
        logger.info(
            f"✅ Accepting new data (confidence {new_confidence:.2f} > {existing_confidence:.2f})"
        )
        return new
    else:
        logger.info(
            f"⏭️ Keeping existing data (confidence {existing_confidence:.2f} >= {new_confidence:.2f})"
        )
        return existing


async def node(
    state: BookingState,
    new_data: Dict[str, Any],
    data_path: str,
    new_confidence: float,
    merge_fn: Optional[Callable] = None,
    confidence_field: str = "confidence",
    turn: Optional[int] = None
) -> BookingState:
    """Atomic merge node - confidence-based data merging.

    Critical for preventing V1's data overwrite bugs.
    Only updates state if new confidence > existing confidence.

    Args:
        state: Current booking state
        new_data: New data to potentially merge
        data_path: Path to data in state (e.g., "customer", "vehicle")
        new_confidence: Confidence score of new data (0.0-1.0)
        merge_fn: Optional custom merge function
        confidence_field: Field name for confidence in data (default: "confidence")
        turn: Optional turn number for tracking

    Returns:
        Updated state (only if new data is more confident)

    Example:
        # Extract name with confidence 0.9
        name_data = {"first_name": "Hrijul", "last_name": "Dey"}
        state = await merge.node(state, name_data, "customer", 0.9)

        # Later, low-confidence extraction tries to overwrite
        bad_data = {"first_name": "Shukriya"}  # Greeting misinterpreted
        state = await merge.node(state, bad_data, "customer", 0.5)
        # Result: Original "Hrijul" preserved! 0.5 < 0.9

        # Same node, different data path!
        vehicle_data = {"brand": "TATA", "model": "Punch"}
        state = await merge.node(state, vehicle_data, "vehicle", 0.8)
    """
    # Get existing data
    existing_data = get_nested_field(state, data_path)

    # If no existing data, just set the new data
    if existing_data is None or not existing_data:
        logger.info(f"✅ Setting {data_path} (no existing data)")
        merged = {**new_data, confidence_field: new_confidence}

        if turn is not None:
            merged["turn_extracted"] = turn

        set_nested_field(state, data_path, merged)
        return state

    # Get existing confidence
    existing_confidence = existing_data.get(confidence_field, 0.0)

    # Use custom merge function if provided
    if merge_fn is not None:
        try:
            merged = merge_fn(
                existing_data,
                new_data,
                existing_confidence,
                new_confidence
            )
            merged[confidence_field] = max(existing_confidence, new_confidence)

            if turn is not None:
                merged["turn_extracted"] = turn

            set_nested_field(state, data_path, merged)
            return state

        except Exception as e:
            logger.error(f"❌ Custom merge function failed: {e}")
            # Fall back to default strategy

    # Default strategy: only update if new confidence is higher
    if new_confidence > existing_confidence:
        logger.info(
            f"✅ Updating {data_path}: new confidence {new_confidence:.2f} > "
            f"existing {existing_confidence:.2f}"
        )

        # Merge new data into existing (preserves other fields)
        merged = {**existing_data, **new_data, confidence_field: new_confidence}

        if turn is not None:
            merged["turn_extracted"] = turn

        set_nested_field(state, data_path, merged)

    else:
        logger.info(
            f"⏭️ Keeping {data_path}: existing confidence {existing_confidence:.2f} >= "
            f"new {new_confidence:.2f}"
        )
        # No change to state

    return state

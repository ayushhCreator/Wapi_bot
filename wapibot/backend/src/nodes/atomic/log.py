"""Atomic log node - structured logging for brain learning and debugging.

SOLID Principles:
- Single Responsibility: ONLY logs events in structured format
- Open/Closed: Extensible via event types
- Interface Segregation: Simple logging interface

Blender Design:
- Atomic operation for structured logging
- Brain uses logs for reinforcement learning
- Replaces scattered logger.info() calls with structured events
"""

import logging
import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from workflows.shared.state import BookingState
from core.brain_config import get_brain_settings
from repositories.brain_decision_repo import BrainDecisionRepository
from models.brain_decision import BrainDecision

logger = logging.getLogger(__name__)


async def node(
    state: BookingState,
    event_type: str,
    event_data: Optional[Dict[str, Any]] = None,
    severity: str = "info",
) -> BookingState:
    """Atomic structured logging node - logs events for brain learning.

    Logs events in a structured format that brain can analyze for:
    - Reinforcement learning (successful vs failed paths)
    - Pattern detection (user behavior)
    - Performance metrics (API latency, extraction success rates)

    Args:
        state: Current booking state
        event_type: Type of event (e.g., "extraction_success", "api_call", "validation_failed")
        event_data: Additional structured data about the event
        severity: Log level ("debug", "info", "warning", "error")

    Returns:
        Unchanged state (logging is side-effect only)

    Examples:
        # Log successful extraction
        await log.node(state, "extraction_success", {
            "field": "customer.first_name",
            "method": "dspy",
            "confidence": 0.95
        })

        # Log API call
        await log.node(state, "api_call", {
            "endpoint": "get_available_slots",
            "latency_ms": 234,
            "status": "success"
        })

        # Log validation failure
        await log.node(state, "validation_failed", {
            "field": "phone",
            "reason": "invalid_format"
        }, severity="warning")
    """
    brain_settings = get_brain_settings()

    # Build structured log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "conversation_id": state.get("conversation_id"),
        "current_step": state.get("current_step"),
        "brain_mode": brain_settings.brain_mode
        if brain_settings.brain_enabled
        else "disabled",
        "data": event_data or {},
    }

    # Log to standard logger
    log_message = f"📊 {event_type}: {event_data}"
    if severity == "debug":
        logger.debug(log_message)
    elif severity == "warning":
        logger.warning(log_message)
    elif severity == "error":
        logger.error(log_message)
    else:
        logger.info(log_message)

    # Send to brain memory for RL learning (Phase 4 Integration)
    # Brain will use these logs to learn patterns and improve decisions
    if brain_settings.brain_enabled and brain_settings.rl_gym_enabled:
        try:
            # Create brain decision record for this event
            decision = BrainDecision(
                decision_id=f"log_{uuid.uuid4().hex[:8]}",
                conversation_id=state.get("conversation_id", "unknown"),
                user_message=state.get("user_message", ""),
                conversation_history=json.dumps(
                    state.get("history", [])[-3:]
                ),  # Last 3 messages
                state_snapshot=json.dumps(
                    {
                        "event_type": event_type,
                        "severity": severity,
                        "data": event_data or {},
                    }
                ),
                brain_mode=brain_settings.brain_mode,
                action_taken=f"log:{event_type}",
                workflow_outcome=severity,  # Maps to success/warning/error
            )

            # Save to RL Gym database
            repo = BrainDecisionRepository()
            repo.save(decision)
            logger.debug(f"🧠 Event logged to brain_gym.db: {event_type}")
        except Exception as e:
            logger.debug(f"⚠️ Failed to save event to brain memory: {e}")

    return state

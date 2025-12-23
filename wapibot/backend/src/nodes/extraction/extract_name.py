"""Name extraction node with 3-tier resilience.

Tier 1: DSPy LLM extraction (best quality)
Tier 2: Regex fallback (fast, reliable)
Tier 3: Ask user (graceful degradation)
"""

import asyncio
import logging
from typing import Dict, Any
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)


# Tier 1: DSPy Extraction (best quality, LLM-based)
async def extract_name_dspy(state: BookingState) -> Dict[str, Any]:
    """Extract name using DSPy module (LLM-based)."""
    try:
        # Import DSPy module (to be implemented)
        # from dspy_modules.extractors import NameExtractor
        # extractor = NameExtractor()

        # Simulate DSPy extraction (replace with actual implementation)
        result = await asyncio.wait_for(
            asyncio.sleep(0.1),  # Placeholder: replace with actual DSPy call
            timeout=5.0
        )

        # Parse result
        # result = extractor(state["history"], state["user_message"])

        # Return extracted data
        return {
            "first_name": "John",  # Placeholder
            "last_name": "Doe",    # Placeholder
            "extraction_method": "dspy",
            "confidence": 0.95
        }

    except (TimeoutError, ConnectionError) as e:
        logger.warning(f"DSPy extraction timeout: {e}")
        raise
    except Exception as e:
        logger.error(f"DSPy extraction failed: {e}")
        raise


# Tier 2: Regex Fallback (fast, reliable)
async def extract_name_regex(state: BookingState) -> Dict[str, Any]:
    """Extract name using regex fallback."""
    from fallbacks.name_fallback import RegexNameExtractor

    extractor = RegexNameExtractor()
    result = extractor.extract(state["user_message"])

    if result:
        logger.info(f"✅ Regex extracted: {result['first_name']}")
        return {
            **result,
            "extraction_method": "regex",
            "confidence": 0.70
        }

    raise ValueError("Regex extraction failed")


# Main Node Function
async def node(state: BookingState) -> BookingState:
    """
    Extract customer name with 3-tier resilience.

    Tier 1: Try DSPy (LLM-based, best quality)
    Tier 2: Try Regex (fast, reliable)
    Tier 3: Ask user (graceful degradation)
    """

    # Tier 1: Try DSPy extraction
    try:
        name_data = await extract_name_dspy(state)

        # Update state with extracted name
        if not state.get("customer"):
            state["customer"] = {}

        state["customer"].update(name_data)
        state["current_step"] = "extract_phone"
        logger.info(f"✅ Name extracted (DSPy): {name_data['first_name']}")
        return state

    except Exception as dspy_error:
        logger.warning(f"Tier 1 (DSPy) failed: {dspy_error}")

        # Tier 2: Try regex fallback
        try:
            name_data = await extract_name_regex(state)

            if not state.get("customer"):
                state["customer"] = {}

            state["customer"].update(name_data)
            state["current_step"] = "extract_phone"
            logger.info(
                f"✅ Name extracted (Regex fallback): {name_data['first_name']}"
            )
            return state

        except Exception as regex_error:
            logger.warning(f"Tier 2 (Regex) failed: {regex_error}")

            # Tier 3: Graceful degradation - ask user
            logger.warning("⚠️ All extraction failed, asking user")
            state["response"] = "I didn't catch your name. What's your name?"
            state["current_step"] = "extract_name"  # Stay in same step
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append("name_extraction_failed")
            return state

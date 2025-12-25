"""Atomic Frappe API call node - uses YawlitClient directly.

SOLID Principles:
- Single Responsibility: ONLY integrates YawlitClient with workflow state
- Open/Closed: Extensible via FrappeOperation protocol
- Dependency Inversion: Depends on Protocol, not concrete YawlitClient methods

DRY Principle:
- Uses YawlitClient's retry logic (NO duplication)
- Uses YawlitClient's error handling (NO duplication)
- Uses YawlitClient's session management (NO duplication)
"""

import logging
from typing import Any, Callable, Dict, Optional, Protocol

from clients.frappe_yawlit import YawlitClient
from clients.frappe_yawlit.utils.exceptions import FrappeAPIError, NotFoundError
from utils.field_utils import set_nested_field
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)


class FrappeOperation(Protocol):
    """Protocol for Frappe operations (Dependency Inversion).

    Any async callable that makes Frappe API calls is a valid FrappeOperation.
    This enables:
    - YawlitClient sub-client methods (client.customer_lookup.check_customer_exists)
    - Custom wrapper functions
    - Composed operations
    """

    async def __call__(self, **kwargs) -> Dict[str, Any]:
        """Execute Frappe operation.

        Args:
            **kwargs: Operation-specific parameters

        Returns:
            API response data
        """
        ...


# Global YawlitClient instance (singleton pattern)
_yawlit_client: Optional[YawlitClient] = None


def get_yawlit_client() -> YawlitClient:
    """Get global YawlitClient instance.

    Creates client on first call, reuses thereafter.
    Reads configuration from settings.

    Returns:
        Configured YawlitClient instance
    """
    global _yawlit_client
    if _yawlit_client is None:
        _yawlit_client = YawlitClient()
        logger.info("YawlitClient singleton initialized")
    return _yawlit_client


async def node(
    state: BookingState,
    operation: FrappeOperation,
    result_path: str,
    state_extractor: Optional[Callable[[BookingState], Dict[str, Any]]] = None,
    on_failure: str = "log"
) -> BookingState:
    """Atomic Frappe API call node - works with ANY YawlitClient method.

    Single Responsibility: ONLY integrates YawlitClient with workflow state.
    Does NOT handle HTTP, retry, auth - YawlitClient does that (DRY).

    Args:
        state: Current booking state
        operation: ANY async callable implementing FrappeOperation protocol
        result_path: Where to store result in state (e.g., "customer_data")
        state_extractor: Optional function to extract operation params from state
        on_failure: Action on failure - "log", "raise", "clear"

    Returns:
        Updated state with Frappe API response

    Examples:
        # Customer lookup
        client = get_yawlit_client()
        await call_frappe.node(
            state,
            client.customer_lookup.check_customer_exists,
            "customer_data",
            state_extractor=lambda s: {"identifier": s["conversation_id"]}
        )

        # Service catalog
        await call_frappe.node(
            state,
            client.service_catalog.get_filtered_services,
            "services",
            state_extractor=lambda s: {
                "vehicle_type": s.get("vehicle", {}).get("vehicle_type")
            }
        )
    """
    # Extract operation parameters from state
    if state_extractor:
        try:
            params = state_extractor(state)
            logger.debug(f"Extracted params from state: {list(params.keys())}")
        except Exception as e:
            logger.error(f"❌ State extraction failed: {e}")
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"frappe_param_extraction_failed_{result_path}")

            if on_failure == "raise":
                raise

            return state
    else:
        params = {}

    # Call YawlitClient operation (delegates ALL HTTP logic)
    try:
        operation_name = getattr(operation, "__name__", str(operation))
        logger.info(f"📞 Calling Frappe operation: {operation_name}")

        result = await operation(**params)

        # Store result in state
        set_nested_field(state, result_path, result)

        logger.info(f"✅ Frappe operation successful: {result_path}")
        return state

    except NotFoundError as e:
        logger.warning(f"⚠️ Frappe resource not found: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"frappe_not_found_{result_path}")

        if on_failure == "raise":
            raise
        elif on_failure == "clear":
            set_nested_field(state, result_path, None)

        return state

    except FrappeAPIError as e:
        logger.error(f"❌ Frappe API error: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"frappe_api_error_{result_path}")

        if on_failure == "raise":
            raise

        return state

    except Exception as e:
        logger.error(f"❌ Unexpected error in Frappe operation: {e}")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"frappe_unexpected_error_{result_path}")

        if on_failure == "raise":
            raise

        return state

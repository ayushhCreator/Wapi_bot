# V2 Node Design: Learning from V1's Mistakes

**Document Purpose**: Design principles for WapiBot Backend V2 nodes to avoid the critical mistakes that plagued V1.

**Date**: 2025-12-24
**Author**: Learning from example/ codebase analysis
**Status**: DRAFT - Foundation for V2 Architecture

---

## Executive Summary: What Went Wrong in V1

V1 suffered from **10 critical architectural bugs** documented in BUGS_4.md, resulting in:
- ❌ 0% data extraction success rate in integration tests (despite 100% in unit tests)
- ❌ 0% booking completion rate
- ❌ Data corruption (names overwriting, vehicle brands as customer names)
- ❌ Code duplication (15% of codebase was duplicated)
- ❌ 953-line "god object" (models.py)
- ❌ Three parallel state management systems
- ❌ Data stored in 4 different locations with different field names

**Root Causes**:
1. **Orchestration bugs**, not module logic bugs (DSPy worked perfectly in isolation)
2. **No single source of truth** for state, data, or configuration
3. **Unconditional data overwrites** without confidence scoring
4. **Over-engineering** (942-line data_extractor.py with 76-line normalization functions)
5. **State-gated extraction** caused circular dependencies
6. **Vehicle names confused with customer names** ("Mahindra Scorpio" → first_name="Mahindra")

---

## Core Principle: LangGraph Node Design Philosophy

### V2 Approach: State-Managed Workflow with Isolated Nodes

```
┌─────────────────────────────────────────────────────────┐
│         BookingState (Single Source of Truth)           │
│  - conversation_id, user_message, history               │
│  - customer: {first_name, last_name, confidence, ...}   │
│  - vehicle: {brand, model, plate, confidence, ...}      │
│  - appointment: {date, time, confidence, ...}           │
│  - current_step, completeness, errors, response         │
└─────────────────────────────────────────────────────────┘
                            │
                  ┌─────────┼─────────┐
                  │         │         │
                  ▼         ▼         ▼
          ┌────────┐  ┌────────┐  ┌────────┐
          │ Node 1 │  │ Node 2 │  │ Node 3 │
          │Extract │  │Extract │  │Extract │
          │  Name  │  │ Phone  │  │Vehicle │
          └────────┘  └────────┘  └────────┘
                  │         │         │
                  └─────────┼─────────┘
                            │
                            ▼
                    Updated BookingState
```

**Key Principles**:
1. **One State Object**: BookingState is the ONLY data container
2. **Immutable Nodes**: Nodes receive state, return new state (functional)
3. **No External Storage**: No conversation_manager, scratchpad_manager, etc.
4. **Confidence-Based Updates**: Only update if new confidence > old confidence
5. **Field Name Consistency**: One naming convention across entire system

---

## Lesson 1: Single Source of Truth for Data

### V1 Problem: Data in 4 Different Places

```python
# V1 ANTI-PATTERN ❌

# Location 1: conversation_manager.py
user_data = {
    "first_name": "Divya",
    "vehicle_plate": "MH12AB1234"  # ← "vehicle_plate"
}

# Location 2: scratchpad.py
form = {
    "customer": {"name": "Divya Iyer"},  # ← "name" not "first_name"
    "vehicle": {"number_plate": "MH12AB1234"}  # ← "number_plate" not "vehicle_plate"
}

# Location 3: service_request.py
customer_name = "Divya"  # ← Flat field
vehicle_plate = "MH12AB1234"  # ← Back to "vehicle_plate"

# Result: 3 field naming conventions, impossible to sync!
```

### V2 Solution: BookingState as Single Source

```python
# V2 PATTERN ✅

from typing import TypedDict, Optional, List, Dict, Any
from typing_extensions import NotRequired

class CustomerData(TypedDict):
    """Customer information with confidence tracking."""
    first_name: NotRequired[str]
    last_name: NotRequired[str]
    phone: NotRequired[str]
    confidence: NotRequired[float]  # Track confidence for merging
    extraction_method: NotRequired[str]  # "dspy", "regex", "retroactive"
    turn_extracted: NotRequired[int]  # Which turn was this extracted


class VehicleData(TypedDict):
    """Vehicle information with confidence tracking."""
    brand: NotRequired[str]
    model: NotRequired[str]
    plate: NotRequired[str]
    confidence: NotRequired[float]
    extraction_method: NotRequired[str]
    turn_extracted: NotRequired[int]


class AppointmentData(TypedDict):
    """Appointment information with confidence tracking."""
    date: NotRequired[str]
    time: NotRequired[str]
    confidence: NotRequired[float]
    extraction_method: NotRequired[str]
    turn_extracted: NotRequired[int]


class BookingState(TypedDict):
    """
    SINGLE SOURCE OF TRUTH for entire booking conversation.

    No other class stores this data - not conversation_manager,
    not scratchpad, not service_request. Just this.
    """
    # Conversation Context
    conversation_id: str
    user_message: str
    history: List[Dict[str, str]]  # [{"role": "user/assistant", "content": "..."}]

    # Extracted Data (with confidence tracking)
    customer: NotRequired[CustomerData]
    vehicle: NotRequired[VehicleData]
    appointment: NotRequired[AppointmentData]

    # Flow Control
    current_step: str  # "extract_name", "extract_phone", "extract_vehicle", etc.
    completeness: float  # 0.0 to 1.0
    errors: List[str]  # Error messages for debugging

    # Response Generation
    response: str  # What to send back to user
    should_confirm: bool  # Trigger confirmation screen
    should_proceed: bool  # Continue workflow

    # Optional: Service Request ID (only after booking created)
    service_request_id: NotRequired[str]
    service_request: NotRequired[Dict[str, Any]]
```

**Why This Works**:
- ✅ **One place** to look for customer data
- ✅ **One naming convention** (first_name, not name)
- ✅ **Confidence tracking** prevents overwrites
- ✅ **Turn tracking** helps with retroactive validation
- ✅ **LangGraph-native** (TypedDict for state)

---

## Lesson 2: Confidence-Based Data Merging

### V1 Problem: Unconditional Overwrites

```python
# V1 ANTI-PATTERN ❌

# Turn 3: Extract "Sneha Reddy"
extracted_data["first_name"] = "Sneha"  # confidence=0.9

# Turn 10: User says "Shukriya" (thank you in Hindi)
# Extraction mistakes it for a name
extracted_data["first_name"] = "Shukriya"  # ❌ OVERWRITES with confidence=0.6!

# Turn 10: Retroactive scan finds "Sneha" in history
extracted_data["first_name"] = "Sneha"  # ❌ Too late! Already stored "Shukriya"
```

**Result**: Customer "Sneha Reddy" becomes "Shukriya" in booking confirmation.

### V2 Solution: Confidence-Based Updates

```python
# V2 PATTERN ✅

async def merge_customer_data(
    state: BookingState,
    new_data: CustomerData,
    new_confidence: float,
    source: str,  # "extraction", "retroactive", "user_correction"
    turn: int
) -> BookingState:
    """
    Merge new customer data into state ONLY if more confident than existing.

    This prevents low-confidence extractions from overwriting
    high-confidence ones (e.g., "Shukriya" overwriting "Sneha").
    """
    current_customer = state.get("customer", {})
    current_confidence = current_customer.get("confidence", 0.0)

    # Rule 1: Only update if new data is MORE confident
    if new_confidence <= current_confidence:
        logger.info(
            f"⏭️ Skipping customer update: "
            f"new confidence {new_confidence} <= "
            f"existing confidence {current_confidence}"
        )
        return state  # No change

    # Rule 2: Validate new data isn't a known false positive
    first_name = new_data.get("first_name", "")
    if is_vehicle_brand(first_name):
        logger.warning(
            f"❌ Rejecting customer data: '{first_name}' is a vehicle brand"
        )
        return state  # No change

    if first_name.lower() in GREETING_STOPWORDS:
        logger.warning(
            f"❌ Rejecting customer data: '{first_name}' is a greeting/courtesy phrase"
        )
        return state  # No change

    # Rule 3: Update with full metadata
    state["customer"] = {
        **new_data,
        "confidence": new_confidence,
        "extraction_method": source,
        "turn_extracted": turn
    }

    logger.info(
        f"✅ Updated customer data: {first_name} "
        f"(confidence: {new_confidence}, source: {source})"
    )

    return state


# Example: Turn 3 vs Turn 10
# Turn 3: Extract "Sneha"
state = merge_customer_data(
    state,
    {"first_name": "Sneha", "last_name": "Reddy"},
    new_confidence=0.9,
    source="dspy",
    turn=3
)
# Result: state["customer"]["first_name"] = "Sneha" ✅

# Turn 10: Extract "Shukriya" (low confidence)
state = merge_customer_data(
    state,
    {"first_name": "Shukriya", "last_name": ""},
    new_confidence=0.6,  # ← Lower than 0.9
    source="dspy",
    turn=10
)
# Result: state["customer"]["first_name"] = "Sneha" ✅ (no change!)
```

**Why This Works**:
- ✅ **High-confidence data protected** from low-confidence overwrites
- ✅ **Vehicle brand validation** prevents "Mahindra Scorpio" as name
- ✅ **Greeting stopwords** prevent "Shukriya", "Dhanyavaad" as names
- ✅ **Metadata tracking** for debugging (when/how was data extracted)

---

## Lesson 3: Avoid Name/Vehicle Confusion

### V1 Problem: Vehicle Brands as Customer Names

```python
# V1 ANTI-PATTERN ❌

# User says: "Mahindra Scorpio"
# State: VEHICLE_DETAILS (collecting vehicle info)

# BUG: Name extraction runs in ALL states
name_data = extract_name(user_message="Mahindra Scorpio")
# DSPy NameExtractor sees: "Mahindra" = first name, "Scorpio" = last name

extracted_data = {
    "first_name": "Mahindra",  # ❌ WRONG!
    "last_name": "Scorpio",     # ❌ WRONG!
    "vehicle_brand": "Mahindra",  # ✅ Correct
    "vehicle_model": "Scorpio"    # ✅ Correct
}

# Result: Customer "Kavita Verma" becomes "Mahindra Scorpio"
```

### V2 Solution: Vehicle Brand Validation

```python
# V2 PATTERN ✅

from enum import Enum

class VehicleBrand(str, Enum):
    """Comprehensive list of vehicle brands for validation."""
    TOYOTA = "Toyota"
    HONDA = "Honda"
    TATA = "Tata"
    MAHINDRA = "Mahindra"
    MARUTI = "Maruti Suzuki"
    HYUNDAI = "Hyundai"
    FORD = "Ford"
    # ... 80+ brands (use V1's VehicleBrandEnum)


def is_vehicle_brand(text: str) -> bool:
    """Check if text matches any known vehicle brand."""
    if not text or not text.strip():
        return False

    text_lower = text.lower().strip()

    return any(
        brand.value.lower() in text_lower or
        text_lower in brand.value.lower()
        for brand in VehicleBrand
    )


# In name extraction node:
async def extract_name_node(state: BookingState) -> BookingState:
    """Extract customer name with vehicle brand rejection."""

    # Extract using DSPy
    name_data = await extract_name_dspy(state)

    if name_data:
        first_name = name_data.get("first_name", "")
        last_name = name_data.get("last_name", "")

        # Validation 1: Reject vehicle brands
        if is_vehicle_brand(first_name) or is_vehicle_brand(last_name):
            logger.warning(
                f"❌ Rejected name extraction: "
                f"'{first_name} {last_name}' contains vehicle brand"
            )
            return state  # Don't update

        # Validation 2: Reject greeting stopwords
        if first_name.lower() in GREETING_STOPWORDS:
            logger.warning(
                f"❌ Rejected name extraction: "
                f"'{first_name}' is a greeting/courtesy phrase"
            )
            return state  # Don't update

        # If validations pass, merge with confidence check
        return merge_customer_data(
            state,
            {"first_name": first_name, "last_name": last_name},
            new_confidence=name_data["confidence"],
            source="dspy",
            turn=len(state.get("history", []))
        )

    return state  # No extraction


# Constants (from V1's config.py)
GREETING_STOPWORDS = [
    "haan", "hello", "hi", "hey", "shukriya", "dhanyavaad",
    "thanks", "thank you", "namaste", "yes", "okay", "ok"
]
```

**Why This Works**:
- ✅ **Vehicle brands rejected** before storing
- ✅ **Greeting stopwords rejected** (prevents "Shukriya" as name)
- ✅ **Reuses V1's VehicleBrandEnum** (80+ brands already defined)
- ✅ **Single utility function** (not duplicated like V1)

---

## Lesson 4: Retroactive Scanning Without Overwrites

### V1 Problem: Retroactive Scan Amplifies Mistakes

```python
# V1 ANTI-PATTERN ❌

# Turn 6: Retroactive scan finds "Mahindra Scorpio" in history (Turn 5)
retroactive_data = scan_for_name(history)
# Extracts: first_name="Mahindra", last_name="Scorpio"

# Unconditionally merges into state
extracted_data.update(retroactive_data)  # ❌ Overwrites correct "Kavita"

# Logs: "⚡ RETROACTIVE IMPROVEMENTS: ['first_name', 'last_name']"
# Actually made it WORSE!
```

### V2 Solution: Retroactive with Validation + Confidence

```python
# V2 PATTERN ✅

async def retroactive_scan_node(state: BookingState) -> BookingState:
    """
    Scan conversation history to fill MISSING fields ONLY.

    Rules:
    1. Only scan if field is missing (don't overwrite)
    2. Apply same validations as direct extraction
    3. Lower confidence than direct extraction (0.7 instead of 0.9)
    4. Limit to last 5 messages (not entire history)
    """
    current_customer = state.get("customer", {})
    history = state.get("history", [])

    # Rule 1: Only scan if first_name is missing
    if current_customer.get("first_name"):
        logger.info("⏭️ Skipping retroactive scan: customer name already exists")
        return state  # Don't scan

    # Rule 2: Limit scan to last 5 messages (prevent scanning too far back)
    recent_messages = history[-5:] if len(history) > 5 else history

    # Rule 3: Scan only user messages (not assistant responses)
    user_messages = [
        msg for msg in recent_messages
        if msg.get("role") == "user"
    ]

    if not user_messages:
        return state

    # Rule 4: Extract from combined recent messages
    combined_text = " ".join([msg.get("content", "") for msg in user_messages])

    # Use DSPy to extract (will work with conversation context)
    from dspy_modules.extractors.name_extractor import NameExtractor
    extractor = NameExtractor()

    try:
        result = extractor(
            conversation_history=history,
            user_message=combined_text,
            context="Retroactive scan of recent conversation"
        )

        first_name = result.get("first_name", "").strip()
        last_name = result.get("last_name", "").strip()

        if first_name:
            # Validate before merging (same as direct extraction)
            if is_vehicle_brand(first_name) or is_vehicle_brand(last_name):
                logger.warning(
                    f"❌ Retroactive scan rejected: "
                    f"'{first_name}' is a vehicle brand"
                )
                return state

            if first_name.lower() in GREETING_STOPWORDS:
                logger.warning(
                    f"❌ Retroactive scan rejected: "
                    f"'{first_name}' is a greeting phrase"
                )
                return state

            # Merge with LOWER confidence (retroactive is less reliable)
            return merge_customer_data(
                state,
                {"first_name": first_name, "last_name": last_name},
                new_confidence=0.7,  # ← Lower than direct extraction (0.9)
                source="retroactive",
                turn=len(history)
            )

    except Exception as e:
        logger.error(f"Retroactive scan failed: {e}")

    return state  # No update on failure
```

**Why This Works**:
- ✅ **Only fills missing fields** (doesn't overwrite existing)
- ✅ **Same validations** as direct extraction
- ✅ **Lower confidence** (0.7 vs 0.9) so won't overwrite high-confidence data
- ✅ **Limited scope** (last 5 messages, not entire history)
- ✅ **User messages only** (doesn't extract from bot responses)

---

## Lesson 5: 3-Tier Resilience Pattern (Keep from V1)

### V1 Success: Multi-Tier Fallback

This was one of the things V1 did RIGHT. Keep this pattern.

```python
# V2 PATTERN ✅ (Keep from V1)

async def extract_name_node(state: BookingState) -> BookingState:
    """
    Extract customer name with 3-tier resilience.

    Tier 1: DSPy LLM extraction (best quality)
    Tier 2: Regex fallback (fast, reliable)
    Tier 3: Ask user (graceful degradation)
    """

    # Tier 1: Try DSPy (LLM-based, best quality)
    try:
        name_data = await extract_name_dspy(state)

        if name_data and name_data.get("confidence", 0) >= 0.7:
            # Validate before returning
            first_name = name_data.get("first_name", "")

            if not is_vehicle_brand(first_name) and \
               first_name.lower() not in GREETING_STOPWORDS:

                state = merge_customer_data(
                    state,
                    name_data,
                    new_confidence=name_data["confidence"],
                    source="dspy",
                    turn=len(state.get("history", []))
                )

                logger.info(f"✅ Name extracted (DSPy): {first_name}")
                state["current_step"] = "extract_phone"  # Progress to next step
                return state

    except Exception as e:
        logger.warning(f"Tier 1 (DSPy) failed: {e}")

    # Tier 2: Try regex fallback
    try:
        name_data = await extract_name_regex(state)

        if name_data:
            state = merge_customer_data(
                state,
                name_data,
                new_confidence=0.7,  # Regex = medium confidence
                source="regex",
                turn=len(state.get("history", []))
            )

            logger.info(f"✅ Name extracted (Regex): {name_data['first_name']}")
            state["current_step"] = "extract_phone"
            return state

    except Exception as e:
        logger.warning(f"Tier 2 (Regex) failed: {e}")

    # Tier 3: Graceful degradation - ask user
    logger.warning("⚠️ All extraction tiers failed, asking user")
    state["response"] = "I didn't catch your name. What's your name?"
    state["current_step"] = "extract_name"  # Stay in same step

    if "errors" not in state:
        state["errors"] = []
    state["errors"].append("name_extraction_failed")

    return state
```

**Why This Works**:
- ✅ **Best quality first** (DSPy LLM)
- ✅ **Fast fallback** (regex)
- ✅ **Graceful degradation** (ask user, don't crash)
- ✅ **Confidence tracking** (DSPy=0.9, regex=0.7)
- ✅ **No silent failures** (always returns valid state)

---

## Lesson 6: Avoid Duplicate Code (DRY Principle)

### V1 Problem: Duplicate Functions

```python
# V1 ANTI-PATTERN ❌

# extraction_coordinator.py:31-57
class ExtractionCoordinator:
    def _is_vehicle_brand(self, text: str) -> bool:
        # 26 lines of code

# retroactive_validator.py:73-95
class RetroactiveScanner:
    def _is_vehicle_brand(self, text: str) -> bool:
        # EXACT SAME 26 lines of code (copy-pasted!)
```

**Result**: Bug fixed in one file, forgotten in the other.

### V2 Solution: Shared Utilities

```python
# V2 PATTERN ✅

# utils/validation.py (NEW FILE)
"""Shared validation utilities used across nodes."""

from enum import Enum
from typing import Set

class VehicleBrand(str, Enum):
    """Vehicle brands for validation (single source of truth)."""
    TOYOTA = "Toyota"
    HONDA = "Honda"
    TATA = "Tata"
    MAHINDRA = "Mahindra"
    # ... all 80+ brands


GREETING_STOPWORDS: Set[str] = {
    "haan", "hello", "hi", "hey", "shukriya", "dhanyavaad",
    "thanks", "thank you", "namaste", "yes", "okay", "ok"
}


def is_vehicle_brand(text: str) -> bool:
    """
    Check if text matches any known vehicle brand.

    Used by:
    - extract_name_node.py
    - retroactive_scan_node.py
    - Any other validation logic

    Returns:
        True if text is a vehicle brand, False otherwise
    """
    if not text or not text.strip():
        return False

    text_lower = text.lower().strip()

    return any(
        brand.value.lower() in text_lower or
        text_lower in brand.value.lower()
        for brand in VehicleBrand
    )


def is_greeting_stopword(text: str) -> bool:
    """Check if text is a greeting or courtesy phrase."""
    return text.lower().strip() in GREETING_STOPWORDS


# Now ALL nodes import from ONE place:
# nodes/extraction/extract_name.py
from utils.validation import is_vehicle_brand, is_greeting_stopword

# nodes/retroactive/scan_history.py
from utils.validation import is_vehicle_brand, is_greeting_stopword
```

**Why This Works**:
- ✅ **One implementation** (fix in one place)
- ✅ **Clear ownership** (utils/validation.py owns validation logic)
- ✅ **Easy testing** (test utilities in isolation)
- ✅ **No drift** (impossible for implementations to diverge)

---

## Lesson 7: Node Design Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Nodes with External Storage

```python
# V1 ANTI-PATTERN ❌

async def extract_name_node(state: BookingState) -> BookingState:
    # DON'T DO THIS!
    conversation_manager.store_user_data(conversation_id, "first_name", "Riju")
    scratchpad_manager.add_customer_info(first_name="Riju")
    service_request_builder.set_customer_name("Riju")

    # Now data is in 3 places with 3 different field names!
    return state
```

**Problem**: Data is scattered, impossible to sync, field names differ.

**V2 Solution**: Only update state, nothing else.

```python
# V2 PATTERN ✅

async def extract_name_node(state: BookingState) -> BookingState:
    # ONLY update state
    name_data = await extract_name_dspy(state)

    state = merge_customer_data(
        state,
        name_data,
        new_confidence=name_data["confidence"],
        source="dspy",
        turn=len(state.get("history", []))
    )

    # No external storage! State is ONLY place data lives.
    return state
```

### ❌ Anti-Pattern 2: Nodes with Side Effects

```python
# V1 ANTI-PATTERN ❌

async def extract_name_node(state: BookingState) -> BookingState:
    # DON'T DO THIS!
    send_email_notification("Name extracted")
    log_to_analytics_service("name_extraction_success")
    update_dashboard_metrics()

    return state
```

**Problem**: Side effects make nodes untestable, non-deterministic.

**V2 Solution**: Nodes are pure functions (state in, state out).

```python
# V2 PATTERN ✅

async def extract_name_node(state: BookingState) -> BookingState:
    # Pure function - no side effects
    name_data = await extract_name_dspy(state)
    state = merge_customer_data(state, name_data, ...)

    # Side effects happen in SEPARATE observability layer
    return state


# Observability happens in LangGraph hooks (not in nodes)
def on_node_end(node_name: str, state: BookingState):
    """Called by LangGraph after each node completes."""
    if node_name == "extract_name":
        log_to_analytics("name_extraction_success", state)
```

### ❌ Anti-Pattern 3: State-Gated Extraction

```python
# V1 ANTI-PATTERN ❌

async def extract_data_node(state: BookingState) -> BookingState:
    # DON'T DO THIS!
    if state["current_step"] == "extract_name":
        name_data = await extract_name_dspy(state)
    elif state["current_step"] == "extract_vehicle":
        vehicle_data = await extract_vehicle_dspy(state)
    # ... lots of if/elif chains

    return state
```

**Problem**: Creates circular dependencies, one giant node doing everything.

**V2 Solution**: Separate nodes for each extraction, LangGraph routing.

```python
# V2 PATTERN ✅

# nodes/extraction/extract_name.py
async def node(state: BookingState) -> BookingState:
    """Extract name ONLY. No state checking."""
    name_data = await extract_name_dspy(state)
    return merge_customer_data(state, name_data, ...)


# nodes/extraction/extract_vehicle.py
async def node(state: BookingState) -> BookingState:
    """Extract vehicle ONLY. No state checking."""
    vehicle_data = await extract_vehicle_dspy(state)
    return merge_vehicle_data(state, vehicle_data, ...)


# workflows/simple_chat.py
workflow = StateGraph(BookingState)

workflow.add_node("extract_name", extract_name_node)
workflow.add_node("extract_vehicle", extract_vehicle_node)

# Routing based on current_step (not inside nodes!)
workflow.add_conditional_edges(
    "extract_name",
    lambda state: state["current_step"],
    {
        "extract_phone": "extract_phone",
        "extract_name": "extract_name"  # Stay if failed
    }
)
```

---

## Lesson 8: Configuration Management

### V1 Problem: Hardcoded Values Everywhere

```python
# V1 ANTI-PATTERN ❌

# models.py
def needs_engagement(self) -> bool:
    return self.interest >= 7.0  # ❌ Hardcoded!

# template_manager.py
sentiment_threshold_interested = 7.0  # ❌ Different value!

# state_coordinator.py
if sentiment.anger > 6.0:  # ❌ Hardcoded!
    return ConversationState.SERVICE_SELECTION
```

**Result**: Same threshold in 3 places with 2 different values (7.0 vs 6.0).

### V2 Solution: Single Configuration Source

```python
# V2 PATTERN ✅

# .env.txt (SINGLE SOURCE OF TRUTH)
SENTIMENT_THRESHOLD_INTEREST=7.0
SENTIMENT_THRESHOLD_ANGER=6.0
SENTIMENT_THRESHOLD_DISGUST=8.0
CONFIDENCE_LOW=0.5
CONFIDENCE_MEDIUM=0.7
CONFIDENCE_HIGH=0.9

# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Sentiment Thresholds
    sentiment_threshold_interest: float = 7.0
    sentiment_threshold_anger: float = 6.0
    sentiment_threshold_disgust: float = 8.0

    # Confidence Thresholds
    confidence_low: float = 0.5
    confidence_medium: float = 0.7
    confidence_high: float = 0.9

    model_config = SettingsConfigDict(
        env_file=".env.txt",
        env_file_encoding="utf-8"
    )

settings = Settings()


# ALL nodes import from config (no hardcoded values!)
# nodes/extraction/extract_name.py
from core.config import settings

async def merge_customer_data(state, new_data, new_confidence, ...):
    if new_confidence <= settings.confidence_medium:
        logger.warning("Low confidence, rejecting")
        return state
```

**Why This Works**:
- ✅ **One place** to change thresholds (.env.txt)
- ✅ **Type-safe** (Pydantic validates)
- ✅ **Documented** (in .env.txt with comments)
- ✅ **No magic numbers** anywhere in code

---

## Node Design Checklist

Use this checklist when designing ANY node in V2:

### ✅ Data Management
- [ ] Node only reads/writes to `BookingState` (no external storage)
- [ ] All field names match `BookingState` TypedDict exactly
- [ ] Confidence scores tracked for all extracted data
- [ ] Metadata tracked (extraction_method, turn_extracted)
- [ ] Merge functions use confidence-based updates

### ✅ Validation
- [ ] Vehicle brand validation applied to name extraction
- [ ] Greeting stopwords checked before storing names
- [ ] Confidence thresholds prevent low-quality overwrites
- [ ] Edge cases handled (empty strings, None, "Unknown")

### ✅ Code Quality
- [ ] No duplicate code (use shared utils)
- [ ] No hardcoded values (use settings from config)
- [ ] No external side effects (pure function)
- [ ] Errors handled gracefully (return state with error message)
- [ ] Logging at appropriate levels (INFO for success, WARNING for rejection)

### ✅ Testing
- [ ] Node tested in isolation (mocked DSPy modules)
- [ ] Integration tested with real LLM
- [ ] Edge cases tested (vehicle names, greetings, etc.)
- [ ] Confidence merging tested (high conf protects from low conf)

### ✅ Documentation
- [ ] Docstring explains node purpose clearly
- [ ] Parameters documented (state input/output)
- [ ] Edge cases documented (what gets rejected)
- [ ] Examples provided (success and failure cases)

---

## Recommended V2 File Structure (Atomic Nodes)

```
backend/src/
├── core/
│   ├── config.py          # Settings (from .env.txt)
│   └── warmup.py          # LLM warmup service
│
├── workflows/
│   ├── booking_onetime.py        # One-time booking workflow
│   ├── booking_subscription.py   # Subscription booking workflow
│   └── shared/
│       ├── state.py              # BookingState TypedDict (SINGLE SOURCE)
│       └── routes.py             # Conditional routing functions
│
├── nodes/
│   ├── atomic/                   # ~10 ATOMIC nodes (reusable!)
│   │   ├── extract.py            # Extract using ANY DSPy module
│   │   ├── validate.py           # Validate using ANY Pydantic model
│   │   ├── scan.py               # Scan ANY source (history/DB/API)
│   │   ├── confidence_gate.py    # Gate using ANY comparison function
│   │   ├── merge.py              # Merge using ANY strategy
│   │   ├── transform.py          # Transform using ANY function
│   │   ├── condition.py          # Route using ANY predicate
│   │   ├── response.py           # Generate using ANY template/LLM
│   │   ├── log.py                # Log using ANY format
│   │   └── checkpoint.py         # Save state at ANY point
│   │
│   └── groups/                   # User-created node groups
│       ├── name_extraction.py    # Composes: extract + validate + scan
│       ├── phone_extraction.py   # Composes: extract + validate + format
│       ├── vehicle_extraction.py # Composes: extract + validate + enrich
│       └── booking_confirm.py    # Composes: validate + response
│
├── utils/
│   ├── validation.py      # Shared validation (is_vehicle_brand, etc.)
│   ├── confidence.py      # Confidence-based merging
│   ├── history_utils.py   # History conversion utilities
│   └── nested_fields.py   # get_nested_field, set_nested_field helpers
│
├── dspy_modules/
│   └── extractors/
│       ├── name_extractor.py       # DSPy NameExtractor
│       ├── phone_extractor.py      # DSPy PhoneExtractor
│       └── vehicle_extractor.py    # DSPy VehicleDetailsExtractor
│
├── fallbacks/
│   ├── name_fallback.py   # Regex name extraction fallback
│   ├── phone_fallback.py  # Regex phone fallback
│   └── vehicle_fallback.py # Regex vehicle fallback
│
└── sources/              # Scannable data sources
    ├── history_source.py  # HistorySource (scan conversation history)
    ├── database_source.py # DatabaseSource (scan DB)
    └── api_source.py      # APISource (scan external APIs)
```

**Key Principles**:
- ✅ **10 atomic nodes** replace 100+ domain-specific nodes
- ✅ **Configuration over specialization** (not extract_name.py, just extract.py + config)
- ✅ **Node groups** for user-created compositions (like Blender)
- ✅ **No duplication** (ONE extract implementation for ALL fields)
- ✅ **Clear ownership** (utils/ owns validation, atomic/ owns primitives)
- ✅ **One state definition** (workflows/shared/state.py)
- ✅ **No circular deps** (utils don't import from nodes)

---

## Summary: Top 10 Lessons from V1

1. **Atomic Nodes Over Domain Nodes**: 10 configurable nodes replace 100+ specialized nodes

2. **Single Source of Truth**: BookingState is ONLY place data lives (no conversation_manager, scratchpad, etc.)

3. **Confidence-Based Updates**: Only overwrite if new confidence > old confidence

4. **Vehicle Brand Validation**: Reject "Mahindra", "Toyota", etc. from name extraction

5. **Greeting Stopword Validation**: Reject "Shukriya", "Thanks", etc. from name extraction

6. **No Duplicate Code**: Share utilities (is_vehicle_brand in ONE file, not two)

7. **No Magic Numbers**: All thresholds in .env.txt + core/config.py

8. **Pure Functions**: Nodes are (state) → (state), no side effects

9. **Node Groups for Composition**: Users create workflows by composing atomic nodes

10. **3-Tier Resilience**: DSPy → Fallback → Ask User (built into atomic extract node)

---

## Next Steps

1. Read this document before designing ANY node
2. Use `BookingState` TypedDict from workflows/shared/state.py
3. Implement `merge_customer_data()`, `merge_vehicle_data()` utilities
4. Create `utils/validation.py` with shared functions
5. Design each extraction node following the 3-tier pattern
6. Test confidence-based merging with edge cases
7. Validate against this checklist for each node

**Remember**: V1 failed because of orchestration bugs, not DSPy bugs. Get the architecture right first, then implementation becomes straightforward.

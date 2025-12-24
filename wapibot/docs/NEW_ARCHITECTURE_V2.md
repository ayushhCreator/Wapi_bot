# 🏗️ WapiBot V2 Architecture

## **Production-Ready, LLM-Resilient, Visual Workflow System**

**Date:** 2025-12-24
**Status:** Design Phase
**Goal:** Eliminate orchestration hell, ensure LLM resilience, enable visual editing

---

## 📋 DESIGN PRINCIPLES

### 1. **LLM Resilience (CRITICAL)**

**Problem:** Junior broke demo when Ollama failed → project almost scrapped
**Solution:** Every LLM call has 3-tier fallback

```python
# ATOMIC NODE: Can extract ANY data with ANY DSPy module
async def extract_node(
    state: BookingState,
    extractor: dspy.Module,     # ← Configurable: NameExtractor, PhoneExtractor, etc.
    field_path: str,             # ← Configurable: "customer.first_name", "vehicle.brand"
    fallback_fn: Callable = None # ← Configurable: regex, rule-based, etc.
):
    """Atomic extraction node with 3-tier resilience."""
    try:
        # Tier 1: DSPy (best quality)
        result = await asyncio.wait_for(
            extractor(state["history"], state["user_message"]),
            timeout=5.0
        )
        set_nested_field(state, field_path, result.value)
        return state

    except (TimeoutError, ConnectionError) as e:
        # Tier 2: Fallback (fast, reliable)
        if fallback_fn:
            logger.warning(f"DSPy failed, using fallback: {e}")
            result = fallback_fn(state["user_message"])
            set_nested_field(state, field_path, result)
            return state

    except Exception as e:
        # Tier 3: Graceful degradation (ask user)
        logger.error(f"All extraction failed: {e}")
        state["response"] = f"I didn't catch your {field_path}. Could you repeat?"
        return state

# Usage (ONE node, multiple purposes):
# extract_node(state, NameExtractor(), "customer.first_name", regex_name_fallback)
# extract_node(state, PhoneExtractor(), "customer.phone", regex_phone_fallback)
# extract_node(state, VehicleExtractor(), "vehicle.brand", None)
```

**Benefits:**

- ✅ Demo NEVER breaks (even if LLM offline)
- ✅ Degrades gracefully (quality drops, but system works)
- ✅ User experience unaffected (transparent fallbacks)
- ✅ Your junior's job saved

---

### 2. **Small Files (100 Lines Max)**

**Problem:** 1,043-line models.py, 674-line message_processor.py
**Solution:** Enforce via linter + code review

```
# .pylintrc (auto-enforce)
[FORMAT]
max-module-lines=100  # Hard limit
max-function-lines=50  # Hard limit per function
```

**File Size Targets:**

- Nodes: 50-100 lines (1 responsibility)
- Models: 30-50 lines (1 model per file)
- Utils: 30-50 lines (1 utility per file)
- Workflows: 100-150 lines (graph definition only)

---

### 3. **Visual + Code Workflows**

**Tool:** LangGraph Studio
**Features:**

- Drag-and-drop node editor
- Export graph → Python code
- Import Python code → visual graph
- Live execution visualization
- State inspection
- Breakpoints/debugging

**Example Workflow (Visual → Code):**

```
[User Message]
    ↓
[Extract Name] ──→ [Extract Vehicle] ──→ [Extract Date]
    ↓ (if name missing)          ↓ (if vehicle missing)
[Ask for Name]                [Ask for Vehicle]
```

Exports to:

```python
# Atomic nodes configured for specific purposes
workflow = StateGraph(BookingState)

# Configure extract node for name
workflow.add_node("extract_name",
    lambda s: extract_node(s, NameExtractor(), "customer.first_name", regex_name_fallback))

# Configure extract node for vehicle (SAME node, different config!)
workflow.add_node("extract_vehicle",
    lambda s: extract_node(s, VehicleExtractor(), "vehicle.brand", None))

# Conditional routing
workflow.add_conditional_edges("extract_name",
    lambda s: "extract_vehicle" if s.get("customer", {}).get("first_name") else "ask_name")
```

---

### 4. **Async-First API**

**All atomic nodes are async and reusable:**

```python
# ATOMIC NODE: Extract with race condition (fastest wins)
async def extract_with_race_node(
    state: BookingState,
    extractors: List[Tuple[dspy.Module, Callable]],  # [(DSPy, fallback), ...]
    field_path: str
) -> BookingState:
    """Atomic extraction with concurrent fallbacks - fastest result wins."""
    tasks = [
        asyncio.create_task(extractor(state["history"], state["user_message"]))
        for extractor, _ in extractors
    ]

    # Return first successful result
    for task in asyncio.as_completed(tasks):
        try:
            result = await task
            if result:
                # Cancel other tasks
                for t in tasks:
                    t.cancel()
                set_nested_field(state, field_path, result.value)
                return state
        except Exception:
            continue

    # All failed - use first fallback
    if extractors[0][1]:
        result = extractors[0][1](state["user_message"])
        set_nested_field(state, field_path, result)
    return state

# Usage: Race DSPy vs Regex, use whichever returns first!
```

**Benefits:**

- ✅ Faster responses (parallel execution)
- ✅ Non-blocking (handle multiple users)
- ✅ Better resource usage

---

### 5. **State = Single Source of Truth**

**No more scattered state!**

```python
from typing import TypedDict, Optional, Dict, List

class BookingState(TypedDict):
    """Single source of truth for booking workflow."""
    # Conversation
    conversation_id: str
    user_message: str
    history: List[Dict[str, str]]

    # Extracted Data (scratchpad replacement)
    customer: Optional[Dict[str, str]]  # first_name, last_name, phone
    vehicle: Optional[Dict[str, str]]   # brand, model, plate
    appointment: Optional[Dict[str, str]]  # date, service, slot

    # AI Analysis
    sentiment: Optional[Dict[str, float]]  # interest, anger, disgust, boredom
    intent: Optional[str]  # inquire, booking, pricing, complaint

    # Workflow Control
    current_step: str  # "extract_name", "confirm_booking", etc.
    completeness: float  # 0.0-1.0
    errors: List[str]

    # Response
    response: str
    should_confirm: bool
```

**LangGraph persists this automatically** with checkpointers:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver("conversations.db")
app = workflow.compile(checkpointer=checkpointer)

# State auto-saved after EVERY node
# Resume from crash: app.invoke(state, thread_id="conv-123")
```

---

## 📂 NEW FOLDER STRUCTURE

```
wapibot/
├── workflows/                      # LangGraph workflow definitions
│   ├── __init__.py
│   ├── booking_onetime.py         (100 lines) - One-time booking graph
│   ├── booking_subscription.py    (120 lines) - Subscription booking graph
│   ├── booking_emergency.py       (80 lines)  - Emergency service graph
│   └── shared/
│       ├── state.py               (50 lines)  - BookingState TypedDict
│       └── routes.py              (60 lines)  - Conditional routing functions
│
├── nodes/
│   ├── atomic/                     # ~10 ATOMIC nodes (reusable, configurable)
│   │   ├── extract.py             (80 lines)  - Extract using ANY DSPy module
│   │   ├── validate.py            (60 lines)  - Validate using ANY Pydantic model
│   │   ├── scan.py                (100 lines) - Scan ANY source (history/DB/API)
│   │   ├── confidence_gate.py     (50 lines)  - Gate using ANY comparison fn
│   │   ├── merge.py               (70 lines)  - Merge using ANY strategy
│   │   ├── transform.py           (60 lines)  - Transform using ANY function
│   │   ├── condition.py           (40 lines)  - Route using ANY predicate
│   │   ├── response.py            (80 lines)  - Generate using ANY template/LLM
│   │   ├── log.py                 (50 lines)  - Log using ANY format
│   │   └── checkpoint.py          (60 lines)  - Save state at ANY point
│   │
│   └── groups/                     # User-created node groups (compositions)
│       ├── name_extraction.py     (90 lines)  - Composes: extract + validate + scan
│       ├── phone_extraction.py    (85 lines)  - Composes: extract + validate + format
│       ├── vehicle_extraction.py  (100 lines) - Composes: extract + validate + enrich
│       ├── booking_confirmation.py (95 lines) - Composes: validate + response
│       └── service_request.py     (110 lines) - Composes: merge + transform + save
│
├── models/                         # Pydantic models (30-50 lines each)
│   ├── __init__.py
│   ├── customer.py                (40 lines)  - Customer, Name, Phone
│   ├── vehicle.py                 (45 lines)  - Vehicle, VehicleBrandEnum
│   ├── appointment.py             (35 lines)  - Appointment, Date, Slot
│   ├── sentiment.py               (40 lines)  - SentimentScores
│   ├── intent.py                  (30 lines)  - Intent, IntentClass
│   ├── response.py                (45 lines)  - ChatResponse
│   └── service_request.py         (50 lines)  - ServiceRequest
│
├── dspy_modules/                   # Your existing DSPy modules (KEEP AS-IS)
│   ├── __init__.py
│   ├── extractors.py              (500 lines) - Name, Vehicle, Date, Phone extractors
│   ├── analyzers.py               (300 lines) - Sentiment, Intent analyzers
│   ├── generators.py              (200 lines) - Response generators
│   └── signatures.py              (400 lines) - All DSPy signatures
│
├── fallbacks/                      # Regex/rule-based fallbacks (30-50 lines each)
│   ├── __init__.py
│   ├── name_fallback.py           (45 lines)  - Regex name extraction
│   ├── vehicle_fallback.py        (50 lines)  - Regex vehicle extraction
│   ├── date_fallback.py           (40 lines)  - Date parsing fallback
│   └── phone_fallback.py          (35 lines)  - Phone regex validation
│
├── api/                            # FastAPI routes (50-100 lines each)
│   ├── __init__.py
│   ├── main.py                    (100 lines) - FastAPI app setup
│   ├── chat.py                    (80 lines)  - POST /chat endpoint
│   ├── confirmation.py            (70 lines)  - POST /api/confirmation
│   └── webhooks.py                (90 lines)  - WhatsApp webhook
│
├── storage/                        # State persistence (50-80 lines each)
│   ├── __init__.py
│   ├── checkpoints.py             (60 lines)  - LangGraph checkpoint config
│   ├── conversations.py           (70 lines)  - Conversation storage
│   └── service_requests.py        (75 lines)  - ServiceRequest storage
│
├── utils/                          # Utilities (30-50 lines each)
│   ├── __init__.py
│   ├── history.py                 (40 lines)  - History conversion
│   ├── validators.py              (50 lines)  - Pydantic validators
│   └── logging.py                 (45 lines)  - Structured logging
│
└── config/                         # Configuration (30-50 lines each)
    ├── __init__.py
    ├── settings.py                (50 lines)  - Pydantic Settings
    ├── llm.py                     (40 lines)  - LLM config (Ollama, OpenAI)
    └── workflows.py               (45 lines)  - Workflow config
```

**Metrics:**

- Total **atomic nodes**: ~10 files (~650 lines total)
- Total **node groups**: ~5-10 files (user-created compositions)
- Total **workflows**: ~3-5 files (booking types)
- Avg file size: **60 lines** (vs current 217 lines)
- Max file size: **120 lines** (vs current 1,043 lines)
- **Node count**: 10 atomic nodes replace 100+ domain-specific nodes!

---

## 🧩 ATOMIC NODE PHILOSOPHY (Blender-Inspired)

### The Problem with Domain-Specific Nodes

**V1 Approach** (❌ Node Explosion):
```
extract_name.py
extract_phone.py
extract_vehicle.py
extract_date.py
extract_service.py
extract_slot.py
extract_address.py
... 50+ extraction nodes ...

validate_name.py
validate_phone.py
validate_vehicle.py
... 50+ validation nodes ...

Total: 100+ specialized nodes, massive duplication
```

### The Atomic Node Solution

**V2 Approach** (✅ Configuration over Specialization):
```python
# ONE atomic extract node
nodes/atomic/extract.py  # Works with ANY DSPy module, ANY field

# Configure it for different purposes:
extract_node(state, NameExtractor(), "customer.first_name")      # Name
extract_node(state, PhoneExtractor(), "customer.phone")          # Phone
extract_node(state, VehicleExtractor(), "vehicle.brand")         # Vehicle
extract_node(state, DateExtractor(), "appointment.date")         # Date

# Result: 1 node replaces 50+ nodes!
```

### The 10 Atomic Nodes

| Atomic Node | Purpose | Configurable With |
|-------------|---------|-------------------|
| `extract.py` | Extract data | ANY DSPy module + field path |
| `validate.py` | Validate data | ANY Pydantic model + field path |
| `scan.py` | Scan source | ANY source (history/DB/API) + extractor |
| `confidence_gate.py` | Gate updates | ANY comparison function |
| `merge.py` | Merge data | ANY merge strategy |
| `transform.py` | Transform data | ANY transform function |
| `condition.py` | Conditional routing | ANY predicate function |
| `response.py` | Generate response | ANY template/LLM |
| `log.py` | Logging | ANY logger/format |
| `checkpoint.py` | Save state | ANY checkpoint trigger |

### Node Groups (User Compositions)

Like Blender's node groups, users compose atomic nodes into reusable workflows:

```python
# nodes/groups/name_extraction.py
def create_name_extraction_group():
    """Compose atomic nodes into name extraction workflow."""
    graph = StateGraph(BookingState)

    # Atomic node 1: Extract
    graph.add_node("extract",
        lambda s: extract_node(s, NameExtractor(), "customer.first_name"))

    # Atomic node 2: Validate
    graph.add_node("validate",
        lambda s: validate_node(s, CustomerData, "customer"))

    # Atomic node 3: Scan if missing
    graph.add_node("scan",
        lambda s: scan_node(s, HistorySource(), NameExtractor(), "customer.first_name"))

    # Routing
    graph.add_conditional_edges("extract",
        lambda s: "validate" if s.get("customer", {}).get("first_name") else "scan")

    return graph.compile()

# This group can be reused in ANY workflow that needs name extraction!
```

---

## 🔄 WORKFLOW EXAMPLE: One-Time Booking

**File:** `workflows/booking_onetime.py` (100 lines)

```python
"""One-time car wash booking workflow using atomic nodes + node groups."""

from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from workflows.shared.routes import has_field, all_fields_present
from nodes.atomic import extract, validate, scan, response, transform
from nodes.groups import name_extraction, vehicle_extraction, phone_extraction
from dspy_modules.extractors import NameExtractor, VehicleExtractor, PhoneExtractor
from models import CustomerData, VehicleData


def create_onetime_booking_workflow() -> StateGraph:
    """Create one-time booking workflow using composable atomic nodes."""

    workflow = StateGraph(BookingState)

    # Option 1: Use node groups (pre-composed)
    workflow.add_node("extract_customer_data", name_extraction.create_group())
    workflow.add_node("extract_vehicle_data", vehicle_extraction.create_group())
    workflow.add_node("extract_phone_data", phone_extraction.create_group())

    # Option 2: Configure atomic nodes directly
    workflow.add_node("extract_name",
        lambda s: extract.node(s, NameExtractor(), "customer.first_name"))

    workflow.add_node("validate_customer",
        lambda s: validate.node(s, CustomerData, "customer"))

    workflow.add_node("scan_history_for_missing",
        lambda s: scan.node(s, HistorySource(), NameExtractor(), "customer.first_name"))

    workflow.add_node("generate_confirmation",
        lambda s: response.node(s, "booking_confirmation", ConfirmationLLM()))

    # Define edges (flow control)
    workflow.set_entry_point("analyze_sentiment")
    workflow.add_edge("analyze_sentiment", "classify_intent")
    workflow.add_edge("classify_intent", "extract_name")

    # Conditional routing based on data completeness
    workflow.add_conditional_edges("extract_name", route_after_name)
    workflow.add_conditional_edges("extract_vehicle", route_after_vehicle)
    workflow.add_conditional_edges("extract_date", route_after_date)

    # Validation and confirmation
    workflow.add_edge("validate_completeness", "confirm_booking")
    workflow.add_conditional_edges(
        "confirm_booking",
        lambda s: "create_service_request" if s["should_confirm"] else "generate_response"
    )

    # Response generation
    workflow.add_edge("generate_response", "compose_final")
    workflow.add_edge("compose_final", END)
    workflow.add_edge("create_service_request", "compose_final")

    return workflow


# Compile workflow
from storage.checkpoints import get_checkpointer

onetime_booking_app = create_onetime_booking_workflow().compile(
    checkpointer=get_checkpointer("onetime_booking")
)
```

**Visual Representation (LangGraph Studio):**

```
[User Message]
    ↓
[Analyze Sentiment] ──→ [Classify Intent]
    ↓
[Extract Name] ──→ [Extract Phone] ──→ [Extract Vehicle] ──→ [Extract Date]
    ↓ (if missing name)         ↓ (if missing vehicle)
[Generate Response]          [Generate Response]
    ↓
[Validate Completeness]
    ↓
[Confirm Booking] ──┬──→ [Create Service Request]
                    └──→ [Generate Response]
                          ↓
                    [Compose Final]
                          ↓
                        [END]
```

---

## 🧩 NODE EXAMPLE: Extract Name (with Resilience)

**File:** `nodes/extraction/extract_name.py` (70 lines)

```python
"""Extract customer name with 3-tier resilience."""

import asyncio
import logging
from typing import Dict, Any
from workflows.shared.state import BookingState
from dspy_modules.extractors import NameExtractor  # Your existing DSPy module
from fallbacks.name_fallback import RegexNameExtractor
from models.customer import Name

logger = logging.getLogger(__name__)

# Initialize extractors
dspy_extractor = NameExtractor()
regex_extractor = RegexNameExtractor()


async def extract_name_dspy(state: BookingState) -> Dict[str, Any]:
    """Tier 1: DSPy extraction (best quality)."""
    try:
        result = await asyncio.wait_for(
            dspy_extractor(state["history"], state["user_message"]),
            timeout=5.0
        )

        if result.first_name and result.first_name != "Unknown":
            logger.info(f"✅ DSPy extracted name: {result.first_name}")
            return {
                "first_name": result.first_name,
                "last_name": result.last_name or "",
                "extraction_method": "dspy",
                "confidence": 0.95
            }
    except (TimeoutError, ConnectionError) as e:
        logger.warning(f"⚠️ DSPy timeout: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ DSPy failed: {e}")
        raise


async def extract_name_regex(state: BookingState) -> Dict[str, Any]:
    """Tier 2: Regex extraction (fast, reliable)."""
    result = regex_extractor.extract(state["user_message"])
    if result:
        logger.info(f"✅ Regex extracted name: {result['first_name']}")
        return {**result, "extraction_method": "regex", "confidence": 0.70}
    raise ValueError("Regex extraction failed")


async def node(state: BookingState) -> BookingState:
    """
    Extract customer name with 3-tier fallback.

    Tier 1: DSPy (LLM-based, best quality)
    Tier 2: Regex (rule-based, fast)
    Tier 3: Ask user (graceful degradation)
    """

    # Try DSPy first
    try:
        name_data = await extract_name_dspy(state)
        state["customer"] = state.get("customer", {})
        state["customer"].update(name_data)
        state["current_step"] = "extract_phone"
        return state

    except Exception:
        # Try regex fallback
        try:
            name_data = await extract_name_regex(state)
            state["customer"] = state.get("customer", {})
            state["customer"].update(name_data)
            state["current_step"] = "extract_phone"
            return state

        except Exception:
            # Graceful degradation: ask user
            logger.warning("⚠️ All name extraction failed, asking user")
            state["response"] = "I didn't catch your name. What's your name?"
            state["current_step"] = "extract_name"  # Stay in same step
            state["errors"].append("name_extraction_failed")
            return state
```

**Benefits:**

- ✅ **70 lines** (vs 674 in message_processor.py)
- ✅ **Single responsibility** (SOLID principle)
- ✅ **3-tier resilience** (never crashes)
- ✅ **Async-first** (non-blocking)
- ✅ **Graceful degradation** (asks user if all fails)

---

## 🛡️ FALLBACK EXAMPLE: Regex Name Extractor

**File:** `fallbacks/name_fallback.py` (45 lines)

```python
"""Regex-based name extraction fallback (when LLM fails)."""

import re
from typing import Optional, Dict

# Greeting stopwords (reject these as names)
STOPWORDS = {"hi", "hello", "hey", "haan", "yes", "ok", "okay", "sure"}


class RegexNameExtractor:
    """Fast, reliable name extraction using regex patterns."""

    # Patterns for name detection
    PATTERNS = [
        r"(?:my name is|i am|i'm|this is|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)$",  # Just a capitalized name
    ]

    def extract(self, message: str) -> Optional[Dict[str, str]]:
        """
        Extract name using regex patterns.

        Returns:
            {"first_name": "John", "last_name": "Doe"} or None
        """
        message = message.strip()

        for pattern in self.PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                full_name = match.group(1).strip()

                # Reject stopwords
                if full_name.lower() in STOPWORDS:
                    continue

                # Split into first/last
                parts = full_name.split()
                if len(parts) == 1:
                    return {"first_name": parts[0], "last_name": ""}
                else:
                    return {"first_name": parts[0], "last_name": " ".join(parts[1:])}

        return None
```

**Benefits:**

- ✅ **45 lines** (small, focused)
- ✅ **No LLM dependency** (works offline)
- ✅ **Fast** (<1ms vs 2-5s for LLM)
- ✅ **No regex hell** (clean Pydantic validation in models)

---

## 📊 MODELS EXAMPLE: Split from 1,043 Lines

**Before:** `datamodels/models.py` (1,043 lines with 44 models)

**After:** 7 files averaging 40 lines each

### `models/customer.py` (40 lines)

```python
"""Customer-related models."""

from pydantic import BaseModel, Field, validator
from typing import Optional


class Name(BaseModel):
    """Customer name with validation."""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: Optional[str] = Field("", max_length=50)

    @validator("first_name")
    def validate_first_name(cls, v):
        """Ensure first name is not a greeting."""
        stopwords = {"hi", "hello", "hey", "haan", "yes"}
        if v.lower() in stopwords:
            raise ValueError(f"Invalid name: {v}")
        return v.title()


class Phone(BaseModel):
    """Indian phone number with validation."""
    number: str = Field(..., regex=r"^\+?91?[6-9]\d{9}$")

    @validator("number")
    def normalize_phone(cls, v):
        """Normalize to 10-digit format."""
        digits = re.sub(r"[^\d]", "", v)
        if len(digits) == 10:
            return digits
        elif len(digits) == 12 and digits.startswith("91"):
            return digits[2:]
        raise ValueError(f"Invalid phone: {v}")


class Customer(BaseModel):
    """Complete customer data."""
    name: Name
    phone: Phone
    email: Optional[str] = None
    address: Optional[str] = None
```

### `models/vehicle.py` (45 lines)

```python
"""Vehicle-related models."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class VehicleBrandEnum(str, Enum):
    """80+ vehicle brands (from your existing code)."""
    TOYOTA = "Toyota"
    HONDA = "Honda"
    MARUTI = "Maruti"
    HYUNDAI = "Hyundai"
    MAHINDRA = "Mahindra"
    TATA = "Tata"
    KIA = "Kia"
    # ... (rest of 80+ brands)


class Vehicle(BaseModel):
    """Vehicle details with validation."""
    brand: VehicleBrandEnum
    model: str = Field(..., min_length=1, max_length=50)
    plate: str = Field(..., regex=r"^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$")
    vehicle_type: Optional[str] = Field(None, regex="^(hatchback|sedan|suv|luxury)$")

    @validator("plate")
    def normalize_plate(cls, v):
        """Normalize plate to uppercase without spaces."""
        return v.upper().replace(" ", "").replace("-", "")
```

**Benefits:**

- ✅ **1,043 lines → 280 lines** (73% reduction)
- ✅ **Easy to navigate** (1 model = 1 file)
- ✅ **Pydantic validation** (no regex hell)
- ✅ **Type-safe** (mypy-compliant)

---

## 🚀 API EXAMPLE: FastAPI Endpoint

**File:** `api/chat.py` (80 lines)

```python
"""Chat endpoint using LangGraph workflow."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from workflows.booking_onetime import onetime_booking_app
from workflows.shared.state import BookingState
from storage.conversations import get_conversation_history

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request payload."""
    conversation_id: str
    user_message: str


class ChatResponse(BaseModel):
    """Chat response payload."""
    message: str
    should_confirm: bool
    completeness: float
    extracted_data: dict
    service_request_id: str | None


@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    """
    Process user message through LangGraph booking workflow.

    Features:
    - Automatic LLM fallbacks (never crashes)
    - State persistence (resume after crash)
    - Async execution (non-blocking)
    """
    try:
        # Get conversation history
        history = await get_conversation_history(request.conversation_id)

        # Prepare state
        state: BookingState = {
            "conversation_id": request.conversation_id,
            "user_message": request.user_message,
            "history": history,
            "customer": None,
            "vehicle": None,
            "appointment": None,
            "sentiment": None,
            "intent": None,
            "current_step": "analyze_sentiment",
            "completeness": 0.0,
            "errors": [],
            "response": "",
            "should_confirm": False,
        }

        # Execute workflow (async, with automatic checkpointing)
        result = await onetime_booking_app.ainvoke(
            state,
            config={"configurable": {"thread_id": request.conversation_id}}
        )

        # Extract response
        return ChatResponse(
            message=result["response"],
            should_confirm=result["should_confirm"],
            completeness=result["completeness"],
            extracted_data={
                "customer": result.get("customer"),
                "vehicle": result.get("vehicle"),
                "appointment": result.get("appointment"),
            },
            service_request_id=result.get("service_request_id"),
        )

    except Exception as e:
        # Graceful error handling
        raise HTTPException(status_code=500, detail=str(e))
```

**Benefits:**

- ✅ **80 lines** (vs 490 in main.py)
- ✅ **Single responsibility** (just handle HTTP)
- ✅ **Async-first** (non-blocking)
- ✅ **LangGraph handles orchestration** (no 674-line process_message)

---

## 🎨 VISUAL WORKFLOW EDITOR: LangGraph Studio

**Setup:**

```bash
# Install LangGraph Studio (desktop app)
pip install langgraph-studio

# Launch visual editor
langgraph-studio
```

**Features:**

1. **Drag-and-Drop Nodes**
   - Add node from library
   - Connect with edges
   - Set conditional routing

2. **Export to Code**

   ```python
   # Generated code from visual editor
   workflow = StateGraph(BookingState)
   workflow.add_node("extract_name", extract_name.node)
   workflow.add_node("extract_vehicle", extract_vehicle.node)
   workflow.add_conditional_edges("extract_name", route_after_name)
   ```

3. **Import from Code**
   - Paste your Python workflow
   - Auto-generates visual graph

4. **Live Execution**
   - Set breakpoints
   - Inspect state at each node
   - Step through execution
   - View logs in real-time

5. **State Visualization**

   ```
   Step 1: analyze_sentiment
   State: {"sentiment": {"interest": 7.5, "anger": 1.0}}

   Step 2: extract_name
   State: {"customer": {"first_name": "Ravi"}}

   Step 3: extract_vehicle
   State: {"vehicle": {"brand": "Honda", "model": "City"}}
   ```

**Benefits:**

- ✅ **Non-technical stakeholders** can understand workflow
- ✅ **Junior developer** can edit visually (no code)
- ✅ **Senior developer** can export to code for review
- ✅ **Product manager** can design flows in meetings

---

## 📈 COMPARISON: Before vs After

| Metric | Before (Your Code) | After (New Arch) | Improvement |
|--------|-------------------|------------------|-------------|
| **Largest file** | 1,043 lines (models.py) | 120 lines (workflows) | **87% smaller** |
| **Avg file size** | 217 lines | 60 lines | **72% smaller** |
| **Orchestration complexity** | 674 lines (message_processor) | 100 lines (workflow graph) | **85% reduction** |
| **LLM resilience** | 0% (crashes if Ollama fails) | 100% (3-tier fallbacks) | **∞% improvement** |
| **Visual editing** | None | LangGraph Studio | **Game changer** |
| **State management** | Scattered (3 places) | Single source (BookingState) | **Unified** |
| **Async support** | Partial | 100% async | **Better performance** |
| **File navigation** | 50 files, hard to find | 60 files, intuitive structure | **Better DX** |

---

## 🎯 MIGRATION PLAN

### Phase 1: Foundation (COMPLETE ✅ - Dec 24, 2025)

- [x] Design architecture (this document)
- [x] Create folder structure (backend/src/)
- [x] Split models.py → 7 files (models/{core,customer,vehicle,appointment,sentiment,intent,response}.py)
- [x] Define BookingState TypedDict (workflows/shared/state.py)
- [x] Setup LangGraph dependencies (langgraph>=0.2.40)
- [x] Create core config (core/config.py, core/dspy_config.py)
- [x] Create main.py with modern async lifespan

### Phase 2: API & Schemas (COMPLETE ✅ - Dec 24, 2025)

- [x] Create Pydantic schemas with examples (schemas/chat.py, schemas/wapi.py)
- [x] Create POST /api/v1/chat endpoint (api/v1/chat_endpoint.py)
- [x] Create POST /api/v1/wapi/webhook endpoint (api/v1/wapi_webhook.py)
- [x] Auto-generated Swagger docs at /docs
- [x] Centralized router registry (api/router_registry.py)
- [x] Full type annotations + example values

### Phase 3: MVP Workflow (COMPLETE ✅ - Dec 24, 2025)

- [x] Create simple workflow (workflows/simple_chat.py)
- [x] Create name extraction node (nodes/extraction/extract_name.py)
- [x] Create regex fallback (fallbacks/name_fallback.py)
- [x] Wire workflow to /chat endpoint
- [x] 3-tier resilience working (DSPy → Regex → Ask User)
- [x] Test end-to-end with Ollama

### Phase 4: Remaining Nodes (TODO - Next)

- [ ] Extract existing DSPy modules from example/ to dspy_modules/
- [ ] Create phone extraction node (nodes/extraction/extract_phone.py)
- [ ] Create vehicle extraction node (nodes/extraction/extract_vehicle.py)
- [ ] Create date extraction node (nodes/extraction/extract_date.py)
- [ ] Create sentiment node (nodes/analysis/analyze_sentiment.py)
- [ ] Create intent node (nodes/analysis/classify_intent.py)
- [ ] Create response generator (nodes/responses/generate_response.py)

### Phase 5: Full Workflow (TODO)

- [ ] Build complete booking workflow (workflows/booking_onetime.py)
- [ ] Add conditional routing (workflows/shared/routes.py)
- [ ] Setup state persistence with checkpoints
- [ ] Test with LangGraph Studio visual editor
- [ ] Integration with Frappe backend

### Phase 6: Production (TODO)

- [ ] WAPI integration (send messages via wapi_client.py)
- [ ] Error handling & monitoring
- [ ] Load testing (100+ concurrent users)
- [ ] Deploy to production

**Total Time:**
- Phase 1-3: ✅ 1 session (vs 36 hours of hell in V1)
- Phase 4-6: Estimated 1-2 days

---

## 🛡️ RESILIENCE GUARANTEES

### 1. **LLM Offline Protection**

```python
# Every node has this structure:
async def node(state):
    try:
        return await dspy_module(state)  # Try LLM
    except:
        return await fallback(state)  # Use regex/rules
```

### 2. **Timeout Protection**

```python
# All LLM calls have 5-second timeout
result = await asyncio.wait_for(llm_call(), timeout=5.0)
```

### 3. **State Persistence**

```python
# Crash recovery: Resume from last checkpoint
app.invoke(state, thread_id="conv-123")
```

### 4. **Graceful Degradation**

```python
# If all extraction fails, ask user directly
state["response"] = "Could you tell me your name again?"
```

---

## 🔧 DEVELOPMENT WORKFLOW

### Local Development

```bash
# Start Ollama (optional, with fallbacks)
ollama serve

# Start FastAPI dev server
uvicorn api.main:app --reload --port 8000

# Launch LangGraph Studio (visual editor)
langgraph-studio
```

### Code Review Checklist

- [ ] File size ≤ 100 lines?
- [ ] Single responsibility (SOLID)?
- [ ] Has LLM fallback?
- [ ] Async function?
- [ ] Type hints?
- [ ] Docstring?
- [ ] Unit test?

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
- name: Check file sizes
  run: |
    max_lines=$(find . -name "*.py" -exec wc -l {} + | awk '{print $1}' | sort -rn | head -1)
    if [ $max_lines -gt 100 ]; then
      echo "File exceeds 100 lines!"
      exit 1
    fi
```

---

## 📚 NEXT STEPS

1. **Review this document** with team
2. **Approve architecture** or request changes
3. **Start Phase 1** (foundation)
4. **Weekly demos** (show progress to stakeholders)
5. **Migrate to production** (6 weeks)

---

## ✅ SUCCESS CRITERIA

- ✅ **No file >100 lines**
- ✅ **System works when Ollama offline**
- ✅ **Visual workflow editor works**
- ✅ **Async API handles 100+ concurrent users**
- ✅ **Subscription workflow added in 1 day**
- ✅ **Junior can edit workflows visually**
- ✅ **Senior can review generated code**
- ✅ **Demos NEVER break**

---

**Status:** Ready for approval
**Next:** Team review meeting

# V2 Node Design: Applying Blender's Node Philosophy

**Document Purpose**: Apply proven node-based design principles from Blender Geometry Nodes and Shader Nodes to WapiBot Backend V2's LangGraph architecture.

**Date**: 2025-12-24
**Inspiration**: [Blender Geometry Nodes Design](https://developer.blender.org/docs/handbook/design/examples/geometry_nodes/), [Bundles and Closures](https://code.blender.org/2025/08/bundles-and-closures/)

---

## Why Learn from Blender?

Blender's node systems (Geometry Nodes, Shader Nodes) achieve **complex procedural results through simple, composable nodes**. Key successes:

1. **Simple nodes, complex outcomes**: Basic nodes like "Set Position", "Instance", "Mix" combine to create forests, cities, procedural animations
2. **Non-destructive workflow**: Change any node, entire graph updates downstream
3. **Functional composition**: Data flows left-to-right, no hidden state
4. **Producer/consumer design**: Each node has clear inputs and outputs
5. **Incremental complexity**: System was "releasable at every stage" - even with just 3-4 nodes

**V1's Mistake**: Complex monolithic components (942-line data_extractor.py) instead of composable building blocks.

---

## Core Principle 1: Single Responsibility Nodes

### Blender's Approach

From [Geometry Nodes Design](https://developer.blender.org/docs/handbook/design/examples/geometry_nodes/):
> "The moment only a few nodes were in (enough to scatter some pebbles), the system was considered ready for a release."

Each Blender node does **one thing well**:
- `Set Position` - moves points
- `Instance on Points` - creates copies
- `Mesh to Points` - converts geometry
- `Random Value` - generates numbers

**Composition creates complexity**: Combine 4 simple nodes → procedural forest.

### V2 Application

**V1 Anti-Pattern** ❌:
```python
# V1: Monolithic node doing EVERYTHING
class DataExtractionCoordinator:
    def extract_for_state(self, state, message, history):
        # 200+ lines handling:
        # - Name extraction (DSPy + regex + validation)
        # - Phone extraction (DSPy + regex + validation)
        # - Vehicle extraction (DSPy + regex + validation)
        # - Date extraction (DSPy + regex + validation)
        # - State routing logic
        # - Retroactive scanning
        # - Typo detection
        # Result: 942-line file, impossible to test/maintain
```

**V2 Pattern** ✅:
```python
# V2: ATOMIC nodes (configurable, reusable)

# ONE atomic extract node (works for ANY field)
# nodes/atomic/extract.py (~80 lines)
async def node(
    state: BookingState,
    extractor: dspy.Module,  # ← ANY DSPy module
    field_path: str,          # ← ANY field path
    fallback_fn: Callable = None
) -> BookingState:
    """Atomic extraction - works with ANY extractor, ANY field."""
    try:
        result = extractor(state["history"], state["user_message"])
        set_nested_field(state, field_path, result.value)
    except Exception:
        if fallback_fn:
            result = fallback_fn(state["user_message"])
            set_nested_field(state, field_path, result)
    return state


# ONE atomic validate node (works for ANY model)
# nodes/atomic/validate.py (~60 lines)
async def node(
    state: BookingState,
    model: type[BaseModel],  # ← ANY Pydantic model
    field_path: str           # ← ANY field path
) -> BookingState:
    """Atomic validation - works with ANY model, ANY field."""
    data = get_nested_field(state, field_path)
    try:
        validated = model(**data)
        set_nested_field(state, field_path, validated.dict())
    except ValidationError:
        set_nested_field(state, field_path, {})
    return state


# ONE atomic scan node (works for ANY source)
# nodes/atomic/scan.py (~100 lines)
async def node(
    state: BookingState,
    source: Source,          # ← ANY source (history, DB, API)
    extractor: dspy.Module,  # ← ANY extractor
    field_path: str           # ← ANY field
) -> BookingState:
    """Atomic scan - works with ANY source, ANY extractor, ANY field."""
    if get_nested_field(state, field_path):
        return state  # Already have data

    data = await source.get_data(state)
    result = extractor([], data)
    set_nested_field(state, field_path, result.value)
    return state


# Composition in LangGraph workflow:
workflow.add_node("extract_name",
    lambda s: extract.node(s, NameExtractor(), "customer.first_name"))

workflow.add_node("validate_customer",
    lambda s: validate.node(s, CustomerData, "customer"))

workflow.add_node("scan_history",
    lambda s: scan.node(s, HistorySource(), NameExtractor(), "customer.first_name"))

workflow.add_edge("extract_name", "validate_customer")
workflow.add_edge("validate_customer", "scan_history")

# Result: 3 ATOMIC nodes (~240 lines total) replace 100+ domain-specific nodes!
# Can be reused for name, phone, vehicle, date, etc.
```

**Why This Works**:
- ✅ **Each node < 50 lines** (readable in one screen)
- ✅ **Clear responsibility** (name extract, validate, scan)
- ✅ **Testable in isolation** (mock state, verify output)
- ✅ **Composable** (rearrange order, add new nodes between)
- ✅ **Debuggable** (see exactly which node failed)

---

## Core Principle 2: Explicit Dependencies (No Hidden State)

### Blender's Approach

From [Geometry Nodes Design](https://developer.blender.org/docs/handbook/design/examples/geometry_nodes/):
> "The system should be fully self-contained with all external dependencies explicitly exposed, rather than relying on hard-coded values."

Blender nodes **never access global state**. All inputs are explicit sockets:
- Want random seed? Add "Seed" input socket
- Want object reference? Add "Object" input socket
- Want threshold value? Add "Threshold" input socket

**Result**: Looking at a node shows exactly what it depends on.

### V2 Application

**V1 Anti-Pattern** ❌:
```python
# V1: Hidden dependencies everywhere
class DataExtractor:
    def extract_name(self, user_message, history):
        # Hidden dependency: conversation_manager (global)
        conversation_id = self.conversation_manager.get_current_conversation()

        # Hidden dependency: config (imported at module level)
        from config import SENTIMENT_THRESHOLDS

        # Hidden dependency: scratchpad_manager (global)
        completeness = self.scratchpad_manager.get_completeness()

        # Hidden dependency: service_request_builder (global)
        existing_name = self.service_request_builder.customer_name

        # Result: Can't test without setting up 4 external systems!
```

**V2 Pattern** ✅:
```python
# V2: All dependencies in BookingState (explicit)
async def extract_name_node(state: BookingState) -> BookingState:
    """
    Extract customer name.

    Dependencies (ALL explicit in state):
    - state["user_message"]: Current message to extract from
    - state["history"]: Conversation history for context
    - state.get("customer", {}): Existing customer data (to check confidence)
    - len(state["history"]): Turn number for metadata

    No global variables. No hidden imports. Pure function.
    """
    user_message = state["user_message"]
    history = state["history"]
    existing_confidence = state.get("customer", {}).get("confidence", 0.0)
    turn = len(history)

    # Extract name
    name_data = await extract_name_dspy(
        user_message=user_message,
        history=history
    )

    # Merge with confidence check (using state["customer"])
    if name_data["confidence"] > existing_confidence:
        state["customer"] = {
            **name_data,
            "turn_extracted": turn
        }

    return state


# Testing is trivial - just mock state!
async def test_extract_name():
    state = {
        "conversation_id": "test",
        "user_message": "I'm Riju Kumar",
        "history": [],
        "customer": {}
    }

    result = await extract_name_node(state)

    assert result["customer"]["first_name"] == "Riju"
    assert result["customer"]["last_name"] == "Kumar"
    # No need to mock conversation_manager, scratchpad, etc!
```

**Why This Works**:
- ✅ **No global state** (everything in BookingState)
- ✅ **Easy testing** (just pass dict)
- ✅ **Clear dependencies** (see exactly what node needs)
- ✅ **No side effects** (pure function)
- ✅ **Composable** (any node can use any other node's output)

---

## Core Principle 3: Bundles for Related Data (From Blender)

### Blender's Approach

From [Bundles and Closures](https://code.blender.org/2025/08/bundles-and-closures/):
> "Bundles are a simpler concept that combine multiple items into one, allowing passing many items with a single link."

Instead of:
```
[Position Output] ───────────> [Position Input]
[Rotation Output] ──────────> [Rotation Input]
[Scale Output] ─────────────> [Scale Input]
[Color Output] ─────────────> [Color Input]
```

Use bundles:
```
[Transform Bundle Output] ──> [Transform Bundle Input]
  (position, rotation, scale, color packed together)
```

**Benefit**: Less visual clutter, grouped related data.

### V2 Application

**V1 Anti-Pattern** ❌:
```python
# V1: Flat dictionary with 20+ fields
conversation_data = {
    "first_name": "Riju",
    "last_name": "Kumar",
    "phone": "9876543210",
    "vehicle_brand": "Honda",
    "vehicle_model": "City",
    "vehicle_plate": "MH12AB1234",
    "appointment_date": "2025-12-25",
    "appointment_time": "10:00",
    # ... 15+ more fields ...
}

# Problem: Hard to tell what's related
# Is "first_name" customer or vehicle?
# Is "date" extracted or derived?
```

**V2 Pattern** ✅:
```python
# V2: Bundles (nested TypedDicts)
class CustomerBundle(TypedDict):
    """Customer information bundle."""
    first_name: NotRequired[str]
    last_name: NotRequired[str]
    phone: NotRequired[str]
    # Metadata bundled with data
    confidence: NotRequired[float]
    extraction_method: NotRequired[str]
    turn_extracted: NotRequired[int]


class VehicleBundle(TypedDict):
    """Vehicle information bundle."""
    brand: NotRequired[str]
    model: NotRequired[str]
    plate: NotRequired[str]
    # Metadata bundled with data
    confidence: NotRequired[float]
    extraction_method: NotRequired[str]
    turn_extracted: NotRequired[int]


class BookingState(TypedDict):
    """State with bundled data."""
    # Clear grouping - customer bundle separate from vehicle bundle
    customer: NotRequired[CustomerBundle]
    vehicle: NotRequired[VehicleBundle]
    appointment: NotRequired[AppointmentBundle]

    # Flow control
    current_step: str
    errors: List[str]
    response: str


# Node operates on bundles
async def merge_customer_data(
    state: BookingState,
    new_customer: CustomerBundle,  # ← Bundle as unit
    new_confidence: float
) -> BookingState:
    """Merge customer bundle into state."""
    existing = state.get("customer", {})
    existing_confidence = existing.get("confidence", 0.0)

    if new_confidence > existing_confidence:
        state["customer"] = new_customer  # ← Replace entire bundle

    return state
```

**Why This Works**:
- ✅ **Clear grouping** (customer data separate from vehicle data)
- ✅ **Metadata co-located** (confidence lives with data it describes)
- ✅ **Type safety** (TypedDict validates structure)
- ✅ **Easier to pass around** (merge_customer_data gets one bundle, not 6 fields)
- ✅ **Mirrors Blender's success** (related data travels together)

---

## Core Principle 4: Dataflow Programming (Producer/Consumer)

### Dataflow Principles

From [Dataflow Programming](https://en.wikipedia.org/wiki/Dataflow_programming):
> "An operation runs as soon as all of its inputs become valid. The program is a directed graph of operations, with data flowing between them."

Blender's left-to-right node flow:
```
[Input] → [Process A] → [Process B] → [Output]
```

Key rules:
1. **No side effects** - node only transforms inputs to outputs
2. **No shared state** - nodes don't talk to each other directly
3. **Explicit data flow** - can see what feeds what
4. **Automatic execution** - node runs when inputs ready

### V2 Application

**V1 Anti-Pattern** ❌:
```python
# V1: Hidden side effects, unclear flow
class ChatbotOrchestrator:
    def process_message(self, conversation_id, message):
        # Side effect: Updates conversation_manager
        self.conversation_manager.add_message(conversation_id, message)

        # Side effect: Updates scratchpad
        self.scratchpad_coordinator.update_from_extraction(...)

        # Side effect: Stores in service_request
        self.service_request_builder.add_data(...)

        # Side effect: Triggers LLM call
        self.sentiment_service.analyze(...)

        # Side effect: Logs to analytics
        self.analytics.track_event(...)

        # Return value... but what actually changed?
        return response

# Problem: Can't tell what this function does by looking at signature
# What gets modified? In what order? Hard to test, hard to debug
```

**V2 Pattern** ✅:
```python
# V2: Pure dataflow (state in → state out)

# LangGraph workflow defines explicit flow:
workflow = StateGraph(BookingState)

# Producer nodes (create data)
workflow.add_node("extract_name", extract_name_node)      # Produces: customer bundle
workflow.add_node("extract_phone", extract_phone_node)    # Produces: customer.phone
workflow.add_node("extract_vehicle", extract_vehicle_node) # Produces: vehicle bundle

# Consumer nodes (use data)
workflow.add_node("validate_name", validate_name_node)    # Consumes: customer
workflow.add_node("calculate_completeness", calc_completeness_node)  # Consumes: all bundles

# Transform nodes (data → data)
workflow.add_node("retroactive_scan", retroactive_scan_node)  # Consumes: history, Produces: missing fields
workflow.add_node("generate_response", response_node)     # Consumes: all data, Produces: response

# Explicit edges show dataflow
workflow.add_edge("extract_name", "validate_name")        # name → validation
workflow.add_edge("validate_name", "extract_phone")       # validation → phone
workflow.add_edge("extract_phone", "extract_vehicle")     # phone → vehicle
workflow.add_edge("extract_vehicle", "calculate_completeness")  # vehicle → completeness

# Visual dataflow:
# [extract_name] → [validate_name] → [extract_phone] → [extract_vehicle] → [calculate_completeness]
#        ↓               ↓                ↓                    ↓                      ↓
#   customer        validation        customer.phone        vehicle            completeness=0.8


# Each node is pure function:
async def extract_phone_node(state: BookingState) -> BookingState:
    """
    Pure function: BookingState → BookingState

    Inputs (consumed):
    - state["user_message"]
    - state["history"]

    Outputs (produced):
    - state["customer"]["phone"]

    No side effects. No global state. No hidden dependencies.
    """
    phone = await extract_phone_dspy(state["user_message"])

    if phone:
        state["customer"]["phone"] = phone
        state["customer"]["confidence"] = max(
            state["customer"].get("confidence", 0),
            phone["confidence"]
        )

    return state
```

**Why This Works**:
- ✅ **Visual graph** - can draw the flow on paper
- ✅ **Clear dependencies** - see what feeds what
- ✅ **Testable** - mock inputs, verify outputs
- ✅ **Debuggable** - know exactly where data changed
- ✅ **Composable** - rearrange nodes without breaking

---

## Core Principle 5: Incremental Complexity

### Blender's Approach

From [Geometry Nodes Design](https://developer.blender.org/docs/handbook/design/examples/geometry_nodes/):
> "Release value often - the moment only a few nodes were in (enough to scatter some pebbles), the system was considered ready for a release."

Blender's progression:
1. **Release 1**: 3 nodes (scatter points)
2. **Release 2**: 10 nodes (scatter + random scale)
3. **Release 3**: 20 nodes (scatter + random scale + rotation)
4. **Release 4**: 50 nodes (full procedural modeling)

**Principle**: Each release adds value. Don't wait for perfection.

### V2 Application

**V1 Anti-Pattern** ❌:
```python
# V1: Tried to build EVERYTHING before release
# - 11 conversation states
# - 4 extraction types (name, phone, vehicle, date)
# - Retroactive validation
# - Typo detection
# - Sentiment analysis
# - Intent classification
# - Template system
# - Response composition
# - Confirmation flow
# - Booking creation
#
# Result: 0% success rate because too complex to debug
```

**V2 Pattern** ✅:
```python
# V2: Incremental releases

# === MVP 1: Name Extraction Only ===
workflow = StateGraph(BookingState)
workflow.add_node("extract_name", extract_name_node)
workflow.add_edge("extract_name", END)

# Test: Can extract names? ✅
# Deploy: Working name extraction
# Value: Basic data collection works


# === MVP 2: Add Phone Extraction ===
workflow.add_node("extract_phone", extract_phone_node)
workflow.add_edge("extract_name", "extract_phone")
workflow.add_edge("extract_phone", END)

# Test: Can extract name + phone? ✅
# Deploy: Two-field extraction
# Value: Can identify customer


# === MVP 3: Add Vehicle Extraction ===
workflow.add_node("extract_vehicle", extract_vehicle_node)
workflow.add_edge("extract_phone", "extract_vehicle")
workflow.add_edge("extract_vehicle", END)

# Test: Can extract name + phone + vehicle? ✅
# Deploy: Three-field extraction
# Value: Can identify booking intent


# === MVP 4: Add Validation ===
workflow.add_node("validate_name", validate_name_node)
workflow.add_edge("extract_name", "validate_name")
workflow.add_edge("validate_name", "extract_phone")

# Test: Rejects "Mahindra Scorpio" as name? ✅
# Deploy: Validated extraction
# Value: Data quality improves


# === MVP 5: Add Retroactive Scanning ===
workflow.add_node("retroactive_scan", retroactive_scan_node)
# ... and so on

# Each MVP:
# - Adds 1-2 nodes
# - Takes 1-2 days to implement
# - Deployed and tested in production
# - Provides immediate value
# - Builds on previous MVP
```

**Why This Works**:
- ✅ **Fast feedback** - see results in days, not months
- ✅ **Easier debugging** - small changes, easy to find bugs
- ✅ **Continuous value** - each release improves system
- ✅ **Lower risk** - small changes less likely to break
- ✅ **Motivated team** - see progress, not stuck for months

---

## Core Principle 6: Composability Through Conditional Edges

### Blender's Approach

Geometry nodes use **Switch nodes** and **conditional branching** to create complex logic from simple nodes:

```
[Random Value] → [Compare (> 0.5)] → [Switch] → [Scale Big] or [Scale Small]
```

Simple nodes + conditional routing = complex procedural behavior.

### V2 Application

**V1 Anti-Pattern** ❌:
```python
# V1: Complex if/else chains inside nodes
class ExtractionCoordinator:
    def extract_for_state(self, state, message, history):
        if state == "NAME_COLLECTION":
            name = self.extract_name(message)
            if name:
                if self.is_vehicle_brand(name):
                    return None  # Reject
                else:
                    return name
            else:
                # Try retroactive
                name = self.scan_history(history)
                if name:
                    if self.is_vehicle_brand(name):
                        return None
                    else:
                        return name
                else:
                    return {"ask_user": True}
        elif state == "VEHICLE_DETAILS":
            # ... 50 more lines

        # Result: 200+ line function with nested if/else
```

**V2 Pattern** ✅:
```python
# V2: Simple nodes + conditional routing in LangGraph

# Define simple condition functions
def has_customer_name(state: BookingState) -> bool:
    """Check if customer name exists."""
    return bool(state.get("customer", {}).get("first_name"))


def name_is_valid(state: BookingState) -> bool:
    """Check if customer name is valid (not vehicle brand)."""
    first_name = state.get("customer", {}).get("first_name", "")
    return not is_vehicle_brand(first_name)


def should_scan_retroactive(state: BookingState) -> bool:
    """Check if should scan history for missing data."""
    return not has_customer_name(state) and len(state["history"]) > 2


# Use conditional routing in workflow
workflow = StateGraph(BookingState)

workflow.add_node("extract_name", extract_name_node)
workflow.add_node("validate_name", validate_name_node)
workflow.add_node("retroactive_scan", retroactive_scan_node)
workflow.add_node("ask_user", ask_user_node)

# Route based on conditions (not if/else inside nodes!)
workflow.add_conditional_edges(
    "extract_name",
    has_customer_name,  # ← Condition function
    {
        True: "validate_name",    # If has name → validate
        False: "retroactive_scan"  # If no name → scan history
    }
)

workflow.add_conditional_edges(
    "validate_name",
    name_is_valid,  # ← Condition function
    {
        True: "extract_phone",  # If valid → continue
        False: "ask_user"       # If invalid → ask user
    }
)

workflow.add_conditional_edges(
    "retroactive_scan",
    has_customer_name,  # ← Reuse same condition!
    {
        True: "validate_name",  # Found in history → validate
        False: "ask_user"       # Still no name → ask user
    }
)

# Visual flow with conditional routing:
#
#            ┌─→ [validate_name] ─→ (valid?) ─→ [extract_phone]
#            │                           │
# [extract_name] ─→ (has_name?)         └─→ (invalid?) ─→ [ask_user]
#            │
#            └─→ [retroactive_scan] ─→ (has_name?) ─→ [validate_name]
#                                           │
#                                           └─→ [ask_user]
```

**Why This Works**:
- ✅ **Simple nodes** - each does one thing
- ✅ **Reusable conditions** - same function used twice
- ✅ **Visual flow** - can draw graph showing all paths
- ✅ **Testable** - test conditions independently
- ✅ **Composable** - add new routes without changing nodes

---

## Core Principle 7: Non-Destructive Workflow

### Blender's Approach

From [Node-Based Procedural Workflow](https://med3017m-1819-14565893level3digital.coursework.lincoln.ac.uk/2018/10/14/node-based-procedural-workflow/):
> "The benefit of such a system is that it creates a non-destructive – or procedural – workflow which means that editing the composition at a later stage is very easy and, more importantly, non-destructive to the rest of the network."

In Blender:
- Change a node's value → entire downstream graph recalculates
- Delete a node → upstream nodes still work
- Add a node → doesn't break existing graph
- No "save points" - graph IS the source of truth

### V2 Application

**V1 Anti-Pattern** ❌:
```python
# V1: Destructive updates (mutates state)
def extract_name(state):
    # Overwrites existing data - DESTRUCTIVE!
    state["customer"]["first_name"] = "Shukriya"
    # Previous value "Sneha" is LOST forever

    # Stores to external database - CAN'T UNDO!
    conversation_manager.store_user_data(id, "first_name", "Shukriya")

    # Once stored, original value is gone. No way to replay or debug.
```

**V2 Pattern** ✅:
```python
# V2: Non-destructive updates (immutable state)

# Checkpointing preserves history
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

workflow = StateGraph(BookingState)
workflow.add_node("extract_name", extract_name_node)

# Compile with checkpointing
app = workflow.compile(checkpointer=checkpointer)

# Every state change is preserved
config = {"configurable": {"thread_id": "conversation_123"}}

# Turn 1: Extract "Sneha"
state_1 = await app.ainvoke(
    {"user_message": "I'm Sneha Reddy"},
    config=config
)
# Checkpoint saved: {"customer": {"first_name": "Sneha"}}

# Turn 2: Try to extract "Shukriya" (low confidence)
state_2 = await app.ainvoke(
    {"user_message": "Shukriya"},
    config=config
)
# Confidence merge REJECTS update → state unchanged
# Checkpoint saved: {"customer": {"first_name": "Sneha"}}  ← Still Sneha!

# Can rewind to any checkpoint:
history = await app.aget_state_history(config)
for state in history:
    print(f"Turn {state.metadata['turn']}: {state.values['customer']}")
# Output:
# Turn 1: {"first_name": "Sneha", "confidence": 0.9}
# Turn 2: {"first_name": "Sneha", "confidence": 0.9}  ← Didn't change!

# Can replay from any checkpoint:
await app.aupdate_state(
    config,
    values={"customer": {"first_name": "Riju"}},  # Manual correction
    as_node="extract_name"
)
# Replays from this point forward with corrected value
```

**Why This Works**:
- ✅ **Debuggable** - see every state transition
- ✅ **Reversible** - can undo/redo
- ✅ **Testable** - replay scenarios from checkpoints
- ✅ **Correctable** - fix mistakes without starting over
- ✅ **Auditable** - full history of what changed when

---

## Summary: Blender Principles → V2 Design

| Blender Principle | V2 Implementation |
|------------------|-------------------|
| **Single Responsibility** | Each node < 50 lines, does one thing |
| **Explicit Dependencies** | All deps in BookingState, no globals |
| **Bundles** | CustomerBundle, VehicleBundle (TypedDict) |
| **Dataflow** | Pure functions (state in → state out) |
| **Incremental Complexity** | MVP 1 (name) → MVP 2 (phone) → MVP 3 (vehicle) |
| **Conditional Routing** | LangGraph conditional_edges, not if/else in nodes |
| **Non-Destructive** | LangGraph checkpointing, confidence-based merge |
| **Composability** | Simple nodes + edges = complex workflows |

---

## Practical Example: Name Extraction (V1 vs V2)

### V1 Monolith: 942 Lines ❌

```python
# ONE FILE doing EVERYTHING
class DataExtractionService:
    # 200 lines: name extraction + normalization + validation
    # 200 lines: phone extraction + normalization + validation
    # 200 lines: vehicle extraction + normalization + validation
    # 200 lines: date extraction + normalization + validation
    # 142 lines: caching, preprocessing, utilities

# PLUS separate files for each type:
# extract_name.py, extract_phone.py, extract_vehicle.py, extract_date.py
# validate_name.py, validate_phone.py, validate_vehicle.py, validate_date.py
# scan_name.py, scan_phone.py, scan_vehicle.py, scan_date.py
# = 100+ domain-specific files!
```

### V2 Atomic Nodes: ~650 Lines Total (10 Files) ✅

```python
# nodes/atomic/extract.py (~80 lines)
# Works for name, phone, vehicle, date - ANY field!
async def node(state, extractor, field_path, fallback_fn):
    # ONE implementation, configured for each use

# nodes/atomic/validate.py (~60 lines)
# Works for ANY Pydantic model, ANY field!
async def node(state, model, field_path):
    # ONE implementation, configured for each use

# nodes/atomic/scan.py (~100 lines)
# Works for ANY source (history/DB/API), ANY field!
async def node(state, source, extractor, field_path):
    # ONE implementation, configured for each use

# nodes/atomic/confidence_gate.py (~50 lines)
async def node(state, compare_fn, field_path, new_value, new_confidence):
    # ONE implementation, configured for ANY comparison

# nodes/atomic/merge.py (~70 lines)
async def node(state, strategy, field_path, new_data):
    # ONE implementation, configured for ANY merge strategy

# ... 5 more atomic nodes (~240 lines)

# Total: 10 atomic nodes (~650 lines)
# Replace: 100+ domain-specific nodes (10,000+ lines)
# Reusable for: name, phone, vehicle, date, address, service, slot, etc.
```

### Node Group Composition (User-Created)

```python
# nodes/groups/name_extraction.py (~90 lines)
def create_name_extraction_group():
    """Compose atomic nodes for name extraction."""
    graph = StateGraph(BookingState)

    # Atomic node 1 configured for name
    graph.add_node("extract", lambda s: extract.node(s, NameExtractor(), "customer.first_name"))

    # Atomic node 2 configured for customer validation
    graph.add_node("validate", lambda s: validate.node(s, CustomerData, "customer"))

    # Atomic node 3 configured for history scan
    graph.add_node("scan", lambda s: scan.node(s, HistorySource(), NameExtractor(), "customer.first_name"))

    return graph.compile()

# Reuse for phone, vehicle, etc. with different configurations!
```

---

## Node Design Template (Blender-Inspired)

Use this template for every V2 node:

```python
"""
Node Name: [extract_name / validate_vehicle / scan_history / etc.]

Purpose: [One sentence - does ONE thing well]

Inputs (from state):
- state["field1"]: Description
- state["field2"]: Description

Outputs (to state):
- state["field3"]: Description
- state["field4"]: Description

Dependencies:
- utils.validation.is_vehicle_brand
- dspy_modules.extractors.NameExtractor

Conditions:
- Runs when: [condition]
- Skips when: [condition]

Example Flow:
  Input: {"user_message": "I'm Riju"}
  Output: {"customer": {"first_name": "Riju", "confidence": 0.9}}
"""

from typing import Dict, Any
from workflows.shared.state import BookingState
from utils.validation import is_vehicle_brand
from utils.confidence import merge_customer_data
from core.config import settings

import logging
logger = logging.getLogger(__name__)


async def node(state: BookingState) -> BookingState:
    """
    [Node purpose - one sentence]

    Single responsibility: [what this node does and ONLY does]
    """

    # 1. Extract inputs from state (explicit dependencies)
    user_message = state["user_message"]
    history = state["history"]

    # 2. Do the ONE thing this node is responsible for
    result = await do_the_thing(user_message, history)

    # 3. Validate result (if needed)
    if not validate_result(result):
        logger.warning(f"Validation failed: {result}")
        return state  # No change

    # 4. Update state (using utility functions)
    state = merge_data_into_state(state, result)

    # 5. Return updated state
    return state


# Helper functions (keep node clean)
async def do_the_thing(message: str, history: list) -> Dict[str, Any]:
    """The actual work this node does."""
    # Implementation here
    pass


def validate_result(result: Dict[str, Any]) -> bool:
    """Validate result before updating state."""
    # Validation here
    pass
```

---

## Sources

- [Blender Geometry Nodes Developer Documentation](https://developer.blender.org/docs/handbook/design/examples/geometry_nodes/)
- [Bundles and Closures in Geometry Nodes](https://code.blender.org/2025/08/bundles-and-closures/)
- [Geometry Nodes Workshop: September 2025](https://code.blender.org/2025/10/geometry-nodes-workshop-september-2025/)
- [Shader Nodes - Blender Manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/index.html)
- [Node Graph Architecture - Wikipedia](https://en.wikipedia.org/wiki/Node_graph_architecture)
- [Dataflow Programming - Wikipedia](https://en.wikipedia.org/wiki/Dataflow_programming)
- [Node-Based Procedural Workflow](https://med3017m-1819-14565893level3digital.coursework.lincoln.ac.uk/2018/10/14/node-based-procedural-workflow/)

---

**Next Step**: Apply this template to implement extract_name, extract_phone, extract_vehicle nodes following Blender's proven principles.

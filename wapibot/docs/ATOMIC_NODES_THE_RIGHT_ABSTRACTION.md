# Atomic Nodes: Finding the Right Level of Abstraction

**The Critical Question**: How much noding is too much noding?

**Date**: 2025-12-24
**Status**: CRITICAL DESIGN DECISION

---

## The Paradox of Node-Based Design

### Too Few Nodes (V1's Mistake) ❌
```
942-line monolith doing everything
→ Rigid, untestable, impossible to maintain
```

### Too Many Nodes (Visual Programming Hell) ❌
```
Every. Single. Function. As. A. Node.
→ You've just created a new programming language
→ Now you're coding with nodes instead of Python!
```

### The Sweet Spot (Workflow-Level Nodes) ✅
```
Nodes represent BUSINESS LOGIC STEPS
NOT programming primitives
```

---

## Examples: The Wrong Level of Abstraction

### ❌ BAD: Code-Level Nodes (Visual Programming Hell)

```python
# DON'T DO THIS - You're recreating Python in visual form!

[Get User Message Node]
    ↓
[Create DSPy Signature Node]
    ↓
[Configure Signature Fields Node]
    ↓
[Instantiate ChainOfThought Node]
    ↓
[Call DSPy Module Node]
    ↓
[Parse Result Node]
    ↓
[Check If None Node]
    ↓ (if None)
[Create Fallback Node]
    ↓
[Parse String Node]
    ↓
[Regex Match Node]
    ↓
[Extract Groups Node]
    ↓
[Convert To Dict Node]
    ↓
[Validate Schema Node]
    ↓
[Store In State Node]

# That's 14 nodes to do what should be ONE node!
```

**Problem**: You're now "coding with nodes" - every Python operation is a node. Users need to understand:
- DSPy internals
- Signature configuration
- Result parsing
- Error handling
- Data transformation

This defeats the PURPOSE of nodes (abstraction)!

### ✅ GOOD: Workflow-Level Node (The Right Abstraction)

```python
# Do this instead - ONE node for the workflow step

[Extract Customer Data Node]
  ↓
[Validate Data Node]
  ↓
[Call Yawlit API Node]

# That's 3 nodes for a complete workflow!
```

**Inside the `extract` node** (hidden implementation):
```python
# nodes/atomic/extract.py
async def node(
    state: BookingState,
    extractor: Callable,  # Could be DSPy, ReAct, regex, API, ANYTHING
    field_path: str
) -> BookingState:
    """
    Atomic extraction node - HIDES complexity.

    The extractor parameter can be:
    - DSPy ChainOfThought module
    - DSPy ReAct agent
    - DSPy Signature with custom pipeline
    - Regex pattern
    - API client
    - LLM call
    - Database query

    User doesn't need to know HOW extraction works,
    just WHAT to extract and WHERE to store it.
    """
    try:
        # Tier 1: Try configured extractor
        result = await asyncio.wait_for(
            extractor(state["history"], state["user_message"]),
            timeout=5.0
        )

        # Parse result (handles DSPy, dict, string, anything)
        if hasattr(result, 'value'):
            value = result.value  # DSPy module result
        elif isinstance(result, dict):
            value = result.get('value')  # Dict result
        else:
            value = str(result)  # String result

        set_nested_field(state, field_path, value)
        return state

    except (TimeoutError, ConnectionError):
        # Tier 2: Fallback (if provided)
        if hasattr(extractor, 'fallback'):
            result = extractor.fallback(state["user_message"])
            set_nested_field(state, field_path, result)
            return state

    except Exception as e:
        # Tier 3: Graceful degradation
        state["errors"].append(f"{field_path}_extraction_failed: {e}")
        return state

    return state
```

**Usage** (user-facing):
```python
# User configures extraction with ANY extractor

# Option 1: DSPy ChainOfThought
workflow.add_node("extract_name",
    lambda s: extract.node(s, NameExtractor(), "customer.first_name"))

# Option 2: DSPy ReAct agent
workflow.add_node("extract_intent",
    lambda s: extract.node(s, IntentReActAgent(), "intent"))

# Option 3: Custom DSPy pipeline
workflow.add_node("extract_refined",
    lambda s: extract.node(s, BestOfNRefineExtractor(), "customer.email"))

# Option 4: API call
workflow.add_node("extract_from_yawlit",
    lambda s: extract.node(s, YawlitCustomerAPI(), "customer"))

# Same node, different extractors - NO VISUAL PROGRAMMING!
```

---

## The 11 Atomic Nodes (Workflow-Level Abstraction)

### Principles

1. **Each node represents a BUSINESS STEP**, not a code operation
2. **Implementation is hidden** - user doesn't see DSPy internals
3. **Configuration over composition** - pass extractors/validators/etc. as params
4. **No primitives** - no if/else nodes, loop nodes, string concat nodes

### The Nodes

| Node | Workflow Purpose | Internal Implementation (Hidden) |
|------|------------------|----------------------------------|
| `extract` | Extract business data | DSPy modules, ReAct, regex, APIs, custom pipelines |
| `validate` | Validate business rules | Pydantic models, custom validators, LLM validation |
| `scan` | Search for missing data | History search, DB queries, API calls |
| `call_api` | Interact with external systems | HTTP clients, GraphQL, gRPC, webhooks |
| `confidence_gate` | Gate data updates | Simple threshold, LLM judge, custom logic |
| `merge` | Combine data sources | Confidence-based, timestamp-based, LLM-based |
| `transform` | Business logic transforms | Format conversion, enrichment, calculation |
| `condition` | Workflow routing | Field presence, completeness, custom predicates |
| `response` | Generate user response | Templates, LLMs, hybrid approaches |
| `log` | Observability | Structured logging, metrics, tracing |
| `checkpoint` | State persistence | Save/load at workflow milestones |

---

## Deep Dive: `call_api` Node (External System Integration)

### Purpose (Workflow-Level)
Call external APIs to enrich data, trigger actions, or fetch information.

### Implementation (Code-Level, Hidden from Users)

```python
# nodes/atomic/call_api.py (~100 lines)
"""
Atomic API call node.

User configures WHAT API to call and HOW to handle response.
Implementation handles retries, timeouts, error handling, parsing.
"""

from typing import Callable, Dict, Any, Optional
import httpx
import asyncio

class APIRequest:
    """Base class for API request builders."""
    def build_request(self, state: BookingState) -> Dict[str, Any]:
        """Build request from state."""
        raise NotImplementedError

    def parse_response(self, response: httpx.Response) -> Any:
        """Parse API response."""
        raise NotImplementedError


class YawlitCustomerAPI(APIRequest):
    """Yawlit backend API - get customer data."""

    def __init__(self, endpoint: str = "/api/customers"):
        self.endpoint = endpoint

    def build_request(self, state: BookingState) -> Dict[str, Any]:
        """Build request to fetch customer from Yawlit."""
        phone = state.get("customer", {}).get("phone", "")
        return {
            "method": "GET",
            "url": f"{settings.yawlit_base_url}{self.endpoint}",
            "params": {"phone": phone},
            "headers": {"Authorization": f"Bearer {settings.yawlit_api_key}"}
        }

    def parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse Yawlit customer response."""
        data = response.json()
        return {
            "first_name": data.get("firstName"),
            "last_name": data.get("lastName"),
            "email": data.get("email"),
            "address": data.get("defaultAddress")
        }


class FrappeBookingAPI(APIRequest):
    """Frappe backend API - create booking."""

    def __init__(self, endpoint: str = "/api/resource/Booking"):
        self.endpoint = endpoint

    def build_request(self, state: BookingState) -> Dict[str, Any]:
        """Build request to create booking in Frappe."""
        return {
            "method": "POST",
            "url": f"{settings.frappe_base_url}{self.endpoint}",
            "json": {
                "customer_name": f"{state['customer']['first_name']} {state['customer']['last_name']}",
                "vehicle_brand": state['vehicle']['brand'],
                "vehicle_model": state['vehicle']['model'],
                "appointment_date": state['appointment']['date'],
                "service_type": state.get('service_type', 'one_time')
            },
            "headers": {
                "Authorization": f"token {settings.frappe_api_key}:{settings.frappe_api_secret}"
            }
        }

    def parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse Frappe booking creation response."""
        data = response.json()
        return {
            "booking_id": data["data"]["name"],
            "status": data["data"]["status"]
        }


async def node(
    state: BookingState,
    api_request: APIRequest,      # ← User provides request builder
    field_path: str,               # ← Where to store result
    retry_count: int = 3,
    timeout: float = 10.0
) -> BookingState:
    """
    Atomic API call node with retries and error handling.

    Examples:
        # Fetch customer from Yawlit
        call_api.node(state, YawlitCustomerAPI(), "customer")

        # Create booking in Frappe
        call_api.node(state, FrappeBookingAPI(), "booking_id")

        # Custom API call
        call_api.node(state, CustomAPI("https://api.example.com"), "result")
    """
    request_config = api_request.build_request(state)

    async with httpx.AsyncClient() as client:
        for attempt in range(retry_count):
            try:
                # Make HTTP request
                response = await asyncio.wait_for(
                    client.request(**request_config),
                    timeout=timeout
                )

                # Check status
                response.raise_for_status()

                # Parse response
                result = api_request.parse_response(response)

                # Store in state
                set_nested_field(state, field_path, result)

                logger.info(f"✅ API call successful: {field_path}")
                return state

            except httpx.HTTPStatusError as e:
                logger.warning(f"⚠️ API returned {e.response.status_code}, attempt {attempt + 1}/{retry_count}")
                if attempt == retry_count - 1:
                    state["errors"].append(f"api_call_failed: {e.response.status_code}")
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except asyncio.TimeoutError:
                logger.warning(f"⏱️ API timeout, attempt {attempt + 1}/{retry_count}")
                if attempt == retry_count - 1:
                    state["errors"].append(f"api_timeout: {timeout}s")
                else:
                    await asyncio.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"❌ API call failed: {e}")
                state["errors"].append(f"api_error: {str(e)}")
                return state

    return state
```

### Usage (User-Facing)

```python
# User configures API calls in workflow

workflow = StateGraph(BookingState)

# Node 1: Fetch customer data from Yawlit
workflow.add_node("fetch_customer_from_yawlit",
    lambda s: call_api.node(
        s,
        api_request=YawlitCustomerAPI("/api/customers"),
        field_path="customer",
        retry_count=3,
        timeout=5.0
    ))

# Node 2: Create booking in Frappe
workflow.add_node("create_frappe_booking",
    lambda s: call_api.node(
        s,
        api_request=FrappeBookingAPI("/api/resource/Booking"),
        field_path="booking_id",
        retry_count=2,
        timeout=10.0
    ))

# Node 3: Send confirmation to Yawlit webhook
workflow.add_node("notify_yawlit",
    lambda s: call_api.node(
        s,
        api_request=YawlitWebhookAPI("/api/webhooks/booking-confirmed"),
        field_path="webhook_result"
    ))

# Routing
workflow.add_edge("fetch_customer_from_yawlit", "create_frappe_booking")
workflow.add_edge("create_frappe_booking", "notify_yawlit")

# User sees 3 workflow steps, doesn't see:
# - HTTP client setup
# - Retry logic
# - Exponential backoff
# - Error handling
# - Response parsing
# - Timeout management
```

---

## DSPy Integration: Inside Nodes, Not As Nodes

### ❌ WRONG: DSPy Components As Nodes

```python
# Don't do this - you're exposing implementation details!

workflow.add_node("create_signature", lambda s: create_dspy_signature_node(s))
workflow.add_node("configure_cot", lambda s: configure_chain_of_thought_node(s))
workflow.add_node("call_dspy", lambda s: call_dspy_module_node(s))
workflow.add_node("parse_result", lambda s: parse_dspy_result_node(s))
workflow.add_node("validate_output", lambda s: validate_dspy_output_node(s))

# Now user needs to understand DSPy internals to use your system!
```

### ✅ RIGHT: DSPy As Implementation Detail Inside Nodes

```python
# Do this - DSPy is hidden inside atomic nodes

# The extract node accepts ANY extractor (DSPy, regex, API, etc.)
workflow.add_node("extract_name",
    lambda s: extract.node(s, NameExtractor(), "customer.first_name"))

# Behind the scenes (inside extract.py):
# - DSPy signature created
# - ChainOfThought instantiated
# - Module called
# - Result parsed
# - Fallback handled
# - State updated
#
# User doesn't see any of this!
```

### DSPy ReAct Agent Example

From [DSPy ReAct Tutorial](https://dspy.ai/tutorials/customer_service_agent/):

```python
# The ReAct agent is an EXTRACTOR, not a node itself!

class CustomerIntentReActAgent:
    """DSPy ReAct agent for intent classification."""

    def __init__(self):
        # Define tools for ReAct agent
        self.tools = [
            self.check_booking_history,
            self.check_service_catalog,
            self.check_pricing
        ]

        # Create ReAct agent
        self.agent = dspy.ReAct(
            signature="question -> answer",
            tools=self.tools,
            max_iters=5
        )

    def __call__(self, history: List[Dict], user_message: str) -> str:
        """Extract intent using ReAct reasoning."""
        # Build context from history
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-5:]])

        # Run ReAct agent
        result = self.agent(
            question=f"Context: {context}\n\nUser message: {user_message}\n\nWhat is the user's intent?"
        )

        return result.answer

    def check_booking_history(self, customer_id: str) -> str:
        """Tool: Check if customer has bookings."""
        # Implementation...
        pass

    def check_service_catalog(self, query: str) -> str:
        """Tool: Search service catalog."""
        # Implementation...
        pass

    def check_pricing(self, service: str) -> str:
        """Tool: Get pricing info."""
        # Implementation...
        pass


# Usage: ReAct agent is just ANOTHER extractor
workflow.add_node("classify_intent",
    lambda s: extract.node(
        s,
        extractor=CustomerIntentReActAgent(),  # ← ReAct agent as extractor
        field_path="intent"
    ))

# Same extract node, different extractor!
# No need for separate "ReAct node" - it's just an implementation detail
```

### DSPy Best-of-N + Refine Pattern (Real Implementation)

From [Best-of-N and Refine Tutorial](https://dspy.ai/tutorials/output_refinement/best-of-n-and-refine/):

**DSPy provides two refinement strategies:**

1. **BestOfN**: Runs module N times independently, picks highest score
2. **Refine**: Runs with feedback loops - failed attempts generate hints for next try

```python
# Pattern 1: BestOfN (Independent Attempts)
class BestOfNNameExtractor:
    """Extract name N times, pick best result based on confidence."""

    def __init__(self, n=3):
        # Use DSPy's built-in BestOfN module
        self.extractor = dspy.BestOfN(
            module=dspy.ChainOfThought(NameExtractionSignature),
            N=n,
            reward_fn=self.score_extraction,
            threshold=0.9
        )

    def score_extraction(self, args, pred: dspy.Prediction) -> float:
        """Reward function: Returns 0.0-1.0 score."""
        # High score if name looks valid
        if pred.first_name and not is_vehicle_brand(pred.first_name):
            return 1.0 if len(pred.first_name) > 1 else 0.5
        return 0.0

    def __call__(self, conversation_history, user_message):
        return self.extractor(
            conversation_history=conversation_history,
            user_message=user_message
        )


# Pattern 2: Refine (Iterative Improvement with Feedback)
class RefineNameExtractor:
    """Extract name with iterative refinement based on feedback."""

    def __init__(self, n=3):
        # Use DSPy's built-in Refine module
        self.extractor = dspy.Refine(
            module=dspy.ChainOfThought(NameExtractionSignature),
            N=n,
            reward_fn=self.score_extraction,
            threshold=0.9
        )

    def score_extraction(self, args, pred: dspy.Prediction) -> float:
        """Reward function with detailed feedback."""
        score = 0.0

        # Check if name exists
        if not pred.first_name:
            return 0.0

        # Check if it's a vehicle brand (penalty)
        if is_vehicle_brand(pred.first_name):
            return 0.0

        # Check if it's a greeting stopword (penalty)
        if pred.first_name.lower() in GREETING_STOPWORDS:
            return 0.0

        # Valid name found
        score = 1.0

        return score

    def __call__(self, conversation_history, user_message):
        # Refine will:
        # 1. Try extraction
        # 2. If score < threshold, generate feedback
        # 3. Try again with feedback as hint
        # 4. Repeat up to N times
        return self.extractor(
            conversation_history=conversation_history,
            user_message=user_message
        )


# Usage in workflow - SAME extract node, different extractors!

# Option 1: BestOfN (parallel attempts)
workflow.add_node("extract_name_best_of_n",
    lambda s: extract.node(
        s,
        extractor=BestOfNNameExtractor(n=3),
        field_path="customer.first_name"
    ))

# Option 2: Refine (iterative improvement)
workflow.add_node("extract_name_refined",
    lambda s: extract.node(
        s,
        extractor=RefineNameExtractor(n=3),
        field_path="customer.first_name"
    ))

# NO separate nodes for:
# ❌ generate_attempts_node
# ❌ score_attempts_node
# ❌ generate_feedback_node
# ❌ refine_attempt_node
# ❌ select_best_node
#
# All hidden inside the extractor!
```

**Key Insight**: BestOfN and Refine are **extractor implementations**, not workflow nodes!

---

## The Rule: Workflow Steps, Not Code Operations

### Ask Yourself

When designing a node, ask:

1. **Is this a business workflow step?**
   ✅ "Extract customer data"
   ✅ "Validate booking completeness"
   ✅ "Call external API"
   ❌ "Parse JSON"
   ❌ "Create DSPy signature"
   ❌ "Loop through list"

2. **Can a non-programmer understand what this node does?**
   ✅ "Extract Name" - anyone understands
   ❌ "Instantiate ChainOfThought" - only DSPy experts understand

3. **Does this hide complexity or expose it?**
   ✅ Extract node hides DSPy/regex/API complexity
   ❌ DSPy signature node exposes DSPy internals

4. **Would you draw this on a whiteboard workflow diagram?**
   ✅ [Get Data] → [Validate] → [Call API] → [Respond]
   ❌ [Parse] → [Transform] → [Map] → [Filter] → [Reduce] → [Format]

---

## Summary: The 11 Atomic Nodes

All 11 nodes are **WORKFLOW-level**, not code-level:

```python
nodes/atomic/
├── extract.py         # Extract data (DSPy, ReAct, regex, API - ANY extractor)
├── validate.py        # Validate data (Pydantic, LLM, custom - ANY validator)
├── scan.py            # Scan sources (history, DB, API - ANY source)
├── call_api.py        # Call external APIs (Yawlit, Frappe, webhooks - ANY API)
├── confidence_gate.py # Gate updates (threshold, LLM judge - ANY comparison)
├── merge.py           # Merge data (confidence, timestamp, LLM - ANY strategy)
├── transform.py       # Transform data (format, enrich, calculate - ANY transform)
├── condition.py       # Route workflow (presence, completeness - ANY predicate)
├── response.py        # Generate response (template, LLM, hybrid - ANY generator)
├── log.py             # Observability (structured logs, metrics - ANY logger)
└── checkpoint.py      # State persistence (milestones, errors - ANY trigger)
```

**Each node**:
- Represents a **business workflow step**
- Hides **implementation complexity**
- Accepts **any implementation** through configuration
- Is **understandable by non-programmers**

**DSPy components** (signatures, modules, ReAct, refinement) are **INSIDE** nodes as implementation details, not AS nodes.

---

## Next Steps

1. Implement the 11 atomic nodes at **workflow-level abstraction**
2. Create extractors for DSPy, ReAct, refinement pipelines
3. Test: "Can a non-programmer understand the workflow graph?"
4. If answer is NO → abstraction level is wrong → fix it

**Remember**: You're building a workflow engine, not a visual programming language! 🚀

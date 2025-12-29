# WapiBot Backend V2 Refactoring Plan: 50 Steps to SOLID, DRY, and Blender Principles

## Overview

This plan follows the **Brain_based_refactoring.md** architecture to refactor the WapiBot backend using:

- **SOLID principles** (especially Single Responsibility and Composition)
- **DRY principles** (Don't Repeat Yourself - reuse atomic nodes)
- **100 lines per file** (max 150 with overhead)
- **Composition over creation** (use existing atomic nodes, don't create new ones)
- **Blender-like design** (Atomic → Domain → Node Groups → Workflows)

## Architecture Layers

```bash
Layer 1: Atomic Nodes (src/nodes/atomic/)
    ↓ composed into
Layer 2: Domain Nodes (src/nodes/extraction/, src/nodes/selection/, src/nodes/brain/)
    ↓ composed into
Layer 3: Node Groups (src/workflows/node_groups/) ← ONLY wiring, NO logic
    ↓ composed into
Layer 4: Workflows (src/workflows/)
```

**Key Principle:** Brain awareness goes in Layer 1 (atomic) and Layer 2 (domain), NOT in node groups.

## Current State Summary

### Critical Issues

1. **Node groups have inline logic** - violates SOLID, DRY, 100-line rule
2. **Atomic extract.py is unused** - booking flow has inline extraction instead
3. **Brain toggles are orphaned** - exist but never control behavior
4. **extract_name.py violates DRY** - 142 lines that should use atomic extract.node()

### Files Exceeding Limits

- `booking_group.py` (357 lines) - has inline confirmation, pricing, creation logic
- `addon_group.py` (264 lines) - has inline message building and extraction
- `call_api.py` (255 lines) - needs split into protocol + retry + impl
- `slot_preference_group.py` (237 lines) - has inline extraction logic
- `read_model.py` (237 lines) - mixes reading + validation
- `slot_group.py` (218 lines) - has inline filtering and grouping
- `address_group.py` (215 lines) - has inline message building
- `utilities_group.py` (178 lines) - has inline yes/no extraction

### Brain Infrastructure (Built but Not Integrated)

- `brain_config.py` (66 lines) ✓ - Configuration system exists
- `brain_toggles.py` (57 lines) ✓ - Toggle functions exist
- `brain_router.py` (57 lines) ✓ - Routing logic exists
- Brain nodes exist but not wired into workflows

---

## 50-Step Refactoring Plan

### Phase 1: Atomic Layer - Brain Awareness (Steps 1-10)

**Goal:** Add brain mode awareness to atomic nodes without changing their interfaces or creating new Protocol files.

### Step 1: Add brain strategy helpers to extract.py

**File:** `/backend/src/nodes/atomic/extract.py` (202 lines)
**Principle:** Open/Closed
**Action:** Add brain mode logic to existing node

**What to do:**

- Add `respect_brain_mode: bool = True` parameter (backward compatible)
- Import `get_brain_settings()` from `core.brain_config`
- Add brain mode logic:
  - **Reflex mode**: Try regex fallback FIRST (cheaper), then DSPy if `reflex_fail_fast=False`
  - **Conscious mode**: Try DSPy FIRST (quality), then regex fallback
  - **Shadow mode**: Brain proposes what it WOULD do, logs comparison with actual workflow action, but NEVER acts (for learning)
- Extract brain strategy logic to private functions `_reflex_extract()`, `_conscious_extract()`, `_shadow_extract()`
- Target: Keep under 150 lines by using helper functions

### Step 2: Add brain customization to send_message.py

**File:** `/backend/src/nodes/atomic/send_message.py` (160 lines)
**Principle:** Open/Closed
**Action:** Add brain personalization hook

**What to do:**

- Add `allow_brain_customize: bool = True` parameter
- Import `can_customize_template()` from `core.brain_toggles`
- Import `personalize_message.node()` from `nodes.brain.personalize_message`
- If conscious mode + toggle enabled: call `personalize_message.node()` before sending
- Target: ~175 lines (acceptable with overhead)

### Step 3: Add brain monitoring to call_api.py

**File:** `/backend/src/nodes/atomic/call_api.py` (255 lines)
**Principle:** Single Responsibility - SPLIT into 3 files first
**Action:** Split file, then add brain monitoring

**What to do:**

- Split into:
  - `/backend/src/nodes/atomic/_call_api_retry.py` (70 lines) - retry decorator logic
  - `/backend/src/nodes/atomic/_call_api_helpers.py` (85 lines) - request/response formatting
  - `/backend/src/nodes/atomic/call_api.py` (100 lines) - core node using helpers
- Add brain logging for API latency tracking
- Target: 100 lines for main file

### Step 4: Add brain awareness to validate.py

**File:** `/backend/src/nodes/atomic/validate.py` (166 lines)
**Principle:** Open/Closed
**Action:** Add brain correction suggestions

**What to do:**

- Add `respect_brain_mode: bool = True` parameter
- If validation fails in conscious mode, check if brain has suggested corrections
- Log validation failures to brain for learning
- Target: ~180 lines (acceptable)

### Step 5: Add brain routing to merge.py

**File:** `/backend/src/nodes/atomic/merge.py` (183 lines)
**Principle:** Open/Closed
**Action:** Add brain merge strategy selection

**What to do:**

- If conscious mode, brain can override merge strategy (confidence vs timestamp vs LLM)
- Log merge decisions to brain for learning
- Target: ~195 lines (acceptable)

### Step 6: Enhance brain_toggles.py with extraction strategies

**File:** `/backend/src/core/brain_toggles.py` (57 lines)
**Principle:** Single Responsibility
**Action:** Add helper functions for atomic nodes

**What to do:**

- Add `get_extraction_strategy() -> "regex_first" | "dspy_first" | "both"`
- Add `should_try_dspy_after_regex_fail() -> bool`
- Add `should_log_for_brain_learning() -> bool`
- Target: ~80 lines

### Step 7: Split read_model.py to use existing validate.py

**File:** `/backend/src/nodes/atomic/read_model.py` (237 lines)
**Principle:** Composition over creation + DRY
**Action:** Remove validation logic, delegate to validate.py

**What to do:**

- read_model.py should ONLY read data from sources (DB, API, state)
- Remove Pydantic validation logic (lines 180-220)
- In workflows: compose `read_model.node()` → `validate.node()`
- Target: ~100 lines (reduced by 137 lines)

### Step 8: Add brain observation decorator

**File:** `/backend/src/nodes/brain/observation_hook.py` (NEW - 80 lines)
**Principle:** Blender design
**Action:** Create reusable decorator for brain observation

**What to do:**

- Create `@observe_with_brain` decorator
- Wraps any node function to log inputs, outputs, latency, errors
- Used by brain for reinforcement learning
- Can be applied to any node without modifying node code
- Target: 80 lines

### Step 9: Create brain workflow wrapper

**File:** `/backend/src/workflows/brain_workflow.py` (NEW - 90 lines)
**Principle:** Dependency Inversion
**Action:** Wrap existing workflows with brain observation

**What to do:**

- Create wrapper function that takes any workflow
- Injects brain observation before/after each node
- Workflows unchanged - brain is transparently injected
- Uses `observation_hook.py` decorator
- Target: 90 lines

### Step 10: Update .env configuration for brain modes

**File:** `./.env.txt`
**Principle:** Configuration
**Action:** Document brain configuration options

**What to do:**

- Add brain mode settings:

  ```bash
  BRAIN_ENABLED=true
  BRAIN_MODE=reflex  # shadow | reflex | conscious
  REFLEX_REGEX_FIRST=true
  REFLEX_FAIL_FAST=false
  REFLEX_TEMPLATE_ONLY=true
  ```

- Document what each mode does
- Target: Add 10-15 lines of config

---

### Phase 2: Domain Layer - Extraction Nodes (Steps 11-25)

**Goal:** Create domain extraction nodes that COMPOSE atomic extract.node(), removing inline logic from node groups.

### Step 11: Create extract_slot_preference.py domain node

**File:** `/backend/src/nodes/extraction/extract_slot_preference.py` (NEW - 60 lines)
**Principle:** Composition - reuse atomic extract.node()
**Action:** Create domain node for slot preference extraction

**What to do:**

- Create `regex_fallback(message)` function using existing `extract_time_range()` and `extract_date()`
- Create `node(state)` function that calls `extract.node(state, SlotPreferenceExtractor(), "slot_preference", regex_fallback)`
- Uses existing atomic extract.node() - no duplication
- Target: 60 lines

### Step 12: Create extract_confirmation.py domain node

**File:** `/backend/src/nodes/extraction/extract_confirmation.py` (NEW - 40 lines)
**Principle:** Composition - reuse atomic extract.node()
**Action:** Create domain node for yes/no confirmation

**What to do:**

- Create `regex_fallback(message)` for yes/no/confirm/cancel patterns
- Create `node(state, field_path)` that calls `extract.node(state, ConfirmationExtractor(), field_path, regex_fallback)`
- Reusable for booking confirmation, addon skip, utilities, etc.
- Target: 40 lines

### Step 13: Create extract_utilities.py domain node

**File:** `/backend/src/nodes/extraction/extract_utilities.py` (NEW - 45 lines)
**Principle:** Composition - reuse atomic extract.node()
**Action:** Create domain node for electricity/water yes/no

**What to do:**

- Create `regex_fallback(message)` for electricity/water yes/no patterns
- Create `extract_electricity(state)` and `extract_water(state)` using `extract.node()`
- Target: 45 lines

### Step 14: Refactor extract_name.py to use atomic extract.node()

**File:** `/backend/src/nodes/extraction/extract_name.py` (142 → 60 lines)
**Principle:** DRY - eliminate duplication
**Action:** Remove duplicated extraction logic

**What to do:**

- Keep only `regex_fallback(message)` function (20 lines)
- Replace extraction logic with `extract.node(state, NameExtractor(), "customer.first_name", regex_fallback)`
- Remove 80+ lines of duplicated retry/timeout/fallback logic
- Target: 60 lines (reduced by 82 lines)

### Step 15: Create AddonSelectionBuilder message builder

**File:** `/backend/src/nodes/message_builders/addon_selection.py` (NEW - 50 lines)
**Principle:** Single Responsibility - extract from node group
**Action:** Move inline message builder from addon_group.py

**What to do:**

- Extract `build_addon_message` function from `/backend/src/workflows/node_groups/addon_group.py` (lines 55-87)
- Create `AddonSelectionBuilder` class implementing MessageBuilder Protocol
- Reusable across workflows
- Target: 50 lines

### Step 16: Create AddressMessageBuilder message builder

**File:** `/backend/src/nodes/message_builders/address_selection.py` (NEW - 45 lines)
**Principle:** Single Responsibility - extract from node group
**Action:** Move inline message builder from address_group.py

**What to do:**

- Extract inline address message building from `/backend/src/workflows/node_groups/address_group.py`
- Create `AddressMessageBuilder` class
- Target: 45 lines

### Step 17: Create UtilitiesMessageBuilder message builder

**File:** `/backend/src/nodes/message_builders/utilities_selection.py` (NEW - 40 lines)
**Principle:** Single Responsibility - extract from node group
**Action:** Move inline message builder from utilities_group.py

**What to do:**

- Extract inline utilities message building
- Create `UtilitiesMessageBuilder` class
- Target: 40 lines

### Step 18: Create BookingConfirmationBuilder message builder

**File:** `/backend/src/nodes/message_builders/booking_confirmation_full.py` (NEW - 60 lines)
**Principle:** Single Responsibility - extract from node group
**Action:** Move inline confirmation message from booking_group.py

**What to do:**

- Extract inline booking confirmation message (lines 264-282)
- Create `BookingConfirmationBuilder` class
- Includes: customer name, service, vehicle, slot, price
- Target: 60 lines

### Step 19: Create AddonExtractor DSPy module

**File:** `/backend/src/dspy_modules/extractors/addon_extractor.py` (NEW - 40 lines)
**Principle:** Composition - create extractor for atomic extract.node()
**Action:** Extract addon selection logic to DSPy module

**What to do:**

- Create `AddonExtractor` DSPy module for extracting addon selections
- Implements Extractor Protocol
- Used by `extract.node(state, AddonExtractor(), "addon_selection")`
- Target: 40 lines

### Step 20: Create UtilitiesExtractor DSPy module

**File:** `/backend/src/dspy_modules/extractors/utilities_extractor.py` (NEW - 35 lines)
**Principle:** Composition - create extractor for atomic extract.node()
**Action:** Extract utilities selection logic to DSPy module

**What to do:**

- Create `UtilitiesExtractor` for electricity/water yes/no
- Implements Extractor Protocol
- Target: 35 lines

### Step 21: Create slot filter transformer

**File:** `/backend/src/nodes/transformers/filter_slots.py` (NEW - 60 lines)
**Principle:** Single Responsibility - extract from slot_group.py
**Action:** Move inline slot filtering to transformer

**What to do:**

- Extract slot filtering logic from `/backend/src/workflows/node_groups/slot_group.py` (lines 70-88)
- Create `FilterSlots` transformer class
- Used by `transform.node(state, FilterSlots(), "filtered_slots")`
- Target: 60 lines

### Step 22: Create slot grouper transformer

**File:** `/backend/src/nodes/transformers/group_slots.py` (NEW - 70 lines)
**Principle:** Single Responsibility - extract from slot_group.py
**Action:** Move inline slot grouping to transformer

**What to do:**

- Extract slot grouping by time-of-day logic from slot_group.py
- Create `GroupSlotsByTime` transformer class
- Target: 70 lines

### Step 23: Create booking price calculator

**File:** `/backend/src/nodes/transformers/calculate_price.py` (NEW - 80 lines)
**Principle:** Single Responsibility - extract from booking_group.py
**Action:** Move pricing calculation to transformer

**What to do:**

- Extract `calculate_price()` logic from `/backend/src/workflows/node_groups/booking_group.py`
- Create `CalculateBookingPrice` transformer
- Sums service + vehicle + addons prices
- Target: 80 lines

### Step 24: Create selection error handler

**File:** `/backend/src/nodes/selection/selection_error_handler.py` (NEW - 50 lines)
**Principle:** DRY - reuse across node groups
**Action:** Extract common selection error handling

**What to do:**

- Extract error handling pattern from vehicle_group, addon_group, address_group
- Create `send_selection_error(state, error_message, current_step)` function
- Reusable across all selection node groups
- Target: 50 lines

### Step 25: Create continuation/resume router

**File:** `/backend/src/nodes/routing/resume_router.py` (NEW - 60 lines)
**Principle:** DRY - reuse resume logic
**Action:** Extract resume/continuation pattern

**What to do:**

- Extract resume logic from vehicle_group, addon_group (lines 61-84 in vehicle_group)
- Create `route_on_resume(state, step_name, has_options_key, selected_key)` function
- Returns: "skip" | "show_options" | "process_selection"
- Reusable across all node groups
- Target: 60 lines

---

### Phase 3: Node Group Refactoring - Remove Inline Logic (Steps 26-40)

**Goal:** Refactor node groups to ONLY wire nodes - no inline logic. Use domain nodes and message builders.

### Step 26: Refactor slot_preference_group.py - remove inline extraction

**File:** `/backend/src/workflows/node_groups/slot_preference_group.py` (237 → 120 lines)
**Principle:** Composition - use domain extraction node
**Action:** Replace inline extraction with extract_slot_preference.node()

**What to do:**

- Remove inline `extract_preference()` logic (lines 80-150)
- Replace with: `return await extract_slot_preference.node(state)`
- Import from `/backend/src/nodes/extraction/extract_slot_preference.py` (Step 11)
- Target: 120 lines (reduced by 117 lines)

### Step 27: Refactor booking_group.py - remove inline confirmation extraction

**File:** `/backend/src/workflows/node_groups/booking_group.py` (357 → 280 lines)
**Principle:** Composition - use domain extraction node
**Action:** Replace inline confirmation with extract_confirmation.node()

**What to do:**

- Remove inline yes/no confirmation logic (lines 103-115)
- Replace with: `return await extract_confirmation.node(state, "booking_confirmed")`
- Import from `/backend/src/nodes/extraction/extract_confirmation.py` (Step 12)
- Target: Reduce by 77 lines

### Step 28: Refactor booking_group.py - extract price calculation

**File:** `/backend/src/workflows/node_groups/booking_group.py` (280 → 220 lines)
**Principle:** Composition - use transformer node
**Action:** Replace inline pricing with calculate_price transformer

**What to do:**

- Remove inline `calculate_price()` function (lines 185-245)
- Replace with: `return await transform.node(state, CalculateBookingPrice(), "total_price")`
- Import CalculateBookingPrice from Step 23
- Target: Reduce by 60 lines

### Step 29: Refactor booking_group.py - extract message builders

**File:** `/backend/src/workflows/node_groups/booking_group.py` (220 → 140 lines)
**Principle:** Composition - use message builders
**Action:** Replace inline message building with BookingConfirmationBuilder

**What to do:**

- Replace inline confirmation messages (lines 264-282) with `send_message.node(state, BookingConfirmationBuilder())`
- Import BookingConfirmationBuilder from Step 18
- Target: Reduce by 80 lines

### Step 30: Refactor addon_group.py - extract message builder

**File:** `/backend/src/workflows/node_groups/addon_group.py` (264 → 214 lines)
**Principle:** Composition - use message builder
**Action:** Replace inline addon message with AddonSelectionBuilder

**What to do:**

- Remove `build_addon_message()` function (lines 55-87)
- Replace with: `send_message.node(state, AddonSelectionBuilder())`
- Import AddonSelectionBuilder from Step 15
- Target: Reduce by 50 lines

### Step 31: Refactor addon_group.py - use atomic extract for selection

**File:** `/backend/src/workflows/node_groups/addon_group.py` (214 → 140 lines)
**Principle:** Composition - use atomic extract.node()
**Action:** Replace inline extraction with extract.node() + AddonExtractor

**What to do:**

- Remove inline `extract_addon_selection()` function (lines 97-140)
- Replace with: `extract.node(state, AddonExtractor(), "addon_selection", regex_fallback)`
- Import AddonExtractor from Step 19
- Target: Reduce by 74 lines

### Step 32: Refactor utilities_group.py - extract message builder

**File:** `/backend/src/workflows/node_groups/utilities_group.py` (178 → 138 lines)
**Principle:** Composition - use message builder
**Action:** Replace inline utilities message with UtilitiesMessageBuilder

**What to do:**

- Remove inline message building
- Replace with: `send_message.node(state, UtilitiesMessageBuilder())`
- Import from Step 17
- Target: Reduce by 40 lines

### Step 33: Refactor utilities_group.py - use domain extraction

**File:** `/backend/src/workflows/node_groups/utilities_group.py` (138 → 100 lines)
**Principle:** Composition - use domain extraction
**Action:** Replace inline yes/no extraction with extract_utilities.node()

**What to do:**

- Remove inline extraction logic
- Replace with calls to `extract_utilities.extract_electricity()` and `extract_utilities.extract_water()`
- Import from Step 13
- Target: Reduce by 38 lines

### Step 34: Refactor address_group.py - extract message builder

**File:** `/backend/src/workflows/node_groups/address_group.py` (215 → 170 lines)
**Principle:** Composition - use message builder
**Action:** Replace inline address message with AddressMessageBuilder

**What to do:**

- Remove `build_address_message()` function
- Replace with: `send_message.node(state, AddressMessageBuilder())`
- Import from Step 16
- Target: Reduce by 45 lines

### Step 35: Refactor address_group.py - use generic selection handler

**File:** `/backend/src/workflows/node_groups/address_group.py` (170 → 120 lines)
**Principle:** DRY - reuse existing generic_handler
**Action:** Replace inline selection logic with generic_handler.handle_selection()

**What to do:**

- Remove inline `process_address_selection()` function
- Replace with: `generic_handler.handle_selection(state, "address", "address_options", "address")`
- Already exists in `/backend/src/nodes/selection/generic_handler.py`
- Target: Reduce by 50 lines

### Step 36: Refactor slot_group.py - use slot filter transformer

**File:** `/backend/src/workflows/node_groups/slot_group.py` (218 → 160 lines)
**Principle:** Composition - use transformer
**Action:** Replace inline slot filtering with FilterSlots transformer

**What to do:**

- Remove inline filtering logic (lines 70-88)
- Replace with: `transform.node(state, FilterSlots(), "filtered_slots")`
- Import from Step 21
- Target: Reduce by 58 lines

### Step 37: Refactor slot_group.py - use slot grouper transformer

**File:** `/backend/src/workflows/node_groups/slot_group.py` (160 → 120 lines)
**Principle:** Composition - use transformer
**Action:** Replace inline grouping with GroupSlotsByTime transformer

**What to do:**

- Remove inline grouping logic
- Replace with: `transform.node(state, GroupSlotsByTime(), "grouped_slots")`
- Import from Step 22
- Target: Reduce by 40 lines

### Step 38: Refactor all selection groups - use resume_router

**Files:** vehicle_group.py, addon_group.py, address_group.py, service_group.py
**Principle:** DRY - reuse resume routing logic
**Action:** Replace duplicated resume logic with resume_router

**What to do:**

- In each group, replace `route_*_entry()` function with call to `resume_router.route_on_resume()`
- Import from Step 25
- Reduces each file by ~20 lines
- Target: Total reduction of 80 lines across 4 files

### Step 39: Refactor all selection groups - use selection_error_handler

**Files:** vehicle_group.py, addon_group.py, address_group.py, service_group.py
**Principle:** DRY - reuse error handling
**Action:** Replace duplicated error handling with selection_error_handler

**What to do:**

- In each group, replace `send_*_error()` function with `selection_error_handler.send_selection_error()`
- Import from Step 24
- Reduces each file by ~15 lines
- Target: Total reduction of 60 lines across 4 files

### Step 40: Final cleanup - verify all node groups under 150 lines

**Files:** All node groups in `/backend/src/workflows/node_groups/`
**Principle:** 100-line limit (150 with overhead)
**Action:** Verify and document line counts

**What to do:**

- Run line count on all node groups
- Expected results:
  - slot_preference_group.py: ~120 lines ✓
  - booking_group.py: ~140 lines ✓
  - addon_group.py: ~140 lines ✓
  - utilities_group.py: ~100 lines ✓
  - address_group.py: ~120 lines ✓
  - slot_group.py: ~120 lines ✓
  - vehicle_group.py: ~125 lines ✓
  - service_group.py: ~130 lines ✓
- All should be under 150 lines

---

### Phase 4: Brain Integration into Workflows (Steps 41-50)

**Goal:** Wire brain nodes into workflows using existing brain infrastructure.

### Step 41: Integrate conflict_monitor into bargaining_group

**File:** `/backend/src/workflows/node_groups/bargaining_group.py`
**Principle:** Composition - add brain observation
**Action:** Add conflict_monitor.node() before response generation

**What to do:**

- Import `conflict_monitor` from `/backend/src/nodes/brain/conflict_monitor.py`
- Add node: `workflow.add_node("detect_conflict", conflict_monitor.node)`
- Add edge: `"detect_conflict" → "generate_response"`
- Brain detects bargaining/frustration patterns
- Target: Add 3 lines

### Step 42: Integrate conflict_monitor into cancellation_group

**File:** `/backend/src/workflows/node_groups/cancellation_group.py` (if exists)
**Principle:** Composition - add brain observation
**Action:** Add conflict detection for frustration

**What to do:**

- Add conflict_monitor.node() to detect user frustration
- If frustration detected, escalate to human
- Target: Add 5 lines

### Step 43: Integrate intent_predictor into profile_group

**File:** `/backend/src/workflows/node_groups/profile_group.py`
**Principle:** Composition - add brain prediction
**Action:** Predict next user action after profile collection

**What to do:**

- Import `intent_predictor` from `/backend/src/nodes/brain/intent_predictor.py`
- Add node after name/phone extraction: `workflow.add_node("predict_intent", intent_predictor.node)`
- Brain predicts: will user provide vehicle next? Or ask questions?
- Target: Add 3 lines

### Step 44: Integrate intent_predictor into service_group

**File:** `/backend/src/workflows/node_groups/service_group.py`
**Principle:** Composition - add brain prediction
**Action:** Predict slot preference patterns

**What to do:**

- Add intent_predictor.node() after service selection
- Brain predicts: preferred time of day, weekend vs weekday
- Target: Add 3 lines

### Step 45: Integrate response_proposer into booking_group

**File:** `/backend/src/workflows/node_groups/booking_group.py`
**Principle:** Composition - add brain response
**Action:** Let brain propose confirmation message in conscious mode

**What to do:**

- Import `response_proposer` from `/backend/src/nodes/brain/response_proposer.py`
- Before sending confirmation, check if brain has proposed_response
- If confidence > threshold and conscious mode, use brain's response
- Target: Add 5 lines

### Step 46: Integrate recall_memories into extract.py

**File:** `/backend/src/nodes/atomic/extract.py`
**Principle:** Open/Closed - enhance with memory
**Action:** Add memory recall for context

**What to do:**

- Import `recall_memories` from `/backend/src/nodes/brain/recall_memories.py`
- Before extraction, call recall_memories.node() to get past conversation patterns
- Provide memories as additional context to DSPy extractor
- Brain learns: "This user always books car wash on Saturdays"
- Target: Add 8 lines

### Step 47: Wire brain_router into existing_user_booking workflow

**File:** `/backend/src/workflows/existing_user_booking.py`
**Principle:** Composition - add brain routing
**Action:** Route to brain modes at workflow entry

**What to do:**

- Import `brain_router` from `/backend/src/core/brain_router.py`
- At workflow start: `mode = brain_router.select_mode(state)`
- Add conditional routing:
  - If "shadow": observe only, don't act
  - If "reflex": regex-first strategy
  - If "conscious": DSPy-first + brain actions
- Target: Add 10 lines

### Step 48: Wrap main workflow with brain observation

**File:** `/backend/src/workflows/existing_user_booking.py`
**Principle:** Dependency Inversion - inject brain observation
**Action:** Use brain_workflow wrapper from Step 9

**What to do:**

- Import `brain_workflow` wrapper
- Wrap compiled workflow: `app = brain_workflow.wrap(base_workflow.compile(), checkpointer)`
- Brain observes all node executions transparently
- Logs to RL gym for learning
- Target: Add 2 lines

### Step 49: Add brain metrics endpoint

**File:** `/backend/src/api/v1/brain.py` (NEW - 70 lines)
**Principle:** Interface Segregation
**Action:** Create brain metrics API endpoint

**What to do:**

- Create GET /api/v1/brain/metrics endpoint
- Returns JSON: `{ shadow_observations: 150, reflex_actions: 45, conscious_decisions: 12, learning_accuracy: 0.87 }`
- Uses existing brain_service.py to get stats
- Target: 70 lines

### Step 50: Create brain integration tests

**File:** `/backend/src/tests/integration/test_brain_modes.py` (NEW - 180 lines)
**Principle:** Testing
**Action:** Test all three brain modes

**What to do:**

- Test shadow mode: brain proposes actions, logs comparison with actual workflow, never acts (for RL Gym learning)
- Test reflex mode: regex-first extraction, template-only responses
- Test conscious mode: DSPy-first, brain can propose responses, customize messages
- Test toggle enforcement: `can_customize_template()` actually prevents customization when disabled
- Test extraction strategy: reflex uses regex first, conscious uses DSPy first
- Target: 180 lines

---

## Summary

**Files Created:** 18

- 4 domain extraction nodes (extract_slot_preference, extract_confirmation, extract_utilities, refactored extract_name)
- 4 message builders (addon, address, utilities, booking confirmation)
- 2 DSPy extractors (addon, utilities)
- 3 transformers (filter_slots, group_slots, calculate_price)
- 2 reusable handlers (selection_error_handler, resume_router)
- 2 brain integration files (observation_hook, brain_workflow)
- 1 API endpoint (brain metrics)

**Files Modified:** 16

- 6 atomic nodes (extract, send_message, call_api, validate, merge, read_model)
- 8 node groups (slot_preference, booking, addon, utilities, address, slot, vehicle, service)
- 1 brain config (brain_toggles)
- 1 workflow (existing_user_booking)

**Files Split:** 1

- call_api.py → 3 files (_call_api_retry, _call_api_helpers, call_api)

**Lines Reduced:** ~850 lines

- Node groups: -480 lines (removing inline logic)
- Atomic nodes: -137 lines (read_model validation removal)
- extract_name: -82 lines (using atomic extract.node())
- Message consolidation: -151 lines

**Lines Added:** ~1200 lines (new functionality)

- Domain nodes: +340 lines
- Message builders: +195 lines
- Transformers: +210 lines
- Brain integration: +250 lines
- Tests: +180 lines
- Brain wrapper: +170 lines

**Net Impact:** +350 lines, but:

- All files now under 150 lines ✓
- No duplication ✓
- Brain fully integrated ✓
- High test coverage ✓
- SOLID/DRY principles achieved ✓

---

## Quick Reference: Step-by-Step Execution Guide

**Each step is designed to be stateless and independent - can be executed by parallel agents.**

### Execution Order

1. **Phase 1** (Steps 1-10): Atomic layer - can execute Steps 1-7 in parallel, then 8-10
2. **Phase 2** (Steps 11-25): Domain layer - can execute Steps 11-20 in parallel, then 21-25
3. **Phase 3** (Steps 26-40): Node groups - must execute in sequence per file
4. **Phase 4** (Steps 41-50): Brain integration - can execute Steps 41-46 in parallel, then 47-50

### Step Format

Each step specifies:

- **File path** (absolute path to file)
- **Action** (CREATE new file | EDIT existing file | DELETE file)
- **Lines** (specific line numbers to modify)
- **What to write** (exact code or clear description)
- **Imports needed** (what to add to imports section)
- **Target line count** (verify after completion)

### Example of Prescriptive Step

```bash
Step 11: Create extract_slot_preference.py
FILE: /backend/src/nodes/extraction/extract_slot_preference.py
ACTION: CREATE new file
WRITE:
  """Slot preference extraction node - composes atomic extract.node()."""
  from nodes.atomic import extract
  from dspy_modules.extractors.slot_preference_extractor import SlotPreferenceExtractor
  from fallbacks.pattern_extractors import extract_time_range, extract_date

  def regex_fallback(message: str) -> dict:
      result = {}
      time_result = extract_time_range(message, TIME_RANGE_PATTERNS)
      if time_result:
          result["preferred_time_range"] = time_result.get("preferred_time_range")
      date_result = extract_date(message, DATE_PATTERNS)
      if date_result:
          result["preferred_date"] = date_result.get("preferred_date")
      return result if result else None

  async def node(state, timeout=None):
      return await extract.node(
          state,
          extractor=SlotPreferenceExtractor(),
          field_path="slot_preference",
          fallback_fn=regex_fallback,
          respect_brain_mode=True
      )
VERIFY: File is ~60 lines
```

---

## Parallel Execution Groups

### Group A (Execute in Parallel)

- Steps 1-7: Atomic node enhancements
- Steps 11-14: Domain extraction nodes
- Steps 15-18: Message builders
- Steps 19-20: DSPy extractors
- Steps 21-25: Transformers and handlers

### Group B (Execute in Sequence per File)

- Steps 26-29: booking_group.py refactoring (must be sequential)
- Steps 30-31: addon_group.py refactoring (must be sequential)
- Steps 32-33: utilities_group.py refactoring (must be sequential)
- Steps 34-35: address_group.py refactoring (must be sequential)
- Steps 36-37: slot_group.py refactoring (must be sequential)

### Group C (Execute in Parallel)

- Steps 41-46: Brain node integrations

### Group D (Execute in Sequence)

- Steps 47-50: Workflow-level brain integration (must be sequential)

---

## Critical Dependencies

**Before Step 26:** Must complete Steps 11, 15 (slot_preference extraction + message builder)
**Before Step 27:** Must complete Step 12 (confirmation extraction)
**Before Step 28:** Must complete Step 23 (price calculator)
**Before Step 30:** Must complete Step 15 (addon message builder)
**Before Step 31:** Must complete Step 19 (addon extractor)
**Before Step 32:** Must complete Step 17 (utilities message builder)
**Before Step 33:** Must complete Step 13 (utilities extraction)
**Before Step 36:** Must complete Step 21 (slot filter)
**Before Step 37:** Must complete Step 22 (slot grouper)
**Before Step 47:** Must complete Steps 1, 6, 9 (extract.py brain mode, brain_toggles, brain_workflow)

---

## Success Verification Checklist

After completing all 50 steps, verify:

### Line Count Compliance

- [ ] All atomic nodes < 200 lines (acceptable with 50-line overhead)
- [ ] All domain nodes < 100 lines
- [ ] All node groups < 150 lines
- [ ] All message builders < 60 lines
- [ ] All transformers < 90 lines

### Architecture Compliance

- [ ] Node groups have NO inline logic (only wiring)
- [ ] Domain nodes COMPOSE atomic nodes (no duplication)
- [ ] Message builders implement MessageBuilder Protocol
- [ ] Extractors implement Extractor Protocol
- [ ] Transformers implement Transformer Protocol

### Brain Integration

- [ ] Brain modes work: shadow, reflex, conscious
- [ ] Brain toggles control behavior (can_customize_template, etc.)
- [ ] Extraction strategy respects brain mode (regex-first vs DSPy-first)
- [ ] Brain observation logs all node executions
- [ ] Brain metrics endpoint returns valid data

### Testing

- [ ] All atomic node tests pass
- [ ] All node group integration tests pass
- [ ] All brain mode tests pass
- [ ] Extract with "I want to book on 29th december morning" works in all modes

### No Regressions

- [ ] Existing workflows still function
- [ ] API endpoints still respond correctly
- [ ] WAPI webhooks still process messages
- [ ] Frontend integration still works

---

This plan provides a clear roadmap to refactor WapiBot backend following SOLID, DRY, 100-line limit, composition over creation, Domain Driven Design, and Blender principles. Each step is small, stateless, and can be executed independently by parallel agents.

- Lines 55-87: `build_addon_message` → `/backend/src/nodes/message_builders/addon_selection.py` (30 lines)
- addon_group.py should compose: `send_message.node(state, AddonSelectionBuilder())`
- Reduces addon_group.py by ~80 lines of inline logic

### Step 4: Split call_api.py into protocol + implementation

**File:** `/backend/src/nodes/atomic/call_api.py`
**Principle:** Interface Segregation + 100-line limit
**Goal:** Split 255 lines into 3 files

**Details:**

- Extract to:
  - `call_api_protocol.py`: APIClient Protocol, types (40 lines)
  - `call_api_retry.py`: Retry decorator, exponential backoff (70 lines)
  - `call_api.py`: Core node using Protocol + retry (100 lines)
- Follows Dependency Inversion - depend on Protocol, not concrete implementations

### Step 5: Split read_model.py into read + validate

**File:** `/backend/src/nodes/atomic/read_model.py`
**Principle:** Single Responsibility + Composition over creation
**Goal:** Split 237 lines into 2 files

**Details:**

- Split to:
  - `read_model.py`: ONLY read data from sources (100 lines)
  - Use existing `validate.py` for Pydantic validation (already exists)
- Compose in workflows: `read_model.node()` → `validate.node()`

---

## Phase 2: Node Group Refactoring (Steps 6-15)

### Step 6: Extract slot_preference_group.py inline logic

**File:** `/backend/src/workflows/node_groups/slot_preference_group.py`
**Principle:** Blender design (node groups wire, don't implement)
**Goal:** Reduce from 237 to ~120 lines

**Details:**

- Remove 6+ inline function definitions
- Reuse `extract.node()` with DateExtractor, TimeExtractor
- Extract message builders to `message_builders/slot_preference_messages.py`
- slot_preference_group.py becomes ONLY workflow wiring

### Step 7: Extract slot_group.py inline logic

**File:** `/backend/src/workflows/node_groups/slot_group.py`
**Principle:** Single Responsibility + DRY
**Goal:** Reduce from 218 to ~130 lines

**Details:**

- Extract slot filtering → `/backend/src/nodes/transformers/slot_filter.py` (60 lines)
- Extract slot grouping → `/backend/src/nodes/transformers/slot_grouper.py` (70 lines)
- Use `transform.node()` to compose transformers
- slot_group.py becomes workflow wiring only

### Step 8: Extract address_group.py inline logic

**File:** `/backend/src/workflows/node_groups/address_group.py`
**Principle:** Composition over creation
**Goal:** Reduce from 215 to ~120 lines

**Details:**

- Reuse `extract.node()` with AddressExtractor
- Reuse `validate.node()` with AddressModel
- Extract message builders to `message_builders/address_messages.py`
- Compose atomic nodes instead of inline implementation

### Step 9: Extract utilities_group.py inline helpers

**File:** `/backend/src/workflows/node_groups/utilities_group.py`
**Principle:** Single Responsibility
**Goal:** Reduce from 178 to ~100 lines

**Details:**

- Extract utility functions to `/backend/src/utils/booking_utils.py` (50 lines)
- Keep ONLY workflow node definitions in utilities_group.py
- Utilities belong in utils/, not node_groups/

### Step 10: Refactor addon_group.py to use atomic extract

**File:** `/backend/src/workflows/node_groups/addon_group.py`
**Principle:** Composition over creation + DRY
**Goal:** Reduce from 264 to ~140 lines

**Details:**

- Replace inline `extract_addon_selection` with `extract.node(state, AddonExtractor(), "addon_selection")`
- Create `/backend/src/dspy_modules/extractors/addon_extractor.py` (40 lines)
- Compose: fetch_addons → show_options → extract.node() → validate

### Step 11: Create domain extraction nodes directory

**File:** `/backend/src/nodes/extraction/domain/`
**Principle:** Domain Driven Design
**Goal:** Organize domain-specific extractors (directory structure)

**Details:**

- Create:
  - `/backend/src/nodes/extraction/domain/__init__.py`
  - `/backend/src/nodes/extraction/domain/customer_extractor.py`
  - `/backend/src/nodes/extraction/domain/vehicle_extractor.py`
  - `/backend/src/nodes/extraction/domain/booking_extractor.py`
- These are CONFIGURATIONS of extract.node(), not new implementations

### Step 12: Create customer_extractor.py domain node

**File:** `/backend/src/nodes/extraction/domain/customer_extractor.py`
**Principle:** Domain Driven Design + Composition
**Goal:** 40 lines of customer-specific extraction configuration

**Details:**

- Composes extract.node() with NameExtractor, PhoneExtractor
- Defines customer-specific fallback functions
- Example: `extract_customer_name = lambda s: extract.node(s, NameExtractor(), "customer.first_name", regex_name_fallback)`

### Step 13: Create vehicle_extractor.py domain node

**File:** `/backend/src/nodes/extraction/domain/vehicle_extractor.py`
**Principle:** Domain Driven Design + Composition
**Goal:** 45 lines of vehicle-specific extraction configuration

**Details:**

- Composes extract.node() with VehicleBrandExtractor, VehicleModelExtractor, VehiclePlateExtractor
- Defines vehicle-specific fallback functions
- Reuses atomic extract.node() for each field

### Step 14: Create booking_extractor.py domain node

**File:** `/backend/src/nodes/extraction/domain/booking_extractor.py`
**Principle:** Domain Driven Design + Composition
**Goal:** 50 lines of booking-specific extraction configuration

**Details:**

- Composes extract.node() with DateExtractor, TimeExtractor, ServiceExtractor
- Defines booking-specific fallback functions
- Reuses atomic extract.node() for each field

### Step 15: Create confirmation_extractor.py domain node

**File:** `/backend/src/nodes/extraction/domain/confirmation_extractor.py`
**Principle:** DRY (currently inline in booking_group.py)
**Goal:** 35 lines of confirmation extraction

**Details:**

- Extract YES/NO confirmation logic from booking_group.py
- Use extract.node() with ConfirmationExtractor (DSPy module)
- Fallback to regex patterns (yes/no/confirm/cancel)
- Reusable across cancellation_group, bargaining_group

---

## Phase 3: Atomic Node Enhancements (Steps 16-25)

### Step 16: Add brain awareness to extract.py

**File:** `/backend/src/nodes/atomic/extract.py`
**Principle:** Open/Closed (extend without modifying core)
**Goal:** Add respect_brain_mode parameter (+20 lines, total 221 lines)

**Details:**

- Add parameter: `respect_brain_mode: bool = True`
- If brain_mode == "conscious" and brain has proposed_extraction, use brain's suggestion
- If brain_mode == "shadow", log extraction for learning
- Preserves backward compatibility

### Step 17: Add brain awareness to validate.py

**File:** `/backend/src/nodes/atomic/validate.py`
**Principle:** Open/Closed
**Goal:** Add respect_brain_mode parameter (+15 lines, total 181 lines)

**Details:**

- If brain detected validation conflict, use brain's correction
- Log validation failures to brain for learning
- Maintains existing behavior when brain disabled

### Step 18: Add brain awareness to send_message.py

**File:** `/backend/src/nodes/atomic/send_message.py`
**Principle:** Open/Closed
**Goal:** Add respect_brain_mode parameter (+25 lines, total 185 lines)

**Details:**

- If brain_mode == "conscious" and brain has proposed_response, use brain's message
- Apply personalization suggestions
- Log all sent messages to brain
- Template customization only in conscious mode

### Step 19: Add brain awareness to call_api.py

**File:** `/backend/src/nodes/atomic/call_api.py` (after Step 4 split)
**Principle:** Open/Closed
**Goal:** Add brain monitoring (+15 lines)

**Details:**

- Log API call start/end for latency tracking
- If brain detects slow API, suggest fallback strategies
- Brain learns API reliability patterns

### Step 20: Enhance transform.py with brain awareness

**File:** `/backend/src/nodes/atomic/transform.py`
**Principle:** Blender design
**Goal:** Add brain awareness (+10 lines, total 124 lines)

**Details:**

- Add brain logging for transformations
- Brain learns which transformations are frequently needed
- Used by slot_filter, slot_grouper

### Step 21: Create condition.py atomic node

**File:** `/backend/src/nodes/atomic/condition.py` (NEW)
**Principle:** Blender design
**Goal:** 80 lines for conditional routing with brain awareness

**Details:**

- Generic condition evaluation: `condition.node(state, predicate_fn, true_path, false_path)`
- Brain observes which conditions are frequently true/false
- Brain learns patterns: "Users usually skip addons for service X"
- Replaces inline if/else in node groups

### Step 22: Create response.py atomic node

**File:** `/backend/src/nodes/atomic/response.py` (NEW)
**Principle:** Blender design
**Goal:** 90 lines for response generation with brain personalization

**Details:**

- Composes send_message.node() with brain personalization
- Brain customizes templates based on conversation history
- Replaces inline response building across node groups
- Supports template-based, LLM-based, and hybrid responses

### Step 23: Create log.py atomic node

**File:** `/backend/src/nodes/atomic/log.py` (NEW)
**Principle:** Blender design
**Goal:** 60 lines for structured logging to brain

**Details:**

- Logs events to brain memory: decisions, extractions, API calls, errors
- Brain uses logs for reinforcement learning
- Replaces scattered logger.info() calls
- Structured format for brain analysis

### Step 24: Create checkpoint.py atomic node

**File:** `/backend/src/nodes/atomic/checkpoint.py` (NEW)
**Principle:** Blender design
**Goal:** 70 lines for milestone-based checkpointing

**Details:**

- Saves state at milestones: customer confirmed, slot selected, booking created
- Brain uses checkpoints to learn successful vs failed paths
- Enables conversation replay for debugging
- Triggers on milestone events or errors

### Step 25: Add brain routing to merge.py

**File:** `/backend/src/nodes/atomic/merge.py`
**Principle:** Open/Closed
**Goal:** Add brain merge strategy selection (+15 lines, total 198 lines)

**Details:**

- If brain_mode == "conscious", brain selects merge strategy (confidence, timestamp, LLM)
- Brain learns which merge strategy works best for each field
- Defaults to confidence-based merge when brain disabled

---

## Phase 4: Brain Integration (Steps 26-35)

### Step 26: Create brain-aware workflow wrapper

**File:** `/backend/src/workflows/brain_workflow.py` (NEW)
**Principle:** Dependency Inversion + Open/Closed
**Goal:** 90 lines for brain wrapper

**Details:**

- Wraps existing workflows with brain observation layer
- Before each node: brain observes state → logs decision
- After each node: brain analyzes result → learns
- Workflow code unchanged - brain injected via wrapper pattern

### Step 27: Integrate brain_router.py into main workflow

**File:** `/backend/src/workflows/existing_user_booking.py`
**Principle:** Composition
**Goal:** Add brain routing to workflow entry point (modify 15 lines)

**Details:**

- At workflow start: `mode = brain_router.select_mode(state)`
- Route based on mode: shadow/reflex/conscious
- brain_router.py already exists, just needs integration

### Step 28: Add brain toggle checks to atomic nodes

**Files:** `/backend/src/nodes/atomic/*.py` (8 files)
**Principle:** Open/Closed + Interface Segregation
**Goal:** Use brain_toggles.py in atomic nodes (modify 8 files)

**Details:**

- In send_message.py: check `brain_toggles.can_customize_template()`
- In extract.py: check `brain_toggles.is_brain_enabled()`
- In validate.py: check `brain_toggles.can_suggest_corrections()`
- Each atomic node adds 3-5 lines for toggle checks

### Step 29: Create brain observation hooks

**File:** `/backend/src/nodes/brain/observation_hook.py` (NEW)
**Principle:** Blender design
**Goal:** 80 lines for automatic brain observation

**Details:**

- Decorator: `@observe_with_brain` wraps any node
- Logs inputs, outputs, latency, errors to brain
- Brain builds dataset of successful vs failed executions
- Used in brain-aware workflow wrapper

### Step 30: Integrate conflict_monitor.py into workflow

**File:** `/backend/src/nodes/brain/conflict_monitor.py` (exists)
**Principle:** Composition
**Goal:** Add conflict monitoring to 2 node groups

**Details:**

- In bargaining_group.py: add conflict_monitor.node() before response
- In cancellation_group.py: add conflict_monitor.node() to detect frustration
- Detects: frustration, bargaining, confusion patterns

### Step 31: Integrate intent_predictor.py into workflow

**File:** `/backend/src/nodes/brain/intent_predictor.py` (exists)
**Principle:** Composition
**Goal:** Add intent prediction to 3 node groups

**Details:**

- After extract nodes, predict next user action
- In profile_group, service_group, vehicle_group: add intent_predictor.node()
- Brain learns: "After asking for name, 90% provide phone next"

### Step 32: Integrate personalize_message.py into send_message

**File:** `/backend/src/nodes/brain/personalize_message.py` (exists)
**Principle:** Composition
**Goal:** Compose personalize_message with send_message.node()

**Details:**

- In send_message.py, if brain_mode == "conscious":
  - Call personalize_message.node() before sending
  - Apply personalization (tone, formality, emoji usage)
- personalize_message learns from conversation history

### Step 33: Integrate response_proposer.py into response generation

**File:** `/backend/src/nodes/brain/response_proposer.py` (exists)
**Principle:** Composition
**Goal:** Use brain's proposed response in conscious mode (modify 4 node groups)

**Details:**

- In booking_group, slot_group, addon_group, service_group:
- Before building response, check if brain has proposed_response
- If confidence > threshold, use brain's response
- Brain learns which responses lead to booking completion

### Step 34: Integrate recall_memories.py for context

**File:** `/backend/src/nodes/brain/recall_memories.py` (exists)
**Principle:** Composition
**Goal:** Add memory recall before extraction nodes

**Details:**

- In extract.py, before calling extractor:
  - Call recall_memories.node() to get relevant past conversations
  - Provide memories as additional context
- Brain learns: "This user always books on weekends"

### Step 35: Create brain metrics dashboard endpoint

**File:** `/backend/src/api/v1/brain_metrics.py` (NEW)
**Principle:** Interface Segregation
**Goal:** 70 lines for brain performance monitoring

**Details:**

- GET /api/v1/brain/metrics: Returns brain stats
  - Shadow/reflex/conscious mode counts
  - Learning accuracy (RL gym results)
- Uses existing brain_service.py
- Enables production monitoring

---

## Phase 5: Message Builder Consolidation (Steps 36-40)

### Step 36: Audit and consolidate message_builders/

**File:** `/backend/src/nodes/message_builders/`
**Principle:** DRY
**Goal:** Document all message builders, identify duplicates

**Details:**

- Current: 17 builder files
- Identify duplicate patterns
- Create shared templates in message_builders/templates/
- Preparation for consolidation

### Step 37: Create base message builder Protocol

**File:** `/backend/src/nodes/message_builders/base.py` (NEW)
**Principle:** Interface Segregation + Liskov Substitution
**Goal:** 50 lines for MessageBuilder Protocol

**Details:**

- Define Protocol:

  ```python
  class MessageBuilder(Protocol):
      def __call__(self, state: BookingState) -> str: ...
  ```

- All message builders implement this Protocol
- Ensures consistent interface

### Step 38: Extract common message formatting to utils

**File:** `/backend/src/nodes/message_builders/formatting.py` (NEW)
**Principle:** DRY
**Goal:** 80 lines for shared formatting functions

**Details:**

- Extract patterns:
  - `format_price(amount)`: "₹1,500"
  - `format_date(date)`: "25th December 2025"
  - `format_time_slot(slot)`: "10:00 AM - 11:00 AM"
- Used by all message builders

### Step 39: Consolidate slot message builders

**File:** `/backend/src/nodes/message_builders/slot_messages.py`
**Principle:** DRY
**Goal:** Merge 3 slot builders into 1 file (100 lines)

**Details:**

- Merge:
  - grouped_slots.py (162 lines)
  - date_preference_menu.py (53 lines)
  - time_preference_menu.py (60 lines)
- Result: slot_messages.py with 3 classes
- Total reduction: 275 lines → 100 lines (175 lines saved)

### Step 40: Consolidate confirmation message builders

**File:** `/backend/src/nodes/message_builders/confirmation_messages.py`
**Principle:** DRY
**Goal:** Merge 2 confirmation builders into 1 file (70 lines)

**Details:**

- Merge:
  - booking_confirmation.py (109 lines)
  - date_confirmation.py (37 lines)
- Result: confirmation_messages.py with 2 classes
- Total reduction: 146 lines → 70 lines (76 lines saved)

---

## Phase 6: Testing and Validation (Steps 41-45)

**NOTE:** Protocol file creation steps removed per Blender architecture - Protocols stay inline in atomic nodes.

### Step 41: Create atomic node unit tests

**File:** `/backend/src/tests/unit/test_atomic_nodes.py` (NEW)
**Principle:** Testability
**Goal:** 200 lines of comprehensive tests

**Details:**

- Test each atomic node in isolation:
  - test_extract_node_with_dspy_success
  - test_extract_node_with_fallback
  - test_validate_node_success
  - test_call_api_node_with_retry
  - test_brain_awareness_in_conscious_mode
- Mock all external dependencies

### Step 42: Create node group integration tests

**File:** `/backend/src/tests/integration/test_node_groups.py` (NEW)
**Principle:** Composition testing
**Goal:** 250 lines of workflow tests

**Details:**

- Test complete node group flows:
  - test_booking_group_end_to_end
  - test_addon_group_with_brain
  - test_slot_preference_group_composition
- Verify nodes compose correctly
- Test brain integration in each mode

### Step 43: Create brain integration tests

**File:** `/backend/src/tests/integration/test_brain_integration.py` (NEW)
**Principle:** Brain learning validation
**Goal:** 180 lines of brain behavior tests

**Details:**

- Test brain modes:
  - test_shadow_mode_observes_only
  - test_reflex_mode_regex_first
  - test_conscious_mode_brain_acts
- Test brain toggle enforcement
- Test brain learning patterns

### Step 44: Update .env.txt and documentation

**File:** `/backend/.env.txt` and `/backend/CLAUDE.md`
**Principle:** Configuration + Documentation
**Goal:** Document brain modes and Blender architecture

**Details:**

- Update `.env.txt` with brain configuration:

  ```bash
  BRAIN_ENABLED=true
  BRAIN_MODE=shadow  # shadow | reflex | conscious
  REFLEX_REGEX_FIRST=true
  REFLEX_FAIL_FAST=false
  ```

- CLAUDE.md already updated with Blender architecture principles
- Document: "I want to book on 29th december morning" test scenario

### Step 45: Create refactoring summary documentation

**File:** `/backend/docs/REFACTORING_COMPLETE.md` (NEW - no line limit for docs)
**Principle:** Documentation
**Goal:** Document refactoring changes

**Details:**

- Document what changed:
  - Files deleted (extract_name.py - DRY violation)
  - Files split (call_api.py, read_model.py)
  - Files refactored (6 node groups reduced to <150 lines)
  - Brain integration (all 9 brain nodes wired)
  - NO Protocol files created (Blender principle - stay inline)
- Migration guide for developers
- Before/after metrics

---

## Impact Summary

### Lines of Code Reduction

- extract_name.py deleted: **-142 lines**
- booking_group.py split: **-167 lines** (357 → 190 across 4 files)
- Message builders consolidated: **-251 lines**
- Node groups refactored: **-280 lines**
- **Total reduction: ~840 lines** while adding functionality

### Files Reorganized

- **Deleted:** 1 (extract_name.py)
- **Split:** 5 (booking_group, addon_group, call_api, read_model, slot_preference_group)
- **Created:** 18 (Protocols, domain extractors, atomic nodes, brain integration)
- **Net:** +12 files (better organized, smaller, more testable)

### Principles Achieved

- ✅ **SOLID:** All atomic nodes follow Single Responsibility, depend on Protocols (DI)
- ✅ **DRY:** Eliminated duplication, consolidated message builders
- ✅ **100-line limit:** All files now < 150 lines (with 50-line overhead)
- ✅ **Composition:** Node groups wire atomic nodes, don't implement logic
- ✅ **DDD:** Domain extractors organized by business domain
- ✅ **Blender:** Atomic nodes are simple, composable building blocks

### Brain Integrations

- 10 brain nodes integrated into main workflow
- 3 brain modes operational (shadow, reflex, conscious)
- 9 brain toggles enforceable in atomic nodes
- Brain learning from all workflow executions

---

## Critical Files Reference

### Phase 1 (DRY Violations) - Most Critical

1. `/backend/src/nodes/extraction/extract_name.py` - DELETE
2. `/backend/src/workflows/node_groups/booking_group.py` - SPLIT
3. `/backend/src/nodes/atomic/call_api.py` - SPLIT
4. `/backend/src/nodes/atomic/read_model.py` - SPLIT
5. `/backend/src/workflows/node_groups/addon_group.py` - REFACTOR

### Phase 4 (Brain Integration) - Most Critical

1. `/backend/src/workflows/brain_workflow.py` - CREATE
2. `/backend/src/nodes/atomic/extract.py` - ENHANCE
3. `/backend/src/nodes/atomic/send_message.py` - ENHANCE
4. `/backend/src/core/brain_router.py` - INTEGRATE
5. `/backend/src/nodes/brain/observation_hook.py` - CREATE

---

## Execution Orders

**Phase 1 first** (Steps 1-5) - Fixes critical DRY violations and line count issues

**Phase 2 next** (Steps 6-15) - Refactors node groups to follow Blender pattern

**Phase 3 then** (Steps 16-25) - Enhances atomic nodes with brain awareness

**Phase 4 after** (Steps 26-35) - Integrates brain into workflows

**Phase 5 follows** (Steps 36-40) - Consolidates message builders

**Phase 6 finally** (Steps 41-45) - Testing and documentation

**Note:** Protocol file creation removed - follows Blender architecture (Protocols stay inline in atomic nodes)

This plan provides a clear roadmap to refactor WapiBot backend following SOLID, DRY, 100-line limit, and Blender Everything Nodes architecture.

---

## CRITICAL LEARNINGS (Bug Fixes & Patterns)

### Learning #1: LangGraph TypedDict Schema Enforcement (Dec 29, 2024)

**Bug:** Booking ID showed as "Unknown" despite being set correctly in code.

**Root Cause:** LangGraph **strictly enforces** TypedDict schema and **silently drops any fields not defined** in `BookingState`.

**Evidence:**

```python
# In booking_group.py - we set booking_id
result["booking_id"] = message.get("booking_id", "LIT-BK-HD-OT-291225-0025")
logger.info(f"Booking ID: {result.get('booking_id')}")  # Logs: "LIT-BK-HD-OT-291225-0025" ✅

# Next node reads it
booking_id = state.get("booking_id", "Unknown")
logger.info(f"Booking ID: {booking_id}")  # Logs: "Unknown" ❌
```

**Debug Output Revealed:**

```bash
DEBUG: State has booking_id key: False  ❌
DEBUG: booking_id value: None  ❌
DEBUG: booking_response value: {'booking_id': 'LIT-BK-HD-OT-291225-0025'}  ✅
```

**Why booking_response persisted but booking_id didn't:**

- `booking_response` was defined in `BookingState` TypedDict ✅
- `booking_id` was NOT defined → LangGraph dropped it ❌

**The Fix:**

```python
# In /backend/src/workflows/shared/state.py
class BookingState(TypedDict):
    # ... existing fields ...

    # Booking Result
    booking_api_response: Optional[Dict[str, Any]]  # ✅ ADD THIS
    booking_response: Optional[Dict[str, Any]]  # Already existed
    booking_id: Optional[str]  # ✅ ADD THIS - the missing field!
    booking_data: Optional[Dict[str, Any]]  # ✅ ADD THIS
```

**Key Lesson:**
> **EVERY field you use in LangGraph workflows MUST be defined in the BookingState TypedDict.**
>
> LangGraph will silently drop undefined fields during state serialization between nodes.
>
> The warning at line 16-17 of state.py is CRITICAL:
>
> ```python
> # IMPORTANT: All fields used in workflows MUST be defined here.
> # LangGraph drops undefined fields during state serialization!
> ```

**Prevention Checklist:**

- [ ] Before adding `state["new_field"] = value` in ANY node
- [ ] Check if `new_field` exists in `BookingState` TypedDict
- [ ] If not, add it with proper type annotation
- [ ] Add comment explaining what the field stores
- [ ] Restart backend to reload schema

**Common Mistake Pattern:**

```python
# ❌ WRONG - field not in TypedDict
result["custom_field"] = compute_something()
return result  # custom_field will be DROPPED!

# ✅ RIGHT - add to TypedDict first
# 1. Add to state.py:
#    custom_field: Optional[Any]  # Description
# 2. Then use it:
result["custom_field"] = compute_something()
return result  # custom_field persists ✅
```

**Related Files:**

- `/backend/src/workflows/shared/state.py` - The single source of truth
- `/backend/CLAUDE.md` lines 299-337 - BookingState documentation
- All node files that modify state

**Impact:** This bug caused 3 hours of debugging. Could have been prevented with TypedDict validation in CI/CD.

**Recommended Tooling:**

- Add mypy strict mode to catch undefined field access
- Add pre-commit hook to validate state field usage
- Create state field usage linter

---

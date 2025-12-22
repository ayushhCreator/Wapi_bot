# Enhanced User Story - WhatsApp Service Booking Chatbot

**Version:** 2.0  
**Target Development Time:** 24 hours (including testing)  
**Architecture:** Modular, SOLID & DRY compliant, 50-line modules max

---

## 1. Introduction & Context

### 1.1 Purpose

A production-ready WhatsApp chatbot for booking automotive services (one-time and subscription) that handles complex conversational flows with resilience, state management, and graceful error recovery.

### 1.2 Core Principles

- **Modular Architecture**: Maximum 50 lines per module
- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY Compliance**: No code duplication, centralized configuration
- **Absolute Imports**: Prevent circular dependencies and debugging hell
- **Fail-Safe Design**: Graceful degradation, no silent failures

---

## 2. User Flows & Scenarios

### 2.1 Primary Flow: New Service Booking

**Actors:** Customer (via WhatsApp), Chatbot System, Backend ERP

**Preconditions:** Customer has WhatsApp access, service is available

**Flow Steps:**

1. **Greeting & Intent Detection**
   - Customer: "Hi", "Hello ji", "Namaste", "Need car wash"
   - System: Detects greeting + booking intent
   - Response: Warm greeting + service introduction
   - **Pitfall Avoided**: Don't extract greetings as names (e.g., "Haan", "Hello" as first_name)

2. **Name Collection**
   - Customer provides name in various formats:
     - Single message: "I'm Rahul Kumar"
     - Split messages: "Rahul" → "Kumar"
     - With titles: "Mr. Amit Singh"
   - System: Extracts first_name, last_name, full_name
   - Validation: Rejects stopwords (hello, hi, haan, shukriya, thanks)
   - **Pitfall Avoided**: Handle split names across messages without re-asking

3. **Phone Number Collection**
   - Customer: "9876543210", "My number is 8888777766"
   - System: Validates 10-digit Indian format (6-9 prefix)
   - Normalization: Removes spaces, hyphens, +91 prefix
   - **Pitfall Avoided**: Don't accept "Unknown" or placeholder values

4. **Vehicle Details Collection**
   - **Scenario A - Combined Input:**
     - Customer: "Honda City, plate MH12AB1234"
     - System: Extracts brand, model, plate in one turn

   - **Scenario B - Sequential Input:**
     - Customer: "I have Honda City"
     - System: "Great! What's the registration number?"
     - Customer: "MH12AB1234"
     - System: Extracts plate in follow-up

   - **Pitfall Avoided**:
     - Don't get stuck asking for plate when already provided
     - Handle 50% combined, 50% sequential naturally
     - Prevent race conditions between chat and button inputs

5. **Service Type & Date Selection**
   - Customer: "Full car wash", "Tomorrow morning", "Next Monday 10am"
   - System:
     - Fetches available services via API
     - Parses date (relative: tomorrow, next week; absolute: 2025-01-15)
     - Validates date is not in past
   - **Pitfall Avoided**: Don't accept invalid dates (Feb 30, past dates)

6. **Scratchpad Completeness Check**
   - System calculates completeness: (fields_collected / total_required) * 100
   - Required fields (12/16): first_name, last_name, phone, brand, model, plate, date, service_type
   - Optional fields (4/16): time_slot, notes, tier, address
   - Threshold: 75% (12 fields) triggers confirmation

7. **Confirmation Flow**
   - System: Displays booking summary
   - Customer options:
     - **Confirm**: "Yes", "Confirm", "Book it"
     - **Edit**: "Change name to Priya", "Edit phone 9999888877"
     - **Cancel**: "Cancel booking", "I changed my mind"
   - **Pitfall Avoided**:
     - Allow edits without restarting entire flow
     - Handle typos: "confrim bokking" → suggest correction
     - Prevent data overwrite during edits

8. **Booking Creation**
   - System calls Frappe API: `create_booking`
   - Payload: customer, vehicle, service, date, addons
   - Response: Service Request ID (SR-XXXXXXXX)
   - WhatsApp: Send confirmation via WAPI `send-message`

9. **Post-Booking**
   - System: "Booking confirmed! SR-ABC123. See you on Jan 15 at 10 AM"
   - State: COMPLETED
   - Cleanup: Archive conversation, reset scratchpad

---

### 2.2 Secondary Flows

#### 2.2.1 Negotiation & Bargaining

**Scenario:** Customer negotiates price before booking

**Flow:**

1. Customer: "What's the rate?"
2. System: Fetches pricing via `calculate_booking_price` API
3. Customer: "Too costly, can you reduce?"
4. System: "We offer 10% discount for first-time customers"
5. Customer: "Okay fine, book it"
6. → Proceeds to name collection

**Pitfall Avoided**: Don't lose context during price discussion

---

#### 2.2.2 Rescheduling During Booking

**Scenario:** Customer changes date mid-flow

**Flow:**

1. Customer provides date: "Tomorrow morning"
2. System: "Slot booked for Jan 15, 10 AM"
3. Customer: "Wait, change to Friday"
4. System: Updates scratchpad, re-validates slot availability
5. → Continues to confirmation

**Pitfall Avoided**: Don't create duplicate bookings, handle state transitions cleanly

---

#### 2.2.3 Indecisive Customer

**Scenario:** Customer gets frustrated, then re-engages

**Flow:**

1. Customer: "Wait, I'm confused"
2. System: Detects low interest sentiment (boredom: 7/10)
3. System: "No worries! Let me simplify. Just need your name and car details"
4. Customer: "This is too complicated"
5. System: Detects high frustration (anger: 8/10)
6. System: "I understand. Would you like to continue or call us instead?"
7. Customer: "Okay okay, continue"
8. System: Re-engages with simplified questions

**Pitfall Avoided**: Don't abandon conversation, provide escape routes

---

#### 2.2.4 Error Recovery - Spelling Mistakes

**Scenario:** Customer makes typos

**Flow:**

1. Customer: "confrim bokking" (typos)
2. System: Detects typos via DSPy signature
3. System: "Did you mean 'confirm booking'? (Yes/No)"
4. Customer: "Yes"
5. → Proceeds to confirmation

**Pitfall Avoided**: Don't fail silently on typos, suggest corrections

---

#### 2.2.5 Cancel & Restart

**Scenario:** Customer cancels then decides to book again

**Flow:**

1. Customer: "Cancel this booking"
2. System: "Booking cancelled. Can I help with anything else?"
3. Customer: "Actually, I want to book again"
4. System: Resets scratchpad, starts fresh
5. → Greeting state

**Pitfall Avoided**: Don't retain stale data from cancelled booking

---

### 2.3 New Flow: API-Based Product & Service Fetching

**Integration Point:** Frappe ERP APIs

#### 2.3.1 Service Discovery

**API:** `get_filtered_services`

**Flow:**

1. Customer: "Show me car wash services"
2. System calls API:

   ```json
   {
     "category": "Car Wash",
     "frequency_type": "One Time",
     "vehicle_type": "Sedan"
   }
   ```

3. API returns:

   ```json
   {
     "success": true,
     "services": [
       {
         "name": "SRV-001",
         "product_name": "Premium Wash",
         "base_price": 499.0,
         "included_addons": [...]
       }
     ]
   }
   ```

4. System: "We have Premium Wash (₹499) with interior vacuum included"

**Pitfall Avoided**: Cache API responses (5 min TTL) to prevent rate limiting

---

#### 2.3.2 Add-on Selection

**API:** `get_optional_addons`

**Flow:**

1. System: "Would you like wax polish (₹199) or ceramic coating (₹999)?"
2. Customer: "Add wax polish"
3. System updates scratchpad: `addons: [{addon: "ADD-005", quantity: 1}]`

---

#### 2.3.3 Slot Availability Check

**API:** `get_available_slots_enhanced`

**Flow:**

1. Customer: "Tomorrow morning"
2. System calls API: `date_str: "2025-01-15"`
3. API returns available slots:

   ```json
   {
     "slots": [
       {
         "slot_id": "09:00-10:00",
         "available_capacity": 3
       }
     ]
   }
   ```

4. System: "Available slots: 9-10 AM (3 spots), 11-12 PM (1 spot)"

**Pitfall Avoided**: Atomic slot locking via `check_slot_availability` before booking

---

#### 2.3.4 Dynamic Pricing

**API:** `calculate_booking_price`

**Flow:**

1. System calculates total:
   - Base: ₹499
   - Addons: ₹199
   - Surcharges: ₹150 (water not provided)
   - Total: ₹848
2. Customer: "I'll provide water"
3. System recalculates: ₹698 (surcharge removed)

---

### 2.4 New Flow: WAPI WhatsApp Control

**Integration Point:** WAPI Endpoints (wapi_endpioints.md)

#### 2.4.1 Send Text Message

**Endpoint:** `POST /contact/send-message`

**Usage:**

```python
# Module: wapibot/integrations/wapi/message_sender.py
def send_text(phone: str, message: str):
    payload = {
        "phone_number": phone,
        "message_body": message,
        "contact": {
            "first_name": scratchpad.first_name,
            "last_name": scratchpad.last_name
        }
    }
    response = requests.post(f"{WAPI_BASE}/send-message", json=payload)
```

---

#### 2.4.2 Send Interactive Buttons

**Endpoint:** `POST /contact/send-interactive-message`

**Usage:**

```python
# Confirmation screen with buttons
def send_confirmation_buttons(phone: str, summary: str):
    payload = {
        "phone_number": phone,
        "interactive_type": "button",
        "body_text": summary,
        "buttons": [
            {"id": "confirm", "title": "✅ Confirm"},
            {"id": "edit", "title": "✏️ Edit"},
            {"id": "cancel", "title": "❌ Cancel"}
        ]
    }
```

**Pitfall Avoided**: Handle button clicks and text responses in parallel (race condition prevention)

---

#### 2.4.3 Send Template Message

**Endpoint:** `POST /contact/send-template-message`

**Usage:**

```python
# Booking confirmation template
def send_booking_confirmation(phone: str, sr_id: str, date: str):
    payload = {
        "phone_number": phone,
        "template_name": "booking_confirmation",
        "template_language": "en",
        "field_1": sr_id,
        "field_2": date
    }
```

---

#### 2.4.4 Send Media (Invoice/Receipt)

**Endpoint:** `POST /contact/send-media-message`

**Usage:**

```python
# Send invoice PDF
def send_invoice(phone: str, invoice_url: str):
    payload = {
        "phone_number": phone,
        "media_type": "document",
        "media_url": invoice_url,
        "file_name": f"Invoice_{sr_id}.pdf"
    }
```

---

## 3. Critical Pitfalls & Avoidance Strategies

### 3.1 Pitfalls from conversation_simulator_v2.py

#### Pitfall 1: State Lock in Name/Address Collection

**Problem:** System gets stuck asking for name repeatedly

**Root Cause:**

- Scratchpad not updating after extraction
- State transition logic doesn't check completeness

**Solution:**

```python
# Module: wapibot/core/state/transition_validator.py (max 50 lines)
def can_transition(from_state, to_state, scratchpad):
    if from_state == "name_collection":
        return scratchpad.has_name()  # Check actual data
    return True
```

---

#### Pitfall 2: Data Overwrite During Edits

**Problem:** Editing phone number overwrites entire scratchpad

**Root Cause:**

- Scratchpad update logic replaces instead of merging

**Solution:**

```python
# Module: wapibot/core/data/scratchpad_merger.py (max 50 lines)
def merge_update(scratchpad, new_data):
    for key, value in new_data.items():
        if value is not None:  # Only update non-null
            scratchpad[key] = value
```

---

#### Pitfall 3: Race Condition (Chat vs Button)

**Problem:** User clicks button while typing message → duplicate bookings

**Root Cause:**

- No locking mechanism between /chat and /api/confirmation

**Solution:**

```python
# Module: wapibot/core/locks/conversation_lock.py (max 50 lines)
import redis
lock_client = redis.Redis()

def acquire_lock(conv_id, timeout=5):
    return lock_client.set(f"lock:{conv_id}", "1", nx=True, ex=timeout)
```

---

#### Pitfall 4: Silent LLM Failures

**Problem:** DSPy extraction fails, system continues with empty data

**Root Cause:**

- No validation after LLM calls
- Exceptions swallowed

**Solution:**

```python
# Module: wapibot/core/llm/extraction_validator.py (max 50 lines)
def validate_extraction(result):
    if not result or result.confidence < 0.5:
        raise ExtractionError("Low confidence extraction")
    return result
```

---

#### Pitfall 5: Network Timeout Cascades

**Problem:** API timeout causes entire conversation to fail

**Root Cause:**

- No retry logic
- No fallback responses

**Solution:**

```python
# Module: wapibot/integrations/api/retry_handler.py (max 50 lines)
@retry(max_attempts=3, backoff=2)
def call_api(endpoint, payload):
    try:
        return requests.post(endpoint, json=payload, timeout=5)
    except Timeout:
        return fallback_response()
```

---

### 3.2 Additional Pitfalls to Avoid

#### Pitfall 6: Typo Detection Not Working

**Problem:** System doesn't suggest corrections for "confrim bokking"

**Solution:**

```python
# Module: wapibot/core/nlp/typo_detector.py (max 50 lines)
from dspy import Signature, ChainOfThought

class TypoDetector(Signature):
    user_input = dspy.InputField()
    has_typo = dspy.OutputField(desc="true/false")
    correction = dspy.OutputField(desc="corrected text")
```

---

#### Pitfall 7: Scratchpad Completeness Miscalculation

**Problem:** System shows 100% complete with only 5 fields

**Solution:**

```python
# Module: wapibot/core/data/completeness_calculator.py (max 50 lines)
REQUIRED_FIELDS = 12
TOTAL_FIELDS = 16

def calculate_completeness(scratchpad):
    filled = sum(1 for f in scratchpad.values() if f is not None)
    return (filled / REQUIRED_FIELDS) * 100
```

---

## 4. System Architecture & Modularization

### 4.1 Folder Structure (Absolute Imports)

```bash
wapibot/
├── core/
│   ├── state/
│   │   ├── __init__.py
│   │   ├── state_machine.py          # 50 lines: State enum + transitions
│   │   ├── transition_validator.py   # 50 lines: Validate state changes
│   │   └── state_persister.py        # 50 lines: Save/load state
│   ├── data/
│   │   ├── __init__.py
│   │   ├── scratchpad.py             # 50 lines: Scratchpad model
│   │   ├── scratchpad_merger.py      # 50 lines: Merge updates
│   │   ├── completeness_calculator.py # 50 lines: Calculate %
│   │   └── validator.py              # 50 lines: Field validation
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── dspy_client.py            # 50 lines: DSPy setup
│   │   ├── extraction_validator.py   # 50 lines: Validate LLM output
│   │   └── retry_handler.py          # 50 lines: Retry logic
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── typo_detector.py          # 50 lines: Detect typos
│   │   ├── intent_classifier.py      # 50 lines: Classify intent
│   │   └── sentiment_analyzer.py     # 50 lines: Analyze sentiment
│   └── locks/
│       ├── __init__.py
│       └── conversation_lock.py      # 50 lines: Redis locks
├── integrations/
│   ├── frappe/
│   │   ├── __init__.py
│   │   ├── service_fetcher.py        # 50 lines: get_filtered_services
│   │   ├── addon_fetcher.py          # 50 lines: get_optional_addons
│   │   ├── slot_checker.py           # 50 lines: get_available_slots
│   │   ├── price_calculator.py       # 50 lines: calculate_booking_price
│   │   └── booking_creator.py        # 50 lines: create_booking
│   └── wapi/
│       ├── __init__.py
│       ├── message_sender.py         # 50 lines: send-message
│       ├── interactive_sender.py     # 50 lines: send-interactive
│       ├── template_sender.py        # 50 lines: send-template
│       └── media_sender.py           # 50 lines: send-media
├── orchestrators/
│   ├── __init__.py
│   ├── chat_orchestrator.py          # 50 lines: Main /chat handler
│   ├── confirmation_orchestrator.py  # 50 lines: /api/confirmation handler
│   └── extraction_orchestrator.py    # 50 lines: Coordinate extractions
├── models/
│   ├── __init__.py
│   ├── scratchpad_model.py           # 50 lines: Pydantic model
│   ├── customer_model.py             # 50 lines: Customer fields
│   ├── vehicle_model.py              # 50 lines: Vehicle fields
│   └── appointment_model.py          # 50 lines: Appointment fields
├── config/
│   ├── __init__.py
│   ├── settings.py                   # 50 lines: Global config
│   └── constants.py                  # 50 lines: Constants
└── utils/
    ├── __init__.py
    ├── logger.py                     # 50 lines: Logging setup
    └── error_handler.py              # 50 lines: Global error handler
```

---

### 4.2 Naming Conventions

#### Files & Folders

- **Folders**: `snake_case` (e.g., `state_machine/`, `data_models/`)
- **Files**: `snake_case.py` (e.g., `scratchpad_merger.py`)
- **Test Files**: `test_<module>.py` (e.g., `test_scratchpad_merger.py`)

#### Classes

- **PascalCase**: `ScratchpadMerger`, `StateTransitionValidator`
- **Pydantic Models**: `<Entity>Model` (e.g., `CustomerModel`, `VehicleModel`)

#### Functions

- **snake_case**: `calculate_completeness()`, `merge_update()`
- **Private**: `_internal_helper()`

#### Variables

- **snake_case**: `scratchpad_data`, `user_message`
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `API_TIMEOUT`)

#### Modules

- **Descriptive**: `wapibot.core.state.transition_validator`
- **Absolute Imports**: `from wapibot.core.state.transition_validator import validate_transition`

---

### 4.3 SOLID & DRY Examples

#### Single Responsibility Principle

```python
# ❌ BAD: One class does everything
class BookingHandler:
    def extract_data(self): ...
    def validate_data(self): ...
    def call_api(self): ...
    def send_whatsapp(self): ...

# ✅ GOOD: Separate responsibilities
class DataExtractor:
    def extract(self): ...

class DataValidator:
    def validate(self): ...

class APIClient:
    def call(self): ...

class WhatsAppSender:
    def send(self): ...
```

---

#### DRY Principle

```python
# ❌ BAD: Repeated validation logic
def validate_name(name):
    if not name or len(name) < 2:
        raise ValueError("Invalid name")

def validate_phone(phone):
    if not phone or len(phone) != 10:
        raise ValueError("Invalid phone")

# ✅ GOOD: Centralized validation
# File: wapibot/core/data/validator.py
class FieldValidator:
    @staticmethod
    def validate(field, value, rules):
        if not value:
            raise ValueError(f"Missing {field}")
        if "min_length" in rules and len(value) < rules["min_length"]:
            raise ValueError(f"{field} too short")
```

---

## 5. Data Models (Modularized & SOLID)

### 5.1 Scratchpad Model

```python
# File: wapibot/models/scratchpad_model.py (50 lines max)
from pydantic import BaseModel, Field
from typing import Optional

class ScratchpadModel(BaseModel):
    # Customer section
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    
    # Vehicle section
    vehicle_brand: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_plate: Optional[str] = None
    
    # Appointment section
    appointment_date: Optional[str] = None
    service_type: Optional[str] = None
    time_slot: Optional[str] = None
    notes: Optional[str] = None
    
    # Optional enhancements
    service_tier: Optional[str] = None
    address: Optional[str] = None
    addons: list = Field(default_factory=list)
    
    def has_name(self) -> bool:
        return bool(self.first_name and self.last_name)
    
    def has_vehicle(self) -> bool:
        return bool(self.vehicle_brand and self.vehicle_plate)
    
    def completeness(self) -> float:
        filled = sum(1 for v in self.dict().values() if v)
        return (filled / 16) * 100  # 16 total fields
```

---

### 5.2 Customer Model

```python
# File: wapibot/models/customer_model.py (50 lines max)
from pydantic import BaseModel, validator

class CustomerModel(BaseModel):
    first_name: str
    last_name: str
    phone: str
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Invalid phone")
        return v
```

---

### 5.3 Vehicle Model

```python
# File: wapibot/models/vehicle_model.py (50 lines max)
from pydantic import BaseModel, validator

class VehicleModel(BaseModel):
    brand: str
    model: str
    plate: str
    
    @validator('plate')
    def validate_plate(cls, v):
        # Indian format: MH12AB1234
        if not v or len(v) < 8:
            raise ValueError("Invalid plate")
        return v.upper()
```

---

## 6. Testing Strategy (24-Hour Timeline)

### 6.1 Unit Tests (8 hours)

- Test each 50-line module independently
- Mock external dependencies (APIs, Redis)
- Coverage target: 80%

### 6.2 Integration Tests (6 hours)

- Test API integrations (Frappe, WAPI)
- Test state transitions
- Test scratchpad updates

### 6.3 E2E Tests (6 hours)

- Run conversation_simulator_v2.py scenarios
- Validate all 7 scenarios pass
- Check typo detection, error recovery

### 6.4 Load Tests (2 hours)

- Simulate 100 concurrent conversations
- Verify no race conditions
- Check Redis lock performance

### 6.5 Manual QA (2 hours)

- Test on real WhatsApp
- Verify button interactions
- Check template messages

---

## 7. Deployment Checklist

### 7.1 Pre-Deployment

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] E2E scenarios pass (7/7)
- [ ] Load tests pass (100 concurrent)
- [ ] Code review completed
- [ ] Documentation updated

### 7.2 Configuration

- [ ] Environment variables set (.env)
- [ ] Redis connection configured
- [ ] Frappe API credentials set
- [ ] WAPI credentials set
- [ ] DSPy model downloaded (gemma3:4b)

### 7.3 Monitoring

- [ ] Logging enabled (INFO level)
- [ ] Error tracking (Sentry/similar)
- [ ] Metrics dashboard (Grafana/similar)
- [ ] Alert rules configured

---

## 8. Success Metrics

### 8.1 Functional Metrics

- **Booking Completion Rate**: >85%
- **Error Recovery Rate**: >90% (typos, retries)
- **State Lock Incidents**: 0
- **Data Overwrite Incidents**: 0

### 8.2 Performance Metrics

- **Response Time**: <2s (p95)
- **API Timeout Rate**: <1%
- **Concurrent Conversations**: 100+
- **Uptime**: >99.5%

### 8.3 User Experience Metrics

- **Conversation Abandonment**: <15%
- **Edit Requests**: <10% of bookings
- **Cancellation Rate**: <5%
- **Customer Satisfaction**: >4.5/5

---

## 9. Appendix

### 9.1 API Reference

- **Frappe APIs**: See `docs/frappe_api.md`
- **WAPI Endpoints**: See `docs/wapi_endpioints.md`

### 9.2 State Machine Diagram

```bash
GREETING → NAME_COLLECTION → VEHICLE_DETAILS → DATE_SELECTION → CONFIRMATION → COMPLETED
    ↓           ↓                  ↓                 ↓                ↓
CANCELLED ← CANCELLED ←  CANCELLED ←  CANCELLED ← CANCELLED
```

### 9.3 Example Conversations

- See `example/tests/conversation_simulator_v2.py` for 7 realistic scenarios

---

**Document Version:** 2.0  
**Last Updated:** 2025-01-XX  
**Maintained By:** Development Team

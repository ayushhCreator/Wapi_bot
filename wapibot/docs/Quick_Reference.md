# Quick Reference Guide - WhatsApp Chatbot

**For:** Developers implementing the system  
**Time to Read:** 5 minutes

---

## 🎯 Core Flows (What Users Do)

### 1. Happy Path Booking (90% of users)
```
User: "Hi, need car wash"
Bot: "Hello! I'm here to help. What's your name?"
User: "Rahul Kumar"
Bot: "Great! What's your phone number?"
User: "9876543210"
Bot: "Perfect! What car do you have?"
User: "Honda City, plate MH12AB1234"
Bot: "When would you like the service?"
User: "Tomorrow morning"
Bot: "📋 Booking Summary: Rahul Kumar, Honda City (MH12AB1234), Jan 15 10AM. Confirm?"
User: "Yes"
Bot: "✅ Booked! SR-ABC123"
```

### 2. Negotiation Flow (5% of users)
```
User: "What's the price?"
Bot: "₹499 for Premium Wash"
User: "Too costly, discount?"
Bot: "10% off for first-time: ₹449"
User: "Okay, book it"
→ Proceeds to name collection
```

### 3. Error Recovery (3% of users)
```
User: "confrim bokking" (typo)
Bot: "Did you mean 'confirm booking'?"
User: "Yes"
→ Proceeds to confirmation
```

### 4. Edit During Confirmation (2% of users)
```
Bot: "Confirm booking for Rahul?"
User: "Wait, change name to Priya"
Bot: "Updated! Confirm booking for Priya?"
User: "Yes"
→ Creates booking
```

---

## 🏗️ Architecture (How It Works)

### Module Structure (50 lines max per file)
```
wapibot/
├── core/
│   ├── state/          # State machine logic
│   ├── data/           # Scratchpad & validation
│   ├── llm/            # DSPy extraction
│   ├── nlp/            # Typo, intent, sentiment
│   └── locks/          # Race condition prevention
├── integrations/
│   ├── frappe/         # ERP API calls
│   └── wapi/           # WhatsApp API calls
├── orchestrators/      # Main handlers
├── models/             # Pydantic models
└── config/             # Settings
```

### Key Modules (What Each Does)

| Module | Purpose | Lines |
|--------|---------|-------|
| `state_machine.py` | Define states & transitions | 50 |
| `scratchpad.py` | Store user data | 50 |
| `scratchpad_merger.py` | Merge updates (no overwrite) | 50 |
| `completeness_calculator.py` | Calculate % complete | 50 |
| `typo_detector.py` | Detect & suggest corrections | 50 |
| `conversation_lock.py` | Prevent race conditions | 50 |
| `service_fetcher.py` | Fetch services from Frappe | 50 |
| `message_sender.py` | Send WhatsApp messages | 50 |

---

## 🚨 Critical Pitfalls (What NOT to Do)

### ❌ Pitfall 1: State Lock
**Problem:** System asks for name 5 times  
**Cause:** Not checking if data already exists  
**Fix:**
```python
def can_transition(from_state, scratchpad):
    if from_state == "name_collection":
        return scratchpad.has_name()  # Check data!
```

### ❌ Pitfall 2: Data Overwrite
**Problem:** Editing phone deletes name  
**Cause:** Replacing entire scratchpad  
**Fix:**
```python
def merge_update(scratchpad, new_data):
    for key, value in new_data.items():
        if value is not None:  # Only update non-null
            scratchpad[key] = value
```

### ❌ Pitfall 3: Race Condition
**Problem:** User clicks button + types → 2 bookings  
**Cause:** No locking between /chat and /api/confirmation  
**Fix:**
```python
import redis
lock = redis.Redis()
if lock.set(f"lock:{conv_id}", "1", nx=True, ex=5):
    # Process request
    pass
```

### ❌ Pitfall 4: Silent LLM Failure
**Problem:** Extraction fails, system continues  
**Cause:** No validation after DSPy call  
**Fix:**
```python
result = dspy_extract(message)
if not result or result.confidence < 0.5:
    raise ExtractionError("Low confidence")
```

### ❌ Pitfall 5: API Timeout
**Problem:** Frappe API times out → conversation dies  
**Cause:** No retry logic  
**Fix:**
```python
@retry(max_attempts=3, backoff=2)
def call_api(endpoint, payload):
    return requests.post(endpoint, json=payload, timeout=5)
```

---

## 📊 Data Models (What to Store)

### Scratchpad (16 fields total)
```python
{
    # Customer (4 fields)
    "first_name": "Rahul",
    "last_name": "Kumar",
    "full_name": "Rahul Kumar",
    "phone": "9876543210",
    
    # Vehicle (3 fields)
    "vehicle_brand": "Honda",
    "vehicle_model": "City",
    "vehicle_plate": "MH12AB1234",
    
    # Appointment (4 fields)
    "appointment_date": "2025-01-15",
    "service_type": "Premium Wash",
    "time_slot": "early_morning",
    "notes": "Please call before arriving",
    
    # Optional (5 fields)
    "service_tier": "Premium",
    "address": "123 Main St",
    "addons": [{"addon": "ADD-005", "quantity": 1}],
    "electricity_provided": true,
    "water_provided": false
}
```

### Completeness Calculation
```python
REQUIRED_FIELDS = 12  # Minimum to book
TOTAL_FIELDS = 16     # All fields

completeness = (filled_fields / REQUIRED_FIELDS) * 100
# Trigger confirmation at 75% (12 fields)
```

---

## 🔌 API Integrations

### Frappe ERP APIs
```python
# 1. Get Services
GET /api/customer_portal.get_filtered_services
→ Returns: List of services with prices

# 2. Get Add-ons
GET /api/booking.get_optional_addons?product_id=SRV-001
→ Returns: Optional add-ons (wax, polish, etc.)

# 3. Check Slots
GET /api/booking.get_available_slots_enhanced?date_str=2025-01-15
→ Returns: Available time slots

# 4. Calculate Price
POST /api/booking.calculate_booking_price
→ Returns: Total price with surcharges

# 5. Create Booking
POST /api/booking.create_booking
→ Returns: Service Request ID (SR-XXXXXXXX)
```

### WAPI WhatsApp APIs
```python
# 1. Send Text
POST /contact/send-message
Body: {"phone_number": "9876543210", "message_body": "Hello!"}

# 2. Send Buttons
POST /contact/send-interactive-message
Body: {"interactive_type": "button", "buttons": [...]}

# 3. Send Template
POST /contact/send-template-message
Body: {"template_name": "booking_confirmation", "field_1": "SR-123"}

# 4. Send Media
POST /contact/send-media-message
Body: {"media_type": "document", "media_url": "https://..."}
```

---

## 🧪 Testing (24-Hour Timeline)

### Hour 0-8: Unit Tests
```bash
pytest tests/unit/ -v
# Test each 50-line module
# Mock external dependencies
```

### Hour 8-14: Integration Tests
```bash
pytest tests/integration/ -v
# Test API calls (Frappe, WAPI)
# Test state transitions
```

### Hour 14-20: E2E Tests
```bash
python tests/conversation_simulator_v2.py
# Run 7 realistic scenarios
# Verify typo detection, error recovery
```

### Hour 20-22: Load Tests
```bash
locust -f tests/load_test.py --users 100
# Simulate 100 concurrent conversations
# Check for race conditions
```

### Hour 22-24: Manual QA
- Test on real WhatsApp
- Verify button clicks
- Check template messages

---

## 📝 Naming Conventions

### Files & Folders
```
snake_case/
├── scratchpad_merger.py
├── state_machine.py
└── test_scratchpad_merger.py
```

### Classes
```python
class ScratchpadMerger:  # PascalCase
class CustomerModel(BaseModel):  # Pydantic models
```

### Functions
```python
def calculate_completeness():  # snake_case
def _internal_helper():  # Private with underscore
```

### Variables
```python
scratchpad_data = {}  # snake_case
MAX_RETRIES = 3  # Constants in UPPER_SNAKE_CASE
```

### Imports
```python
# ✅ GOOD: Absolute imports
from wapibot.core.state.transition_validator import validate_transition

# ❌ BAD: Relative imports
from ..state.transition_validator import validate_transition
```

---

## 🎯 Success Metrics

### Must-Have (Launch Blockers)
- ✅ Booking completion rate >85%
- ✅ Error recovery rate >90%
- ✅ Zero state lock incidents
- ✅ Zero data overwrite incidents
- ✅ Response time <2s (p95)

### Nice-to-Have (Post-Launch)
- 📈 Conversation abandonment <15%
- 📈 Edit requests <10%
- 📈 Cancellation rate <5%
- 📈 Customer satisfaction >4.5/5

---

## 🚀 Quick Start Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
docker run -d -p 6379:6379 redis

# Start Ollama (for DSPy)
ollama serve
ollama pull gemma3:4b

# Set environment variables
cp .env.example .env
# Edit .env with API keys
```

### Run
```bash
# Start chatbot server
python main.py

# Run tests
pytest tests/ -v

# Run E2E simulator
python tests/conversation_simulator_v2.py
```

---

## 📚 Documentation Links

- **Full User Story**: `docs/Users_Story_Enhanced.md`
- **Frappe APIs**: `docs/frappe_api.md`
- **WAPI Endpoints**: `docs/wapi_endpioints.md`
- **Example Conversations**: `example/tests/conversation_simulator_v2.py`

---

**Last Updated:** 2025-01-XX  
**Questions?** Check the full user story or ask the team!

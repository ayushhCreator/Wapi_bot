# Implementation Checklist - 24-Hour Development Plan

**Target:** Production-ready WhatsApp chatbot  
**Timeline:** 24 hours (including testing)  
**Team Size:** 2-3 developers

---

## Phase 1: Core Infrastructure (Hours 0-6)

### Hour 0-1: Project Setup

- [ ] Create folder structure (see Quick_Reference.md)
- [ ] Initialize Git repository
- [ ] Create virtual environment
- [ ] Install dependencies (requirements.txt)
- [ ] Setup Redis (Docker)
- [ ] Setup Ollama + download gemma3:4b
- [ ] Create .env file with API keys
- [ ] Setup logging configuration

**Deliverable:** Working development environment

---

### Hour 1-2: Configuration & Models

#### Task 1.1: Configuration Module

**File:** `wapibot/config/settings.py` (50 lines)

```python
# Define:
- OLLAMA_BASE_URL
- MODEL_NAME
- MAX_TOKENS
- REQUIRED_FIELDS_FOR_BOOKING = 12
- TOTAL_POSSIBLE_FIELDS = 16
- GREETING_STOPWORDS (list)
- SENTIMENT_THRESHOLDS (dict)
```

#### Task 1.2: Scratchpad Model

**File:** `wapibot/models/scratchpad_model.py` (50 lines)

```python
class ScratchpadModel(BaseModel):
    # 16 fields: customer (4), vehicle (3), appointment (4), optional (5)
    # Methods: has_name(), has_vehicle(), completeness()
```

#### Task 1.3: Customer Model

**File:** `wapibot/models/customer_model.py` (50 lines)

```python
class CustomerModel(BaseModel):
    first_name: str
    last_name: str
    phone: str
    # Validators: phone format (10 digits, 6-9 prefix)
```

#### Task 1.4: Vehicle Model

**File:** `wapibot/models/vehicle_model.py` (50 lines)

```python
class VehicleModel(BaseModel):
    brand: str
    model: str
    plate: str
    # Validators: plate format (Indian: MH12AB1234)
```

**Deliverable:** All data models with validation

---

### Hour 2-3: State Machine

#### Task 2.1: State Enum

**File:** `wapibot/core/state/state_machine.py` (50 lines)

```python
class ConversationState(Enum):
    GREETING = "greeting"
    NAME_COLLECTION = "name_collection"
    VEHICLE_DETAILS = "vehicle_details"
    DATE_SELECTION = "date_selection"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

VALID_TRANSITIONS = {
    GREETING: [NAME_COLLECTION],
    NAME_COLLECTION: [VEHICLE_DETAILS],
    # ... etc
}
```

#### Task 2.2: Transition Validator

**File:** `wapibot/core/state/transition_validator.py` (50 lines)

```python
def can_transition(from_state, to_state, scratchpad):
    # Check if transition is valid
    # Check if required data exists
    # Return True/False
```

#### Task 2.3: State Persister

**File:** `wapibot/core/state/state_persister.py` (50 lines)

```python
def save_state(conv_id, state):
    # Save to Redis with TTL (24 hours)

def load_state(conv_id):
    # Load from Redis, default to GREETING
```

**Deliverable:** Working state machine with persistence

---

### Hour 3-4: Data Management

#### Task 3.1: Scratchpad Manager

**File:** `wapibot/core/data/scratchpad.py` (50 lines)

```python
def create_scratchpad():
    return ScratchpadModel()

def save_scratchpad(conv_id, scratchpad):
    # Save to Redis

def load_scratchpad(conv_id):
    # Load from Redis
```

#### Task 3.2: Scratchpad Merger

**File:** `wapibot/core/data/scratchpad_merger.py` (50 lines)

```python
def merge_update(scratchpad, new_data):
    # Merge without overwriting existing data
    # Only update non-null values
    # Return updated scratchpad
```

#### Task 3.3: Completeness Calculator

**File:** `wapibot/core/data/completeness_calculator.py` (50 lines)

```python
def calculate_completeness(scratchpad):
    filled = count_filled_fields(scratchpad)
    return (filled / REQUIRED_FIELDS) * 100

def should_trigger_confirmation(scratchpad):
    return calculate_completeness(scratchpad) >= 75
```

#### Task 3.4: Field Validator

**File:** `wapibot/core/data/validator.py` (50 lines)

```python
def validate_phone(phone):
    # 10 digits, starts with 6-9

def validate_plate(plate):
    # Indian format: MH12AB1234

def validate_date(date_str):
    # Not in past, valid format
```

**Deliverable:** Complete data management layer

---

### Hour 4-5: LLM Integration

#### Task 4.1: DSPy Client

**File:** `wapibot/core/llm/dspy_client.py` (50 lines)

```python
import dspy

def setup_dspy():
    lm = dspy.OllamaLocal(model="gemma3:4b")
    dspy.settings.configure(lm=lm)

class NameExtractor(dspy.Signature):
    user_message = dspy.InputField()
    first_name = dspy.OutputField()
    last_name = dspy.OutputField()
```

#### Task 4.2: Extraction Validator

**File:** `wapibot/core/llm/extraction_validator.py` (50 lines)

```python
def validate_extraction(result, min_confidence=0.5):
    if not result:
        raise ExtractionError("Empty result")
    if result.confidence < min_confidence:
        raise ExtractionError("Low confidence")
    return result
```

#### Task 4.3: Retry Handler

**File:** `wapibot/core/llm/retry_handler.py` (50 lines)

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_llm_with_retry(signature, **kwargs):
    return signature(**kwargs)
```

**Deliverable:** Robust LLM integration with error handling

---

### Hour 5-6: NLP Components

#### Task 5.1: Typo Detector

**File:** `wapibot/core/nlp/typo_detector.py` (50 lines)

```python
class TypoDetector(dspy.Signature):
    user_input = dspy.InputField()
    has_typo = dspy.OutputField(desc="true/false")
    correction = dspy.OutputField(desc="corrected text")

def detect_typos(message):
    # Returns: (has_typo: bool, correction: str)
```

#### Task 5.2: Intent Classifier

**File:** `wapibot/core/nlp/intent_classifier.py` (50 lines)

```python
class IntentClassifier(dspy.Signature):
    user_message = dspy.InputField()
    intent = dspy.OutputField(desc="book/inquire/complaint/cancel")
    confidence = dspy.OutputField(desc="0.0-1.0")

def classify_intent(message):
    # Returns: (intent: str, confidence: float)
```

#### Task 5.3: Sentiment Analyzer

**File:** `wapibot/core/nlp/sentiment_analyzer.py` (50 lines)

```python
class SentimentAnalyzer(dspy.Signature):
    user_message = dspy.InputField()
    interest = dspy.OutputField(desc="1-10")
    anger = dspy.OutputField(desc="1-10")
    boredom = dspy.OutputField(desc="1-10")

def analyze_sentiment(message):
    # Returns: dict with scores
```

**Deliverable:** Complete NLP pipeline

---

## Phase 2: API Integrations (Hours 6-10)

### Hour 6-7: Frappe API Integration

#### Task 6.1: Service Fetcher

**File:** `wapibot/integrations/frappe/service_fetcher.py` (50 lines)

```python
def get_filtered_services(category, frequency_type, vehicle_type):
    response = requests.post(
        f"{FRAPPE_BASE}/api/customer_portal.get_filtered_services",
        json={"category": category, ...}
    )
    return response.json()
```

#### Task 6.2: Addon Fetcher

**File:** `wapibot/integrations/frappe/addon_fetcher.py` (50 lines)

```python
def get_optional_addons(product_id):
    response = requests.get(
        f"{FRAPPE_BASE}/api/booking.get_optional_addons",
        params={"product_id": product_id}
    )
    return response.json()
```

#### Task 6.3: Slot Checker

**File:** `wapibot/integrations/frappe/slot_checker.py` (50 lines)

```python
def get_available_slots(date_str):
    response = requests.get(
        f"{FRAPPE_BASE}/api/booking.get_available_slots_enhanced",
        params={"date_str": date_str}
    )
    return response.json()

def check_slot_availability(slot_id):
    # Atomic check before booking
```

#### Task 6.4: Price Calculator

**File:** `wapibot/integrations/frappe/price_calculator.py` (50 lines)

```python
def calculate_booking_price(product_id, addon_ids, electricity, water):
    response = requests.post(
        f"{FRAPPE_BASE}/api/booking.calculate_booking_price",
        json={...}
    )
    return response.json()
```

#### Task 6.5: Booking Creator

**File:** `wapibot/integrations/frappe/booking_creator.py` (50 lines)

```python
def create_booking(scratchpad):
    response = requests.post(
        f"{FRAPPE_BASE}/api/booking.create_booking",
        json={
            "product_id": scratchpad.service_type,
            "booking_date": scratchpad.appointment_date,
            # ... all fields
        }
    )
    return response.json()  # Returns SR-XXXXXXXX
```

**Deliverable:** Complete Frappe integration

---

### Hour 7-8: WAPI Integration

#### Task 7.1: Message Sender

**File:** `wapibot/integrations/wapi/message_sender.py` (50 lines)

```python
def send_text_message(phone, message, contact_info=None):
    response = requests.post(
        f"{WAPI_BASE}/contact/send-message",
        headers={"Authorization": f"Bearer {WAPI_TOKEN}"},
        json={
            "phone_number": phone,
            "message_body": message,
            "contact": contact_info
        }
    )
    return response.json()
```

#### Task 7.2: Interactive Sender

**File:** `wapibot/integrations/wapi/interactive_sender.py` (50 lines)

```python
def send_buttons(phone, body_text, buttons):
    response = requests.post(
        f"{WAPI_BASE}/contact/send-interactive-message",
        json={
            "phone_number": phone,
            "interactive_type": "button",
            "body_text": body_text,
            "buttons": buttons  # [{"id": "confirm", "title": "✅ Confirm"}]
        }
    )
    return response.json()
```

#### Task 7.3: Template Sender

**File:** `wapibot/integrations/wapi/template_sender.py` (50 lines)

```python
def send_template(phone, template_name, fields):
    response = requests.post(
        f"{WAPI_BASE}/contact/send-template-message",
        json={
            "phone_number": phone,
            "template_name": template_name,
            "template_language": "en",
            **fields  # field_1, field_2, etc.
        }
    )
    return response.json()
```

#### Task 7.4: Media Sender

**File:** `wapibot/integrations/wapi/media_sender.py` (50 lines)

```python
def send_document(phone, media_url, file_name):
    response = requests.post(
        f"{WAPI_BASE}/contact/send-media-message",
        json={
            "phone_number": phone,
            "media_type": "document",
            "media_url": media_url,
            "file_name": file_name
        }
    )
    return response.json()
```

**Deliverable:** Complete WAPI integration

---

### Hour 8-9: Conversation Lock

#### Task 8.1: Redis Lock Manager

**File:** `wapibot/core/locks/conversation_lock.py` (50 lines)

```python
import redis

lock_client = redis.Redis(host='localhost', port=6379)

def acquire_lock(conv_id, timeout=5):
    return lock_client.set(
        f"lock:{conv_id}",
        "1",
        nx=True,  # Only set if not exists
        ex=timeout  # Expire after timeout seconds
    )

def release_lock(conv_id):
    lock_client.delete(f"lock:{conv_id}")

@contextmanager
def conversation_lock(conv_id):
    if not acquire_lock(conv_id):
        raise LockError("Conversation locked")
    try:
        yield
    finally:
        release_lock(conv_id)
```

**Deliverable:** Race condition prevention

---

### Hour 9-10: Orchestrators

#### Task 9.1: Extraction Orchestrator

**File:** `wapibot/orchestrators/extraction_orchestrator.py` (50 lines)

```python
def extract_all_data(user_message, scratchpad):
    # Try name extraction
    name = extract_name(user_message)
    if name:
        scratchpad = merge_update(scratchpad, name)
    
    # Try vehicle extraction
    vehicle = extract_vehicle(user_message)
    if vehicle:
        scratchpad = merge_update(scratchpad, vehicle)
    
    # Try date extraction
    date = extract_date(user_message)
    if date:
        scratchpad = merge_update(scratchpad, date)
    
    return scratchpad
```

**Deliverable:** Coordinated extraction pipeline

---

## Phase 3: Main Handlers (Hours 10-14)

### Hour 10-12: Chat Orchestrator

#### Task 10.1: Main Chat Handler

**File:** `wapibot/orchestrators/chat_orchestrator.py` (50 lines)

```python
def handle_chat(conv_id, user_message):
    # 1. Acquire lock
    with conversation_lock(conv_id):
        # 2. Load state & scratchpad
        state = load_state(conv_id)
        scratchpad = load_scratchpad(conv_id)
        
        # 3. Analyze sentiment
        sentiment = analyze_sentiment(user_message)
        if sentiment.should_disengage():
            return {"message": "I understand. Call us at 1800-XXX"}
        
        # 4. Detect typos
        typo_result = detect_typos(user_message)
        if typo_result.has_typo:
            return {"message": f"Did you mean '{typo_result.correction}'?"}
        
        # 5. Extract data
        scratchpad = extract_all_data(user_message, scratchpad)
        
        # 6. Check completeness
        completeness = calculate_completeness(scratchpad)
        
        # 7. Determine next state
        next_state = determine_next_state(state, scratchpad)
        
        # 8. Generate response
        response = generate_response(state, next_state, scratchpad)
        
        # 9. Save state & scratchpad
        save_state(conv_id, next_state)
        save_scratchpad(conv_id, scratchpad)
        
        # 10. Return response
        return {
            "message": response,
            "state": next_state,
            "scratchpad_completeness": completeness,
            "should_confirm": completeness >= 75
        }
```

**Deliverable:** Main chat endpoint logic

---

### Hour 12-13: Confirmation Orchestrator

#### Task 12.1: Confirmation Handler

**File:** `wapibot/orchestrators/confirmation_orchestrator.py` (50 lines)

```python
def handle_confirmation(conv_id, user_input, action):
    # action: "confirm", "edit", "cancel"
    
    with conversation_lock(conv_id):
        scratchpad = load_scratchpad(conv_id)
        
        if action == "confirm":
            # Create booking
            sr_id = create_booking(scratchpad)
            
            # Send confirmation
            send_text_message(
                scratchpad.phone,
                f"✅ Booking confirmed! SR-{sr_id}"
            )
            
            # Update state
            save_state(conv_id, "completed")
            
            return {
                "message": f"Booking confirmed! SR-{sr_id}",
                "service_request_id": sr_id,
                "state": "completed"
            }
        
        elif action == "edit":
            # Extract edit request
            edit_data = extract_edit_request(user_input)
            scratchpad = merge_update(scratchpad, edit_data)
            save_scratchpad(conv_id, scratchpad)
            
            return {
                "message": "Updated! Please confirm again.",
                "state": "confirmation"
            }
        
        elif action == "cancel":
            save_state(conv_id, "cancelled")
            return {
                "message": "Booking cancelled.",
                "state": "cancelled"
            }
```

**Deliverable:** Confirmation flow handler

---

### Hour 13-14: Response Generator

#### Task 13.1: Response Templates

**File:** `wapibot/orchestrators/response_generator.py` (50 lines)

```python
TEMPLATES = {
    "greeting": "Hello! I'm here to help you book a car service. What's your name?",
    "name_collected": "Great, {name}! What's your phone number?",
    "phone_collected": "Perfect! What car do you have?",
    "vehicle_collected": "Awesome! When would you like the service?",
    "date_collected": "📋 Booking Summary:\n{summary}\n\nConfirm?",
    "completed": "✅ Booking confirmed! SR-{sr_id}. See you on {date}!"
}

def generate_response(state, next_state, scratchpad):
    template = TEMPLATES.get(next_state)
    return template.format(**scratchpad.dict())
```

**Deliverable:** Dynamic response generation

---

## Phase 4: Testing (Hours 14-22)

### Hour 14-18: Unit Tests

#### Task 14.1: State Machine Tests

**File:** `tests/unit/test_state_machine.py`

```python
def test_valid_transition():
    assert can_transition("greeting", "name_collection", scratchpad)

def test_invalid_transition():
    with pytest.raises(InvalidTransitionError):
        can_transition("greeting", "completed", scratchpad)
```

#### Task 14.2: Scratchpad Tests

**File:** `tests/unit/test_scratchpad_merger.py`

```python
def test_merge_without_overwrite():
    scratchpad = {"first_name": "Rahul", "phone": None}
    new_data = {"phone": "9876543210"}
    result = merge_update(scratchpad, new_data)
    assert result["first_name"] == "Rahul"  # Not overwritten
    assert result["phone"] == "9876543210"  # Updated
```

#### Task 14.3: Validation Tests

**File:** `tests/unit/test_validator.py`

```python
def test_phone_validation():
    assert validate_phone("9876543210") == True
    assert validate_phone("1234567890") == False  # Doesn't start with 6-9
```

**Run:** `pytest tests/unit/ -v --cov=wapibot`

---

### Hour 18-20: Integration Tests

#### Task 18.1: Frappe API Tests

**File:** `tests/integration/test_frappe_api.py`

```python
def test_get_services():
    services = get_filtered_services("Car Wash", "One Time", "Sedan")
    assert services["success"] == True
    assert len(services["services"]) > 0
```

#### Task 18.2: WAPI Tests

**File:** `tests/integration/test_wapi.py`

```python
def test_send_message():
    response = send_text_message("9876543210", "Test message")
    assert response.status_code == 200
```

**Run:** `pytest tests/integration/ -v`

---

### Hour 20-22: E2E Tests

#### Task 20.1: Run Conversation Simulator

**File:** `tests/conversation_simulator_v2.py` (already exists)

```bash
python tests/conversation_simulator_v2.py
```

**Expected:** All 7 scenarios pass:

1. ✅ Happy path
2. ✅ Negotiation
3. ✅ Reschedule
4. ✅ Error recovery
5. ✅ Edit confirmation
6. ✅ Cancel & restart
7. ✅ Indecisive customer

---

## Phase 5: Deployment (Hours 22-24)

### Hour 22-23: Production Setup

#### Task 22.1: Environment Configuration

- [ ] Set production API keys (.env.production)
- [ ] Configure Redis (persistent storage)
- [ ] Setup monitoring (Sentry, Grafana)
- [ ] Configure logging (INFO level)

#### Task 22.2: Docker Setup

**File:** `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

**File:** `docker-compose.yml`

```yaml
version: '3.8'
services:
  chatbot:
    build: .
    ports:
      - "8002:8002"
    environment:
      - REDIS_HOST=redis
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

### Hour 23-24: Final QA & Launch

#### Task 23.1: Manual Testing

- [ ] Test on real WhatsApp number
- [ ] Verify button interactions
- [ ] Check template messages
- [ ] Test error scenarios (API timeout, invalid input)

#### Task 23.2: Load Testing

```bash
locust -f tests/load_test.py --users 100 --spawn-rate 10
```

**Target:** 100 concurrent conversations, <2s response time

#### Task 23.3: Launch

- [ ] Deploy to production server
- [ ] Monitor logs for errors
- [ ] Test with 5 real customers
- [ ] Announce launch to team

---

## Success Criteria

### Functional

- [x] All 7 E2E scenarios pass
- [x] Unit test coverage >80%
- [x] Integration tests pass
- [x] No state lock incidents
- [x] No data overwrite incidents

### Performance

- [x] Response time <2s (p95)
- [x] API timeout rate <1%
- [x] Handles 100 concurrent conversations
- [x] Uptime >99.5%

### Code Quality

- [x] All modules <50 lines
- [x] SOLID principles followed
- [x] DRY compliance (no duplication)
- [x] Absolute imports used
- [x] Proper error handling

---

## Rollback Plan

If critical issues found:

1. Revert to previous version (Git tag)
2. Notify customers via WhatsApp template
3. Switch to manual booking (fallback)
4. Fix issues in staging
5. Re-deploy after testing

---

## Post-Launch Monitoring (Week 1)

### Daily Checks

- [ ] Error rate <1%
- [ ] Booking completion rate >85%
- [ ] Average response time <2s
- [ ] Customer satisfaction >4.5/5

### Weekly Review

- [ ] Analyze conversation logs
- [ ] Identify common failure patterns
- [ ] Optimize slow queries
- [ ] Update documentation

---

**Last Updated:** 2025-01-XX  
**Owner:** Development Team  
**Status:** Ready for Implementation

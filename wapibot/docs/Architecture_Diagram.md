# System Architecture Diagram

## **WhatsApp Service Booking Chatbot**

---

## High-Level Architecture

```bash
┌─────────────────────────────────────────────────────────────────┐
│                         USER (WhatsApp)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      WAPI Gateway                               │
│  (Receives messages, sends responses, buttons, templates)       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CHATBOT SYSTEM                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              ORCHESTRATORS LAYER                         │  │
│  │  ┌────────────────┐  ┌──────────────────────────────┐   │  │
│  │  │ Chat Handler   │  │ Confirmation Handler         │   │  │
│  │  │ /chat endpoint │  │ /api/confirmation endpoint   │   │  │
│  │  └────────┬───────┘  └──────────┬───────────────────┘   │  │
│  └───────────┼──────────────────────┼───────────────────────┘  │
│              │                      │                          │
│              ▼                      ▼                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  CORE LAYER                              │  │
│  │                                                          │  │
│  │  ┌─────────────┐  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │ State       │  │ Data     │  │ Conversation     │   │  │
│  │  │ Machine     │  │ Manager  │  │ Lock (Redis)     │   │  │
│  │  └─────────────┘  └──────────┘  └──────────────────┘   │  │
│  │                                                          │  │
│  │  ┌─────────────┐  ┌──────────┐  ┌──────────────────┐   │  │
│  │  │ LLM         │  │ NLP      │  │ Extraction       │   │  │
│  │  │ (DSPy)      │  │ Pipeline │  │ Validator        │   │  │
│  │  └─────────────┘  └──────────┘  └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              INTEGRATIONS LAYER                          │  │
│  │                                                          │  │
│  │  ┌─────────────────────┐  ┌──────────────────────────┐  │  │
│  │  │ Frappe ERP APIs     │  │ WAPI APIs                │  │  │
│  │  │ - Services          │  │ - Send Message           │  │  │
│  │  │ - Addons            │  │ - Send Buttons           │  │  │
│  │  │ - Slots             │  │ - Send Template          │  │  │
│  │  │ - Pricing           │  │ - Send Media             │  │  │
│  │  │ - Booking           │  │                          │  │  │
│  │  └─────────────────────┘  └──────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SYSTEMS                             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Redis        │  │ Frappe ERP   │  │ Ollama (LLM)         │ │
│  │ (State/Lock) │  │ (Backend)    │  │ (gemma3:4b)          │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Request Flow Diagram

### Flow 1: Chat Message Processing

```bash
User sends message
       │
       ▼
[WAPI receives] → POST /chat
       │
       ▼
[Acquire Lock] ─────────────────┐
       │                        │ (Redis)
       ▼                        │
[Load State & Scratchpad] ◄─────┘
       │
       ▼
[Sentiment Analysis] ──→ Disengage if angry?
       │                        │
       │                        └──→ Return "Call us"
       ▼
[Typo Detection] ──→ Has typo?
       │                   │
       │                   └──→ Suggest correction
       ▼
[Data Extraction]
   ├─→ Name
   ├─→ Vehicle
   └─→ Date
       │
       ▼
[Merge to Scratchpad] (no overwrite)
       │
       ▼
[Calculate Completeness] ──→ 75%+ ?
       │                        │
       │                        └──→ Trigger confirmation
       ▼
[State Transition]
       │
       ▼
[Generate Response]
       │
       ▼
[Save State & Scratchpad]
       │
       ▼
[Release Lock]
       │
       ▼
[Send via WAPI]
       │
       ▼
User receives response
```

---

### Flow 2: Confirmation Processing

```bash
User clicks "Confirm" button
       │
       ▼
[WAPI receives] → POST /api/confirmation
       │
       ▼
[Acquire Lock] ─────────────────┐
       │                        │ (Redis)
       ▼                        │
[Load Scratchpad] ◄──────────────┘
       │
       ▼
[Action = confirm/edit/cancel?]
       │
       ├─→ CONFIRM
       │      │
       │      ▼
       │   [Validate Data]
       │      │
       │      ▼
       │   [Call Frappe: create_booking]
       │      │
       │      ▼
       │   [Get SR-XXXXXXXX]
       │      │
       │      ▼
       │   [Send Confirmation via WAPI]
       │      │
       │      ▼
       │   [State = COMPLETED]
       │
       ├─→ EDIT
       │      │
       │      ▼
       │   [Extract Edit Request]
       │      │
       │      ▼
       │   [Merge to Scratchpad]
       │      │
       │      ▼
       │   [Stay in CONFIRMATION]
       │
       └─→ CANCEL
              │
              ▼
           [State = CANCELLED]
              │
              ▼
           [Clear Scratchpad]
       │
       ▼
[Release Lock]
       │
       ▼
User receives response
```

---

## Module Dependency Graph

```bash
main.py
   │
   ├─→ orchestrators/chat_orchestrator.py
   │      │
   │      ├─→ core/state/state_machine.py
   │      ├─→ core/data/scratchpad.py
   │      ├─→ core/nlp/sentiment_analyzer.py
   │      ├─→ core/nlp/typo_detector.py
   │      ├─→ core/llm/dspy_client.py
   │      └─→ integrations/wapi/message_sender.py
   │
   └─→ orchestrators/confirmation_orchestrator.py
          │
          ├─→ core/locks/conversation_lock.py
          ├─→ core/data/scratchpad_merger.py
          ├─→ integrations/frappe/booking_creator.py
          └─→ integrations/wapi/template_sender.py
```

---

## Data Flow Diagram

```bash
┌──────────────────────────────────────────────────────────────┐
│                    CONVERSATION STATE                        │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │ conv_id    │  │ state      │  │ scratchpad         │    │
│  │ "phase2_1" │  │ "greeting" │  │ {first_name: null} │    │
│  └────────────┘  └────────────┘  └────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼ (User: "I'm Rahul")
┌──────────────────────────────────────────────────────────────┐
│                    EXTRACTION PHASE                          │
│                                                              │
│  DSPy Extract → {first_name: "Rahul", confidence: 0.9}      │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    MERGE PHASE                               │
│                                                              │
│  Old: {first_name: null, phone: null}                       │
│  New: {first_name: "Rahul"}                                 │
│  Result: {first_name: "Rahul", phone: null}  ← No overwrite │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    STATE UPDATE                              │
│                                                              │
│  state: "greeting" → "name_collection"                       │
│  completeness: 0% → 6.25% (1/16 fields)                     │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    PERSISTENCE                               │
│                                                              │
│  Redis SET conv:phase2_1:state "name_collection"            │
│  Redis SET conv:phase2_1:scratchpad "{...}"                 │
└──────────────────────────────────────────────────────────────┘
```

---

## State Machine Diagram

```bash
                    ┌─────────────┐
                    │  GREETING   │
                    └──────┬──────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ NAME_COLLECTION │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ VEHICLE_DETAILS │◄───┐
                  └────────┬────────┘    │
                           │             │
                           ▼             │
                  ┌─────────────────┐    │
                  │ DATE_SELECTION  │────┘ (edit)
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  CONFIRMATION   │◄───┐
                  └────────┬────────┘    │
                           │             │
                    ┌──────┴──────┐      │
                    │             │      │
                    ▼             ▼      │
            ┌───────────┐   ┌──────────┐│
            │ COMPLETED │   │ CANCELLED││
            └───────────┘   └──────────┘│
                                        │
                                   (restart)
```

---

## Folder Structure (Visual)

```bash
wapibot/
│
├── core/                          # Core business logic
│   ├── state/                     # State management
│   │   ├── state_machine.py       # 50 lines: States & transitions
│   │   ├── transition_validator.py # 50 lines: Validate transitions
│   │   └── state_persister.py     # 50 lines: Redis save/load
│   │
│   ├── data/                      # Data management
│   │   ├── scratchpad.py          # 50 lines: Scratchpad CRUD
│   │   ├── scratchpad_merger.py   # 50 lines: Merge logic
│   │   ├── completeness_calculator.py # 50 lines: % calculation
│   │   └── validator.py           # 50 lines: Field validation
│   │
│   ├── llm/                       # LLM integration
│   │   ├── dspy_client.py         # 50 lines: DSPy setup
│   │   ├── extraction_validator.py # 50 lines: Validate output
│   │   └── retry_handler.py       # 50 lines: Retry logic
│   │
│   ├── nlp/                       # NLP components
│   │   ├── typo_detector.py       # 50 lines: Detect typos
│   │   ├── intent_classifier.py   # 50 lines: Classify intent
│   │   └── sentiment_analyzer.py  # 50 lines: Analyze sentiment
│   │
│   └── locks/                     # Concurrency control
│       └── conversation_lock.py   # 50 lines: Redis locks
│
├── integrations/                  # External APIs
│   ├── frappe/                    # Frappe ERP
│   │   ├── service_fetcher.py     # 50 lines: Get services
│   │   ├── addon_fetcher.py       # 50 lines: Get addons
│   │   ├── slot_checker.py        # 50 lines: Check slots
│   │   ├── price_calculator.py    # 50 lines: Calculate price
│   │   └── booking_creator.py     # 50 lines: Create booking
│   │
│   └── wapi/                      # WhatsApp API
│       ├── message_sender.py      # 50 lines: Send text
│       ├── interactive_sender.py  # 50 lines: Send buttons
│       ├── template_sender.py     # 50 lines: Send template
│       └── media_sender.py        # 50 lines: Send media
│
├── orchestrators/                 # Request handlers
│   ├── chat_orchestrator.py       # 50 lines: /chat handler
│   ├── confirmation_orchestrator.py # 50 lines: /api/confirmation
│   └── extraction_orchestrator.py # 50 lines: Coordinate extraction
│
├── models/                        # Pydantic models
│   ├── scratchpad_model.py        # 50 lines: Scratchpad schema
│   ├── customer_model.py          # 50 lines: Customer schema
│   ├── vehicle_model.py           # 50 lines: Vehicle schema
│   └── appointment_model.py       # 50 lines: Appointment schema
│
├── config/                        # Configuration
│   ├── settings.py                # 50 lines: Global config
│   └── constants.py               # 50 lines: Constants
│
├── utils/                         # Utilities
│   ├── logger.py                  # 50 lines: Logging
│   └── error_handler.py           # 50 lines: Error handling
│
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── conversation_simulator_v2.py # E2E tests
│
└── main.py                        # Entry point
```

---

## Deployment Architecture

```bash
┌─────────────────────────────────────────────────────────────┐
│                      PRODUCTION                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Load Balancer (Nginx)                   │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                     │
│         ┌─────────────┼─────────────┐                       │
│         │             │             │                       │
│         ▼             ▼             ▼                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Chatbot  │  │ Chatbot  │  │ Chatbot  │                   │
│  │ Instance │  │ Instance │  │ Instance │                   │
│  │    #1    │  │    #2    │  │    #3    │                   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
│       │             │             │                         │
│       └─────────────┼─────────────┘                         │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Redis Cluster                           │   │
│  │  (State, Scratchpad, Locks)                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Ollama Server                           │   │
│  │  (gemma3:4b model)                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ WAPI Gateway │  │ Frappe ERP   │  │ Monitoring       │   │
│  │ (WhatsApp)   │  │ (Backend)    │  │ (Grafana/Sentry) │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

**Last Updated:** 2025-01-XX  
**Maintained By:** Development Team

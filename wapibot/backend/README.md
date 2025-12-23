# WapiBot Backend V2

## **Industry-Standard FastAPI Backend with LLM Resilience**

## Architecture Principles

1. **LLM Resilience**: 3-tier fallback (DSPy → Regex → Ask User)
2. **Small Files**: 100 lines max per file (SOLID + DRY enforced)
3. **Async-First**: All operations non-blocking
4. **Visual Workflows**: LangGraph Studio support
5. **Type-Safe**: Full type hints + Pydantic validation

## Folder Structure

```bash
backend/src/
├── api/                        # FastAPI routes and endpoints
│   ├── v1/                     # API version 1
│   │   ├── chat.py             # Chat endpoints
│   │   ├── confirmation.py     # Confirmation endpoints
│   │   ├── batch.py            # Batch processing endpoints
│   │   └── health.py           # Health check
│   └── deps.py                 # Shared dependencies
│
├── core/                       # Core configuration
│   ├── config.py               # Pydantic Settings
│   ├── security.py             # Authentication/authorization
│   ├── logging.py              # Structured logging setup
│   └── events.py               # Startup/shutdown events
│
├── models/                     # Domain models (Pydantic)
│   ├── customer.py             # Customer, Name, Phone
│   ├── vehicle.py              # Vehicle, VehicleBrand
│   ├── appointment.py          # Appointment, Date, Slot
│   ├── sentiment.py            # SentimentScores
│   ├── intent.py               # Intent, IntentClass
│   ├── response.py             # ChatResponse
│   └── service_request.py      # ServiceRequest
│
├── schemas/                    # API request/response schemas
│   ├── chat.py                 # ChatRequest, ChatResponse
│   ├── booking.py              # BookingRequest, etc.
│   └── webhook.py              # WebhookPayload
│
├── services/                   # Business logic layer
│   ├── chat_service.py         # Chat orchestration
│   ├── booking_service.py      # Booking flow management
│   └── batch_service.py        # Batch processing
│
├── workflows/                  # LangGraph workflow definitions
│   ├── booking_onetime.py      # One-time booking graph
│   ├── booking_subscription.py # Subscription booking graph
│   └── shared/
│       ├── state.py            # BookingState TypedDict
│       └── routes.py           # Conditional routing functions
│
├── nodes/                      # LangGraph workflow nodes (50-100 lines each)
│   ├── extraction/             # Data extraction nodes
│   │   ├── extract_name.py
│   │   ├── extract_vehicle.py
│   │   ├── extract_date.py
│   │   └── extract_phone.py
│   ├── analysis/               # AI analysis nodes
│   │   ├── analyze_sentiment.py
│   │   └── classify_intent.py
│   ├── responses/              # Response generation nodes
│   │   ├── generate_response.py
│   │   └── compose_final.py
│   ├── booking/                # Booking-specific nodes
│   │   ├── confirm_booking.py
│   │   ├── create_service_request.py
│   │   └── handle_edit.py
│   └── validation/             # Validation nodes
│       ├── validate_completeness.py
│       └── detect_typos.py
│
├── dspy_modules/               # DSPy LLM modules
│   ├── extractors.py           # Name, Vehicle, Date extractors
│   ├── analyzers.py            # Sentiment, Intent analyzers
│   └── generators.py           # Response generators
│
├── dspy_signatures/            # DSPy signatures (prompts + I/O)
│   ├── extraction_signatures.py
│   ├── analysis_signatures.py
│   └── generation_signatures.py
│
├── fallbacks/                  # Regex/rule-based fallbacks (30-50 lines each)
│   ├── name_fallback.py        # Regex name extraction
│   ├── vehicle_fallback.py     # Regex vehicle extraction
│   ├── date_fallback.py        # Date parsing fallback
│   └── phone_fallback.py       # Phone regex validation
│
├── wapi/                       # WhatsApp Business API integration
│   ├── client.py               # WAPI client (https://wapi.in.net)
│   ├── webhooks.py             # Webhook handlers
│   ├── message_handler.py      # Message processing
│   └── templates.py            # WhatsApp message templates
│
├── clients/                    # External API clients
│   ├── frappe_client.py        # Frappe ERP client
│   └── yawlit_client.py        # Yawlit webapp client library
│
├── frontend/                   # NextJS frontend integration
│   ├── routes.py               # Frontend-specific routes
│   ├── adapters.py             # Response adapters for UI
│   └── mock_data.py            # Mock data for testing
│
├── db/                         # Database layer
│   ├── session.py              # Database session factory
│   └── base.py                 # Base SQLAlchemy models
│
├── repositories/               # Data access layer (Repository pattern)
│   ├── conversation_repo.py    # Conversation persistence
│   └── service_request_repo.py # Service request storage
│
├── middlewares/                # Custom FastAPI middlewares
│   └── logging_middleware.py   # Request/response logging
│
├── utils/                      # Shared utilities
│   ├── history.py              # Conversation history helpers
│   ├── validators.py           # Pydantic validators
│   └── helpers.py              # General helpers
│
└── tests/                      # Tests (pytest)
    ├── test_api/               # API endpoint tests
    ├── test_services/          # Service layer tests
    ├── test_workflows/         # Workflow tests
    ├── test_wapi/              # WAPI integration tests
    └── test_frontend/          # Frontend integration tests
```

## Layer Responsibilities

### API Layer (`api/`)

- HTTP request/response handling
- Request validation (Pydantic schemas)
- Dependency injection
- Error handling

### Core Layer (`core/`)

- Configuration management
- Security (auth/permissions)
- Logging setup
- Application lifecycle events

### Service Layer (`services/`)

- Business logic orchestration
- Workflow execution
- External API coordination
- Transaction management

### Workflow Layer (`workflows/` + `nodes/`)

- LangGraph state machines
- Conversation flow control
- Node-based processing
- Automatic checkpointing

### Data Layer (`repositories/` + `db/`)

- Database operations
- Data persistence
- Query optimization
- Repository pattern

### Integration Layer (`clients/` + `wapi/` + `frontend/`)

- External API clients
- WhatsApp integration
- Frontend adapters
- Third-party services

## Development Workflow

1. **Start Ollama** (optional, fallbacks will work if offline):

   ```bash
   ollama serve
   ```

2. **Start Backend**:

   ```bash
   cd backend
   uvicorn src.main:app --reload --port 8000
   ```

3. **Run Tests**:

   ```bash
   pytest src/tests/
   ```

4. **Launch LangGraph Studio** (visual workflow editor):

   ```bash
   langgraph-studio
   ```

## Code Quality Standards

- **Max file size**: 100 lines
- **Max function size**: 50 lines
- **Type hints**: Required for all functions
- **Docstrings**: Required for public functions
- **Test coverage**: >80%
- **Linting**: pylint, mypy, black

## Technology Stack

- **Framework**: FastAPI 0.110+
- **LLM Framework**: DSPy + LangGraph
- **Validation**: Pydantic 2.0+
- **Database**: SQLite (checkpoints)
- **Testing**: pytest + pytest-asyncio
- **Type Checking**: mypy
- **Code Formatting**: black + isort

## Next Steps

See `/docs/NEW_ARCHITECTURE_V2.md` for complete migration plan.

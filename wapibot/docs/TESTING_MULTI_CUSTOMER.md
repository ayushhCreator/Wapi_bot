# Multi-Customer Testing Guide

## Overview

Test the WapiBot backend with multiple simulated customers from the frontend using the same workflow as WhatsApp.

## Prerequisites

1. Backend running on port 8000
2. Frontend running on port 3000
3. v2_full_workflow active

## Setup

### 1. Start Backend

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

### 2. Start Frontend

```bash
cd frontend
npm run dev
```

### 3. Switch to FastAPI Mode

- Open frontend at <http://localhost:3000>
- In header, select "Backend: FastAPI"

## Creating Test Conversations

### Customer 1: Rahul Kumar

- **Phone**: `9876543210`
- **Display Name**: `Rahul Kumar`

**Test Conversation**:

```bash
User: Hi, I want to book a car wash
Bot: (extracts name from future messages)
User: My name is Rahul Kumar
Bot: Nice to meet you, Rahul! 👋
```

### Customer 2: Priya Sharma

- **Phone**: `8765432109`
- **Display Name**: `Priya Sharma`

**Test Conversation**:

```bash
User: Hello
Bot: Hello! How can I help you?
User: I need service for my Honda City
Bot: Great! What's your name?
User: Priya Sharma
Bot: Nice to meet you, Priya! 👋
```

### Customer 3: Amit Singh

- **Phone**: `7654321098`
- **Display Name**: `Amit Singh`

**Test Conversation**:

```bash
User: Book car wash
Bot: Sure! What's your name?
User: I am Amit Singh
Bot: Nice to meet you, Amit! 👋
```

## Payload Structure

Frontend sends WAPI-like payload to `/api/v1/chat`:

```json
{
  "contact": {
    "phone_number": "9876543210",
    "first_name": "Rahul",
    "last_name": "Kumar"
  },
  "message": {
    "body": "Hi, I want to book a car wash",
    "message_id": "frontend_1234567890"
  },
  "history": [
    {"role": "user", "content": "Previous message"},
    {"role": "assistant", "content": "Previous response"}
  ]
}
```

## Verification

### Check Backend Logs

The backend should log:

```bash
[Chat] Processing message from 9876543210
[Chat] Using WAPI-like format (frontend testing mode)
[Workflow] extract_name node...
```

### Check Response

Frontend should display:

- Bot's response message
- Extracted data (if using BookingProgress component)
- Booking progress (completeness %)

### Compare with WAPI

The workflow execution should be **identical** to what happens with actual WhatsApp messages.

## Tips

1. **Use realistic phone numbers** - 10 digits starting with 6-9
2. **Test conversation flow** - Send multiple messages per conversation
3. **Switch between conversations** - Verify state is maintained separately
4. **Check extracted data** - Use browser console to see metadata
5. **Test error cases** - Try invalid inputs, empty messages

## Troubleshooting

### Error: "Connection refused"

- Check backend is running on port 8000
- Verify CORS is enabled

### Error: "Invalid format"

- Check payload structure in browser console
- Verify backend schema validation

### No response displayed

- Check browser console for errors
- Verify message was added to conversation store
- Check backend logs for processing errors

## Testing with cURL

### Test Simple Format

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "9876543210",
    "user_message": "Hi, my name is Rahul Kumar",
    "history": []
  }'
```

### Test WAPI-like Format

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "contact": {
      "phone_number": "9876543210",
      "first_name": "Rahul",
      "last_name": "Kumar"
    },
    "message": {
      "body": "Hi, my name is Rahul Kumar",
      "message_id": "test_msg_001"
    },
    "history": []
  }'
```

## Expected Response

Both formats should return:

```json
{
  "message": "Nice to meet you, Rahul! 👋",
  "should_confirm": false,
  "completeness": 0.3,
  "extracted_data": {
    "customer": {
      "first_name": "Rahul",
      "last_name": "Kumar",
      "confidence": 0.9,
      "extraction_method": "dspy"
    },
    "vehicle": null,
    "appointment": null
  },
  "service_request_id": null
}
```

## Test Scenarios

### Scenario 1: Direct Name Extraction

```bash
User: Hi, I am Rahul Kumar
Expected: Immediate extraction, high confidence
```

### Scenario 2: Retroactive Scan

```bash
Message 1: Hi, I am Rahul
Message 2: I want to book
Expected: Scan history, find "Rahul", medium confidence
```

### Scenario 3: Multi-turn Conversation

```bash
Message 1: Hello
Message 2: I need car wash
Message 3: My name is Rahul Kumar
Expected: Extract from third message, update state
```

### Scenario 4: Confidence-based Routing

Test the v2_full_workflow routing:

- High confidence (>0.8): Direct to response
- Low confidence (<0.8): Scan history → merge → response

## Comparison: WAPI vs Frontend Testing

| Aspect | WAPI Webhook | Frontend Testing |
|--------|--------------|------------------|

| **Endpoint** | `/api/v1/wapi/webhook` | `/api/v1/chat` |
| **Payload Format** | WAPI structure | Same WAPI structure |
| **Workflow** | v2_full_workflow | v2_full_workflow (identical) |
| **conversation_id** | `contact.phone_number` | `contact.phone_number` |
| **Security** | HMAC signature | None (dev only) |
| **Response Mechanism** | WAPI API call | JSON return |
| **Use Case** | Production WhatsApp | Local testing |

## Benefits

### ✅ Same Payload Structure

- Frontend sends identical JSON as WAPI
- Test workflow with realistic data
- Easy migration between formats

### ✅ Separate Endpoints

- No risk of breaking WAPI webhook
- Independent security models
- Clear separation of concerns

### ✅ Multi-Customer Testing

- Simulate 2-3+ concurrent conversations
- Test state isolation
- Verify workflow consistency

### ✅ Easy WAPI Comparison

- Test flow in frontend first
- Compare with actual WhatsApp
- Debug before production

"""Chat endpoint for frontend/testing."""

import logging
from fastapi import APIRouter, HTTPException

from schemas.chat import ChatRequest, ChatResponse
from workflows.shared.state import BookingState
from workflows.v2_chat import v2_chat_workflow

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest) -> ChatResponse:
    """
    Process chat message and extract booking data.

    **Flow:**
    1. Create BookingState from request
    2. Run LangGraph workflow (TODO: implement)
    3. Return response with extracted data

    **Example Request:**
    ```json
    {
      "conversation_id": "919876543210",
      "user_message": "I want to book a car wash for my Honda City tomorrow"
    }
    ```

    **Example Response:**
    ```json
    {
      "message": "Great! I can help you. What's your name?",
      "should_confirm": false,
      "completeness": 0.3,
      "extracted_data": {
        "vehicle": {"brand": "Honda", "model": "City"}
      }
    }
    ```
    """
    try:
        logger.info(
            f"Processing chat: {request.conversation_id} - "
            f"{request.user_message[:50]}..."
        )

        # Create initial state
        state: BookingState = {
            "conversation_id": request.conversation_id,
            "user_message": request.user_message,
            "history": request.history or [],
            "customer": None,
            "vehicle": None,
            "appointment": None,
            "sentiment": None,
            "intent": None,
            "intent_confidence": 0.0,
            "current_step": "extract_name",
            "completeness": 0.0,
            "errors": [],
            "response": "",
            "should_confirm": False,
            "should_proceed": True,
            "service_request_id": None,
            "service_request": None
        }

        # Run V2 workflow (atomic nodes architecture)
        result = await v2_chat_workflow.ainvoke(state)

        # Build response
        response = ChatResponse(
            message=result.get("response", "Processing complete!"),
            should_confirm=result.get("should_confirm", False),
            completeness=result.get("completeness", 0.0),
            extracted_data={
                "customer": result.get("customer"),
                "vehicle": result.get("vehicle"),
                "appointment": result.get("appointment")
            },
            service_request_id=result.get("service_request_id")
        )

        logger.info(f"Response: {response.message[:50]}...")
        return response

    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing error: {str(e)}"
        )
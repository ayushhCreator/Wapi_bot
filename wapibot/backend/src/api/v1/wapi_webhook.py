"""WAPI webhook endpoint for WhatsApp messages."""

import logging
import hmac
import hashlib
from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional

from core.config import settings
from schemas.wapi import WAPIWebhookPayload, WAPIResponse
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/wapi", tags=["WAPI"])


def verify_webhook_signature(payload_body: bytes, signature: str) -> bool:
    """Verify WAPI webhook signature using HMAC-SHA256.

    Args:
        payload_body: Raw request body bytes
        signature: Signature from X-WAPI-Signature header

    Returns:
        True if signature is valid, False otherwise
    """
    if not settings.wapi_webhook_secret:
        logger.warning("WAPI webhook secret not configured - skipping signature verification")
        return True  # Allow in development when secret not set

    if not signature:
        return False

    # Compute HMAC-SHA256 signature
    expected_signature = hmac.new(
        settings.wapi_webhook_secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


@router.post("/webhook", response_model=WAPIResponse)
async def wapi_webhook(
    request: Request,
    payload: WAPIWebhookPayload,
    x_wapi_signature: Optional[str] = Header(None, alias="X-WAPI-Signature")
) -> WAPIResponse:
    """
    Handle incoming WhatsApp messages from WAPI with signature validation.

    **Security:**
    - Validates HMAC-SHA256 signature from X-WAPI-Signature header
    - Rejects requests with invalid or missing signatures (in production)

    **Flow:**
    1. Validate webhook signature using HMAC-SHA256
    2. Extract message from WAPI format
    3. Convert to internal BookingState
    4. Run LangGraph workflow
    5. Send response via WAPI API

    **Example Webhook Payload:**
    ```json
    {
      "contact": {
        "phone_number": "919876543210",
        "first_name": "Ravi"
      },
      "message": {
        "whatsapp_message_id": "wamid.abc123",
        "body": "I want to book a car wash"
      }
    }
    ```

    **Headers:**
    - X-WAPI-Signature: HMAC-SHA256 signature of request body
    """
    try:
        # Security: Verify webhook signature
        raw_body = await request.body()
        if not verify_webhook_signature(raw_body, x_wapi_signature or ""):
            logger.warning(f"Invalid webhook signature from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(
                status_code=401,
                detail="Invalid webhook signature"
            )

        phone = payload.contact.phone_number
        message_id = payload.message.whatsapp_message_id
        body = payload.message.body or ""

        logger.info(
            f"WAPI webhook: {phone} - {message_id} - {body[:50]}..."
        )

        # TODO: Convert WAPI format to BookingState
        # TODO: Run workflow
        # TODO: Send response via WAPI API

        # For now, acknowledge receipt
        return WAPIResponse(
            status="received",
            message_id=message_id
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 401 signature validation failure)
        raise
    except Exception as e:
        logger.error(f"WAPI webhook failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred during webhook processing"
        )
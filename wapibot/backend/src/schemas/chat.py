"""Chat API request/response schemas with examples."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
import re


class ChatRequest(BaseModel):
    """Chat message request from frontend."""

    conversation_id: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Unique conversation ID (phone number)",
        examples=["919876543210"]
    )
    user_message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's message text",
        examples=["I want to book a car wash for my Honda City tomorrow"]
    )
    history: Optional[List[Dict[str, str]]] = Field(
        default=[],
        description="Conversation history for retroactive scanning",
        examples=[[
            {"role": "user", "content": "Hi, I am Hrijul"},
            {"role": "assistant", "content": "Hello! How can I help?"}
        ]]
    )

    @field_validator('conversation_id')
    @classmethod
    def validate_conversation_id(cls, v: str) -> str:
        """Validate conversation ID format (alphanumeric only)."""
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('conversation_id must contain only alphanumeric characters')
        return v

    @field_validator('history')
    @classmethod
    def validate_history(cls, v: Optional[List[Dict[str, str]]]) -> Optional[List[Dict[str, str]]]:
        """Validate history structure has required keys."""
        if v is None:
            return v

        for idx, msg in enumerate(v):
            if not isinstance(msg, dict):
                raise ValueError(f'history[{idx}] must be a dict')
            if 'role' not in msg:
                raise ValueError(f'history[{idx}] must have "role" key')
            if 'content' not in msg:
                raise ValueError(f'history[{idx}] must have "content" key')
            if msg['role'] not in ('user', 'assistant'):
                raise ValueError(f'history[{idx}] role must be "user" or "assistant"')
            if not isinstance(msg['content'], str):
                raise ValueError(f'history[{idx}] content must be a string')
            if len(msg['content']) > 5000:
                raise ValueError(f'history[{idx}] content exceeds 5000 characters')

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "919876543210",
                "user_message": "I want to book a car wash for my Honda City tomorrow",
                "history": []
            }
        }


class ChatResponse(BaseModel):
    """Chat response with extracted data."""

    message: str = Field(
        ...,
        description="Response message to user",
        examples=["Great! I can help you book a car wash. What's your name?"]
    )
    should_confirm: bool = Field(
        default=False,
        description="Show confirmation screen",
        examples=[False]
    )
    completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Data collection progress (0-1)",
        examples=[0.3]
    )
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted booking information",
        examples=[{
            "customer": {"first_name": "Ravi", "phone": "919876543210"},
            "vehicle": {"brand": "Honda", "model": "City"},
            "appointment": None
        }]
    )
    service_request_id: Optional[str] = Field(
        default=None,
        description="Service request ID if booking created",
        examples=["SR-2025-001"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Great! I can help you book a car wash. What's your name?",
                "should_confirm": False,
                "completeness": 0.3,
                "extracted_data": {
                    "customer": {"first_name": "Ravi", "phone": "919876543210"},
                    "vehicle": {"brand": "Honda", "model": "City"},
                    "appointment": None
                },
                "service_request_id": None
            }
        }
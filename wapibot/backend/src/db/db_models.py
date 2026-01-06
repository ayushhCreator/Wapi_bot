"""SQLModel database table definitions for conversation persistence.

Database ORM models using SQLModel (Pydantic + SQLAlchemy).
Separate from domain models in models/ folder.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class ConversationStateTable(SQLModel, table=True):
    """Database table for versioned conversation state storage.

    Stores each version of the conversation state with booking data.
    Primary key is composite (conversation_id, version) for versioning.
    """

    __tablename__ = "conversation_states"

    conversation_id: str = Field(primary_key=True, index=True)
    version: int = Field(primary_key=True)
    state: str = Field(description="Current state: collecting, confirmation, completed")
    booking_state_json: str = Field(description="Full BookingState serialized as JSON")
    completeness: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Booking completeness score (0-1)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when this version was created",
    )


class ConversationHistoryTable(SQLModel, table=True):
    """Database table for conversation turn history.

    Stores every message exchange in the conversation.
    """

    __tablename__ = "conversation_history"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="Auto-incrementing primary key"
    )
    conversation_id: str = Field(index=True, description="Conversation identifier")
    turn_number: int = Field(description="Turn number in conversation")
    role: str = Field(description="Message role: user or assistant")
    content: str = Field(description="Message content")
    extracted_data_json: Optional[str] = Field(
        default=None, description="Extracted data from this turn (JSON)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp when turn was recorded"
    )

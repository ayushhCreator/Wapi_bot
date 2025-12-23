"""Response and extraction result domain models.

Provides validated models for chatbot responses and
data extraction results with comprehensive metadata.
"""

from typing import Dict, Any, Optional
from pydantic import (
    BaseModel,
    Field,
    model_validator,
    computed_field,
    ConfigDict
)


class ChatbotResponse(BaseModel):
    """Validated chatbot response with metadata."""

    model_config = ConfigDict(extra='forbid')

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Response message to user"
    )
    should_proceed: bool = Field(
        ...,
        description="Whether conversation should continue"
    )
    extracted_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Data extracted from user message"
    )
    sentiment: Optional[Dict[str, float]] = Field(
        None,
        description="Sentiment scores"
    )
    intent: Optional[str] = Field(
        None,
        description="Classified intent"
    )
    intent_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Intent classification confidence"
    )
    suggestions: Optional[Dict[str, Any]] = Field(
        None,
        description="Conversation handling suggestions"
    )
    processing_time_ms: float = Field(
        ge=0.0,
        description="Processing time in milliseconds"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Response confidence"
    )
    should_confirm: bool = Field(
        default=False,
        description="Show confirmation screen"
    )
    scratchpad_completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Data completeness (0-100%)"
    )
    scratchpad: Optional[Dict[str, Any]] = Field(
        None,
        description="Current scratchpad state"
    )
    state: str = Field(
        default="greeting",
        description="Current conversation state"
    )
    data_extracted: bool = Field(
        default=False,
        description="New data extracted this turn"
    )
    typo_corrections: Optional[Dict[str, str]] = Field(
        default=None,
        description="Suggested typo corrections"
    )
    service_request_id: Optional[str] = Field(
        default=None,
        description="Service request ID if created"
    )
    service_request: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Full service request details"
    )

    @model_validator(mode='after')
    def validate_message_length(self):
        """Validate message is reasonably descriptive."""
        if len(self.message) < 5:
            raise ValueError("Response too short")
        return self

    @computed_field
    @property
    def sentiment_analysis_available(self) -> bool:
        """Check if sentiment analysis available."""
        return self.sentiment is not None

    @computed_field
    @property
    def data_extraction_performed(self) -> bool:
        """Check if data extraction performed."""
        return (
            self.extracted_data is not None
            and len(self.extracted_data) > 0
        )


class ExtractionResult(BaseModel):
    """Validated data extraction result."""

    model_config = ConfigDict(extra='forbid')

    success: bool = Field(
        ...,
        description="Extraction successful"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted data"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        default=1.0,
        description="Extraction confidence"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Extraction errors"
    )

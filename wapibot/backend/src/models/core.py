"""Core validation models and shared infrastructure.

Provides base models for validation results, extraction metadata,
and confidence thresholds used across all domain models.
"""

from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Validation result with detailed feedback."""

    is_valid: bool = Field(description="Whether data passed validation")
    field_name: str = Field(description="Name of validated field")
    errors: List[str] = Field(
        default_factory=list,
        description="Validation errors"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Validation warnings"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        default=1.0,
        description="Confidence in extracted data"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )


class ExtractionMetadata(BaseModel):
    """Metadata for extraction process tracking."""

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Extraction confidence score"
    )
    extraction_method: Literal[
        "direct",
        "chain_of_thought",
        "fallback",
        "rule_based",
        "dspy"
    ] = Field(description="Method used for extraction")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Extraction timestamp"
    )
    extraction_source: str = Field(
        description="Source of extraction (e.g., user message)"
    )
    processing_time_ms: float = Field(
        ge=0.0,
        default=0.0,
        description="Processing time in milliseconds"
    )


class ConfidenceThresholdConfig(BaseModel):
    """Configuration for confidence thresholds."""

    minimum_acceptable: float = Field(
        ge=0.0,
        le=1.0,
        default=0.6,
        description="Minimum acceptable confidence"
    )
    high_confidence: float = Field(
        ge=0.0,
        le=1.0,
        default=0.85,
        description="High confidence threshold"
    )
    require_human_review_below: float = Field(
        ge=0.0,
        le=1.0,
        default=0.5,
        description="Require human review below this"
    )

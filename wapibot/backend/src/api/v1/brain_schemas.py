"""Pydantic schemas for Brain Control API."""

from typing import Literal, Optional, List
from pydantic import BaseModel, Field


class DreamTriggerRequest(BaseModel):
    """Request to manually trigger dream cycle."""
    force: bool = Field(default=False, description="Force dream even if min conversations not met")
    min_conversations: Optional[int] = Field(default=None, description="Override min conversations")


class TrainTriggerRequest(BaseModel):
    """Request to trigger GEPA optimization."""
    optimizer: Literal["gepa"] = Field(default="gepa")
    num_iterations: int = Field(default=100, ge=1)


class FeatureToggleUpdate(BaseModel):
    """Update a feature toggle."""
    feature_name: str
    enabled: bool


class BrainModeUpdate(BaseModel):
    """Update brain operation mode."""
    mode: Literal["shadow", "reflex", "conscious"]


class BrainStatusResponse(BaseModel):
    """Brain system status."""
    enabled: bool
    mode: str
    features: dict
    metrics: dict


class DecisionRecord(BaseModel):
    """Single brain decision record."""
    decision_id: str
    timestamp: str
    conflict_detected: Optional[str]
    action_taken: Optional[str]
    confidence: float


class DecisionListResponse(BaseModel):
    """Paginated decision history."""
    decisions: List[DecisionRecord]
    total: int
    page: int
    page_size: int

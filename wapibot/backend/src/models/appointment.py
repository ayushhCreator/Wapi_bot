"""Appointment-related domain models.

Provides validated models for date and time slot booking
with comprehensive validation rules.
"""

from datetime import date, time, datetime
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    computed_field,
    ConfigDict
)
from .core import ExtractionMetadata


class TimeSlot(str, Enum):
    """Valid appointment time slots."""

    EARLY_MORNING = "early_morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"


class Date(BaseModel):
    """Validated date with reasonableness checks."""

    model_config = ConfigDict(extra='forbid')

    date_str: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Original date string"
    )
    parsed_date: date = Field(
        ...,
        description="Parsed date object"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        default=1.0,
        description="Parsing confidence"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

    @model_validator(mode='after')
    def validate_date_reasonableness(self):
        """Validate date is within reasonable range."""
        today = date.today()
        max_years_ahead = 3
        max_years_back = 10

        future_limit = today.replace(year=today.year + max_years_ahead)
        past_limit = today.replace(year=today.year - max_years_back)

        if self.parsed_date > future_limit:
            raise ValueError(
                f"Date {self.parsed_date} too far in future"
            )
        if self.parsed_date < past_limit:
            raise ValueError(
                f"Date {self.parsed_date} too far in past"
            )

        # Validate calendar date
        try:
            date(
                self.parsed_date.year,
                self.parsed_date.month,
                self.parsed_date.day
            )
        except ValueError as e:
            month = self.parsed_date.month
            day = self.parsed_date.day

            # Lenient validation for LLM quirks
            if month == 2 and day > 29:
                raise ValueError(f"Invalid date: {e}")
            elif month in [4, 6, 9, 11] and day > 30:
                raise ValueError(f"Invalid date: {e}")
            elif day > 31:
                raise ValueError(f"Invalid date: {e}")

        return self

    @computed_field
    @property
    def is_in_past(self) -> bool:
        """Check if date is in the past."""
        return self.parsed_date < date.today()

    @computed_field
    @property
    def days_from_now(self) -> int:
        """Days from today."""
        delta = self.parsed_date - date.today()
        return delta.days


class Appointment(BaseModel):
    """Complete appointment details."""

    model_config = ConfigDict(extra='forbid')

    date: Date = Field(description="Appointment date")
    time_slot: TimeSlot = Field(description="Time slot")
    service_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type of service"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

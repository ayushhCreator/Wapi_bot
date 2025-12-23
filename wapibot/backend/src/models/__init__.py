"""Domain models package.

Exports all validated Pydantic models organized by domain.
"""

from .core import ValidationResult, ExtractionMetadata, ConfidenceThresholdConfig
from .customer import Name, Phone
from .vehicle import VehicleBrand, VehicleDetails
from .appointment import TimeSlot, Date, Appointment
from .sentiment import SentimentDimension, SentimentScores
from .intent import IntentClass, Intent
from .response import ChatbotResponse, ExtractionResult

__all__ = [
    # Core
    "ValidationResult",
    "ExtractionMetadata",
    "ConfidenceThresholdConfig",
    # Customer
    "Name",
    "Phone",
    # Vehicle
    "VehicleBrand",
    "VehicleDetails",
    # Appointment
    "TimeSlot",
    "Date",
    "Appointment",
    # Sentiment
    "SentimentDimension",
    "SentimentScores",
    # Intent
    "IntentClass",
    "Intent",
    # Response
    "ChatbotResponse",
    "ExtractionResult",
]

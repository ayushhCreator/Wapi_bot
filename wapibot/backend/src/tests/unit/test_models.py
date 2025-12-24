"""Unit tests for Pydantic v2 models.

Tests Email validation, appointment date validation, and other model features.
"""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from models.customer import Email
from models.appointment import Date
from models.core import ExtractionMetadata


class TestEmailModel:
    """Test Email model with Pydantic v2 EmailStr validation."""

    def test_valid_email(self):
        """Test valid email address."""
        metadata = ExtractionMetadata(
            confidence=0.9,
            method="dspy",
            reasoning="Clear email format"
        )
        email = Email(email="test@example.com", metadata=metadata)
        assert email.email == "test@example.com"

    def test_email_normalization(self):
        """Test email normalization (lowercase)."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")
        email = Email(email="Test@Example.COM", metadata=metadata)
        # EmailStr should normalize to lowercase
        assert email.email.lower() == "test@example.com"

    def test_invalid_email_format(self):
        """Test rejection of invalid email format."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")

        with pytest.raises(ValidationError):
            Email(email="not-an-email", metadata=metadata)

    def test_placeholder_email_rejection(self):
        """Test rejection of placeholder emails."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")

        # Common placeholders should be rejected
        placeholders = [
            "none@example.com",
            "test@test.com",
            "noreply@example.com",
        ]

        for placeholder in placeholders:
            with pytest.raises(ValidationError, match="Placeholder email not allowed"):
                Email(email=placeholder, metadata=metadata)

    def test_email_with_special_chars(self):
        """Test email with valid special characters."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")
        email = Email(email="user.name+tag@example.co.in", metadata=metadata)
        assert "user.name+tag" in email.email


class TestDateModel:
    """Test Date model with date validation."""

    def test_valid_future_date(self):
        """Test valid future date."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")
        tomorrow = date.today() + timedelta(days=1)

        appt = Date(
            date_str="tomorrow",
            parsed_date=tomorrow,
            metadata=metadata
        )
        assert appt.parsed_date == tomorrow
        assert not appt.is_in_past

    def test_today_is_valid(self):
        """Test that today's date is valid."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")
        today = date.today()

        appt = Date(
            parsed_date=today,
            date_str="today",
            metadata=metadata
        )
        assert appt.parsed_date == today
        assert not appt.is_in_past

    def test_past_date_rejection(self):
        """Test rejection of past dates."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")
        yesterday = date.today() - timedelta(days=1)

        with pytest.raises(ValidationError, match="is in the past"):
            Date(
                parsed_date=yesterday,
                date_str="yesterday",
                metadata=metadata
            )

    def test_far_future_date_rejection(self):
        """Test rejection of dates too far in future (>180 days)."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")
        far_future = date.today() + timedelta(days=200)

        with pytest.raises(ValidationError, match="too far in the future"):
            Date(
                parsed_date=far_future,
                date_str="200 days from now",
                metadata=metadata
            )

    def test_max_valid_future_date(self):
        """Test maximum valid future date (180 days)."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")
        max_future = date.today() + timedelta(days=180)

        appt = Date(
            parsed_date=max_future,
            date_str="180 days from now",
            metadata=metadata
        )
        assert appt.parsed_date == max_future

    def test_days_from_now_property(self):
        """Test days_from_now computed property."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")
        tomorrow = date.today() + timedelta(days=1)

        appt = Date(
            parsed_date=tomorrow,
            date_str="tomorrow",
            metadata=metadata
        )
        assert appt.days_from_now == 1

    def test_is_today_property(self):
        """Test is_today computed property."""
        metadata = ExtractionMetadata(confidence=0.9, method="dspy")
        today = date.today()

        appt = Date(
            parsed_date=today,
            date_str="today",
            metadata=metadata
        )
        assert appt.is_today is True


class TestExtractionMetadata:
    """Test ExtractionMetadata model."""

    def test_metadata_creation(self):
        """Test basic metadata creation."""
        metadata = ExtractionMetadata(
            confidence=0.9,
            method="dspy",
            reasoning="High confidence extraction"
        )
        assert metadata.confidence == 0.9
        assert metadata.method == "dspy"
        assert metadata.reasoning == "High confidence extraction"

    def test_metadata_confidence_bounds(self):
        """Test confidence value bounds (0-1)."""
        # Valid confidence
        metadata = ExtractionMetadata(confidence=0.5, method="dspy")
        assert metadata.confidence == 0.5

        # Invalid confidence (>1)
        with pytest.raises(ValidationError):
            ExtractionMetadata(confidence=1.5, method="dspy")

        # Invalid confidence (<0)
        with pytest.raises(ValidationError):
            ExtractionMetadata(confidence=-0.1, method="dspy")

    def test_metadata_optional_fields(self):
        """Test optional reasoning field."""
        metadata = ExtractionMetadata(confidence=0.8, method="fallback")
        assert metadata.reasoning is None

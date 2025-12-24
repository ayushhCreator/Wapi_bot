"""Unit tests for fallback extractors.

Tests regex-based extraction fallbacks for email, phone, and name.
"""

import pytest
from fallbacks.email_fallback import RegexEmailExtractor
from fallbacks.phone_fallback import RegexPhoneExtractor
from fallbacks.name_fallback import RegexNameExtractor


class TestRegexEmailExtractor:
    """Test regex-based email extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RegexEmailExtractor()

    def test_extract_valid_email(self):
        """Test extraction of valid email from message."""
        message = "My email is john.doe@example.com please contact me"
        result = self.extractor.extract(message)

        assert result is not None
        assert result["email"] == "john.doe@example.com"

    def test_extract_email_with_numbers(self):
        """Test extraction of email with numbers."""
        message = "Contact me at user123@test-domain.co.in"
        result = self.extractor.extract(message)

        assert result is not None
        assert "user123" in result["email"]

    def test_reject_placeholder_emails(self):
        """Test rejection of placeholder emails."""
        placeholders = [
            "My email is none@example.com",
            "test@test.com is my email",
            "Contact noreply@example.com",
        ]

        for message in placeholders:
            result = self.extractor.extract(message)
            assert result is None, f"Should reject placeholder: {message}"

    def test_no_email_in_message(self):
        """Test when no email is present."""
        message = "I don't have an email address right now"
        result = self.extractor.extract(message)

        assert result is None

    def test_invalid_email_format(self):
        """Test rejection of invalid email formats."""
        invalid_messages = [
            "My email is notanemail",
            "Contact me@",
            "Email: @example.com",
        ]

        for message in invalid_messages:
            result = self.extractor.extract(message)
            assert result is None

    def test_extract_first_email_if_multiple(self):
        """Test extraction when multiple emails present."""
        message = "Contact john@example.com or jane@example.com"
        result = self.extractor.extract(message)

        assert result is not None
        # Should extract first valid email
        assert "john@example.com" in result["email"]


class TestRegexPhoneExtractor:
    """Test regex-based phone number extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RegexPhoneExtractor()

    def test_extract_valid_indian_mobile(self):
        """Test extraction of valid Indian mobile number."""
        message = "My phone is 9876543210"
        result = self.extractor.extract(message)

        assert result is not None
        assert result["phone"] == "+919876543210"

    def test_extract_with_country_code(self):
        """Test extraction with +91 prefix."""
        message = "Call me at +919876543210"
        result = self.extractor.extract(message)

        assert result is not None
        assert result["phone"] == "+919876543210"

    def test_extract_with_spaces(self):
        """Test extraction with spaces in number."""
        message = "My number is 98765 43210"
        result = self.extractor.extract(message)

        assert result is not None
        assert "9876543210" in result["phone"]

    def test_reject_invalid_indian_mobile(self):
        """Test rejection of invalid Indian mobile numbers."""
        invalid_numbers = [
            "1234567890",  # Doesn't start with valid prefix
            "5876543210",  # Invalid first digit
            "98765",  # Too short
            "98765432109876",  # Too long
        ]

        for number in invalid_numbers:
            result = self.extractor.extract(f"My phone is {number}")
            assert result is None, f"Should reject invalid number: {number}"

    def test_reject_placeholder_numbers(self):
        """Test rejection of placeholder numbers."""
        placeholders = [
            "9999999999",
            "0000000000",
        ]

        for number in placeholders:
            result = self.extractor.extract(f"My phone is {number}")
            assert result is None


class TestRegexNameExtractor:
    """Test regex-based name extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RegexNameExtractor()

    def test_extract_full_name(self):
        """Test extraction of full name (first + last)."""
        message = "My name is Ravi Kumar"
        result = self.extractor.extract(message)

        assert result is not None
        assert result["first_name"] == "Ravi"
        assert result["last_name"] == "Kumar"

    def test_extract_single_name(self):
        """Test extraction of single name."""
        message = "I'm Priya"
        result = self.extractor.extract(message)

        assert result is not None
        assert result["first_name"] == "Priya"
        assert result["last_name"] == ""

    def test_extract_three_part_name(self):
        """Test extraction of three-part name."""
        message = "My name is Amit Kumar Singh"
        result = self.extractor.extract(message)

        assert result is not None
        assert result["first_name"] == "Amit"
        assert "Kumar" in result["last_name"] or "Singh" in result["last_name"]

    def test_reject_placeholder_names(self):
        """Test rejection of placeholder names."""
        placeholders = [
            "My name is abc",
            "I'm xyz",
            "Call me test",
        ]

        for message in placeholders:
            result = self.extractor.extract(message)
            assert result is None

    def test_no_name_in_message(self):
        """Test when no name pattern is present."""
        message = "I want to book a car wash"
        result = self.extractor.extract(message)

        assert result is None

    def test_capitalization_handling(self):
        """Test proper capitalization of extracted names."""
        message = "my name is ravi kumar"
        result = self.extractor.extract(message)

        assert result is not None
        # Names should be capitalized
        assert result["first_name"][0].isupper()
        if result["last_name"]:
            assert result["last_name"][0].isupper()

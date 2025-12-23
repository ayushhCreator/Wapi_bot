"""Regex-based name extraction fallback.

Fast, reliable name extraction using regex patterns.
Works offline when LLM is unavailable.
"""

import re
from typing import Optional, Dict

# Greeting stopwords to reject as names
STOPWORDS = {
    "hi", "hello", "hey", "haan", "yes", "ok", "okay",
    "sure", "yep", "yeah", "nope", "no", "thanks"
}


class RegexNameExtractor:
    """Fast name extraction using regex patterns."""

    # Patterns for Indian/English name detection
    PATTERNS = [
        # "my name is John", "I am John", "I'm John Doe"
        r"(?:my name is|i am|i'?m|this is|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",

        # Just a capitalized name "John" or "John Doe"
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)$",
    ]

    def extract(self, message: str) -> Optional[Dict[str, str]]:
        """
        Extract name from message using regex.

        Args:
            message: User message text

        Returns:
            {"first_name": "John", "last_name": "Doe"} or None
        """
        if not message:
            return None

        message = message.strip()

        # Try each pattern
        for pattern in self.PATTERNS:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                full_name = match.group(1).strip()

                # Reject stopwords
                if full_name.lower() in STOPWORDS:
                    continue

                # Reject if contains numbers
                if any(char.isdigit() for char in full_name):
                    continue

                # Split into first/last name
                parts = full_name.split()
                if len(parts) == 1:
                    return {
                        "first_name": parts[0],
                        "last_name": ""
                    }
                else:
                    return {
                        "first_name": parts[0],
                        "last_name": " ".join(parts[1:])
                    }

        return None

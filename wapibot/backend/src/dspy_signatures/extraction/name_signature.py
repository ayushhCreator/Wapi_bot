"""DSPy signature for name extraction."""

import dspy


class NameExtractionSignature(dspy.Signature):
    """Extract customer name from unstructured input."""

    conversation_history: dspy.History = dspy.InputField(
        desc="Full conversation history for context"
    )
    user_message = dspy.InputField(desc="User's message that may contain their name")
    context = dspy.InputField(
        desc="Conversation context indicating we're collecting name"
    )

    first_name = dspy.OutputField(
        desc="Extracted first name only, properly capitalized"
    )
    last_name = dspy.OutputField(
        desc="Extracted last name if provided, empty string otherwise"
    )
    confidence = dspy.OutputField(desc="Confidence in extraction (low/medium/high)")

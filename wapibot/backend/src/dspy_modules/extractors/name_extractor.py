"""Name extraction DSPy module."""

import dspy
from typing import List, Dict, Any

from dspy_signatures.extraction.name_signature import NameExtractionSignature
from utils.history_utils import create_dspy_history
from core.config import settings


class NameExtractor(dspy.Module):
    """Extract customer name using DSPy Chain of Thought."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(NameExtractionSignature)

    def __call__(
        self,
        conversation_history: List[Dict[str, str]] | None = None,
        user_message: str = "",
        context: str = "Collecting customer name for booking",
    ) -> Dict[str, Any]:
        """
        Extract name from user message.

        Note: Using __call__ instead of forward() per DSPy best practices.

        Args:
            conversation_history: List of {"role": "user/assistant", "content": "..."}
            user_message: Current user message
            context: Context for extraction

        Returns:
            Dict with first_name, last_name, confidence
        """
        # Convert history to DSPy format
        if not conversation_history:
            conversation_history = []

        dspy_history = create_dspy_history(conversation_history)

        # Call DSPy predictor
        result = self.predictor(
            conversation_history=dspy_history,
            user_message=user_message,
            context=context,
        )

        # Convert confidence string to float using config values (no magic numbers!)
        confidence_map = {
            "low": settings.confidence_low,
            "medium": settings.confidence_medium,
            "high": settings.confidence_high,
        }
        confidence_str = getattr(result, "confidence", "medium").lower()
        confidence_float = confidence_map.get(
            confidence_str, settings.confidence_medium
        )

        return {
            "first_name": getattr(result, "first_name", "").strip(),
            "last_name": getattr(result, "last_name", "").strip(),
            "confidence": confidence_float,
        }

"""DSPy conversation history utilities.

Simplified from V1, adapted for V2 BookingState.
"""

import dspy
from typing import List, Dict


def create_dspy_history(messages: List[Dict[str, str]]) -> dspy.History:
    """
    Convert message list to dspy.History object.

    Args:
        messages: List of {"role": "user/assistant", "content": "..."}

    Returns:
        dspy.History object for DSPy modules
    """
    if not messages:
        return dspy.History(messages=[])

    formatted_messages = []
    for msg in messages:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            formatted_messages.append({
                "role": msg["role"],
                "content": str(msg["content"]).strip()
            })

    return dspy.History(messages=formatted_messages)


def filter_user_messages_only(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter to user messages only.

    Prevents LLM from being confused by chatbot's own responses.
    When extracting user data, only show what the USER said.
    """
    return [msg for msg in messages if msg.get("role") == "user"]
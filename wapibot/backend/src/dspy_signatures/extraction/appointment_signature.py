"""DSPy signature for appointment details extraction.

Extracts date, time, and service type from conversation.
"""

import dspy


class AppointmentExtractionSignature(dspy.Signature):
    """Extract appointment details from user message.

    Identifies preferred date, time, and service type for car wash booking.
    """

    conversation_history: str = dspy.InputField(
        desc="Previous conversation turns for context"
    )
    user_message: str = dspy.InputField(desc="Current user message to extract from")
    context: str = dspy.InputField(
        desc="Extraction context (e.g., 'Scheduling service appointment')"
    )

    date: str = dspy.OutputField(
        desc="Appointment date in YYYY-MM-DD format or relative (e.g., 'tomorrow', 'next Monday')"
    )
    time: str = dspy.OutputField(
        desc="Preferred time slot (e.g., 'morning', '2 PM', 'afternoon')"
    )
    service_type: str = dspy.OutputField(
        desc="Service type requested (e.g., 'basic wash', 'premium detailing')"
    )
    confidence: str = dspy.OutputField(
        desc="Extraction confidence: 'low', 'medium', or 'high'"
    )
    reasoning: str = dspy.OutputField(
        desc="Why these appointment details were extracted"
    )

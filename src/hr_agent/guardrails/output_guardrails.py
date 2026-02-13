"""
Output Guardrails - Filter agent responses for safety.

Ensures agent outputs don't contain harmful content.
"""
import re
from typing import Tuple

# Topics the agent should NEVER discuss
FORBIDDEN_TOPICS = [
    "how to harm",
    "how to steal",
    "embezzle",
    "fraud",
    "illegal",
    "bypass security",
    "personal information of other employees",
]

# Required response elements for grounded answers
GROUNDING_INDICATORS = [
    "according to",
    "based on",
    "the policy states",
    "the handbook",
    "our documentation",
]


def detect_ungrounded_response(text: str) -> bool:
    """
    Check if response appears to be hallucinated (not grounded).
    """
    text_lower = text.lower()
    
    # If response is very confident but lacks grounding phrases, flag it
    confidence_phrases = ["definitely", "absolutely", "certainly", "always", "never"]
    has_confidence = any(phrase in text_lower for phrase in confidence_phrases)
    has_grounding = any(phrase in text_lower for phrase in GROUNDING_INDICATORS)
    
    # Flag if confident but not grounded
    if has_confidence and not has_grounding:
        return True
    
    return False


def detect_forbidden_content(text: str) -> bool:
    """Check for forbidden topics in response."""
    text_lower = text.lower()
    for topic in FORBIDDEN_TOPICS:
        if topic in text_lower:
            return True
    return False


def detect_pii_leak(text: str) -> bool:
    """Check if response leaks PII."""
    # SSN pattern
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
        return True
    # Salary amounts (specific dollar amounts could be sensitive)
    if re.search(r"\$\d{2,3},\d{3}", text):
        return True
    return False


def validate_output(text: str) -> Tuple[bool, str, dict]:
    """
    Validate agent output for safety.
    
    Returns:
        Tuple of (is_safe, sanitized_text, metadata)
    """
    metadata = {
        "ungrounded": False,
        "forbidden_content": False,
        "pii_leak": False,
    }
    
    # Check for forbidden content
    if detect_forbidden_content(text):
        metadata["forbidden_content"] = True
        return False, "I cannot provide that information. Please contact HR directly.", metadata
    
    # Check for PII leaks
    if detect_pii_leak(text):
        metadata["pii_leak"] = True
        return False, "I cannot share that specific information for privacy reasons.", metadata
    
    # Check for ungrounded responses (warning only, don't block)
    if detect_ungrounded_response(text):
        metadata["ungrounded"] = True
        # Add disclaimer
        text = text + "\n\n*Note: Please verify this information with HR.*"
    
    return True, text, metadata


def output_guardrail_callback(context, agent_response: str) -> Tuple[bool, str]:
    """
    ADK-compatible callback for output guardrails.
    """
    is_safe, sanitized, metadata = validate_output(agent_response)
    return is_safe or True, sanitized  # Allow through with modification

"""
Input Guardrails - Validate and sanitize user input.

Production-grade safety layer for multi-agent HR system.
"""
import re
from typing import Tuple

# PII patterns to detect
PII_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
}

# Blocked phrases indicating prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above|your)?\s*instructions",
    r"forget (everything|all|what) (you were|you've been)",
    r"you are now",
    r"act as",
    r"pretend (to be|you are)",
    r"system prompt",
    r"override",
    r"jailbreak",
    r"disregard",
]

# Sensitive topics requiring escalation
ESCALATION_TRIGGERS = [
    "harassment",
    "discrimination", 
    "lawsuit",
    "legal action",
    "termination",
    "fired",
    "whistleblower",
    "retaliation",
    "hostile work environment",
    "sexual",
    "violence",
    "threat",
    "harassed",  # Added
]

# Data exfiltration / PII extraction attempts
DATA_EXTRACTION_PATTERNS = [
    r"(social security|ssn|ss#)",
    r"(bank account|routing number|account number)",
    r"(home address|personal address|street address)",
    r"(phone number|cell number|mobile number) of",
    r"(salary|compensation|pay) (of|for) (other|another|specific)",
    r"(credentials|password|login)",
    r"(previous user|other user|last conversation)",
    r"(database|employee records|confidential)",
]

# Harmful action patterns
HARMFUL_ACTION_PATTERNS = [
    r"(embezzle|steal|fraud)",
    r"(fake|forge|falsify) (document|letter|email)",
    r"(hostile|toxic) work environment",
    r"(fire|terminate) (someone|them|him|her) (illegally|without cause)",
    r"bypass (security|hr|compliance)",
    r"(avoid|evade) (taxes|detection)",
]


def detect_pii(text: str) -> dict:
    """Detect PII in text and return findings."""
    findings = {}
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            findings[pii_type] = matches
    return findings


def detect_injection(text: str) -> bool:
    """Detect prompt injection attempts."""
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def detect_escalation(text: str) -> bool:
    """Detect topics requiring human escalation."""
    text_lower = text.lower()
    for trigger in ESCALATION_TRIGGERS:
        if trigger in text_lower:
            return True
    return False


def detect_data_extraction(text: str) -> bool:
    """Detect attempts to extract sensitive data."""
    text_lower = text.lower()
    for pattern in DATA_EXTRACTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def detect_harmful_action(text: str) -> bool:
    """Detect requests for harmful/illegal actions."""
    text_lower = text.lower()
    for pattern in HARMFUL_ACTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def redact_pii(text: str) -> str:
    """Redact detected PII from text."""
    redacted = text
    for pii_type, pattern in PII_PATTERNS.items():
        redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted, flags=re.IGNORECASE)
    return redacted


def validate_input(text: str) -> Tuple[bool, str, dict]:
    """
    Validate user input for safety.
    
    Returns:
        Tuple of (is_safe, sanitized_text, metadata)
    """
    metadata = {
        "pii_detected": False,
        "injection_detected": False,
        "escalation_required": False,
        "data_extraction_attempt": False,
        "harmful_action_attempt": False,
        "pii_findings": {},
    }
    
    # Check for prompt injection
    if detect_injection(text):
        metadata["injection_detected"] = True
        return False, "", metadata
    
    # Check for data extraction attempts
    if detect_data_extraction(text):
        metadata["data_extraction_attempt"] = True
        return False, "", metadata
    
    # Check for harmful action requests
    if detect_harmful_action(text):
        metadata["harmful_action_attempt"] = True
        return False, "", metadata
    
    # Check for PII
    pii_findings = detect_pii(text)
    if pii_findings:
        metadata["pii_detected"] = True
        metadata["pii_findings"] = pii_findings
        text = redact_pii(text)
    
    # Check for escalation
    if detect_escalation(text):
        metadata["escalation_required"] = True
    
    return True, text, metadata


# Guardrail callback for ADK integration
def input_guardrail_callback(context, user_message: str) -> Tuple[bool, str]:
    """
    ADK-compatible callback for input guardrails.
    
    Returns:
        Tuple of (should_proceed, modified_message_or_error)
    """
    is_safe, sanitized, metadata = validate_input(user_message)
    
    if not is_safe:
        if metadata["injection_detected"]:
            return False, "I'm sorry, but I cannot process that request."
    
    return True, sanitized

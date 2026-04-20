"""
Model Armor Integration - Google Cloud's safety layer for LLMs.

Provides:
- Prompt injection detection
- Jailbreak detection
- PII/sensitive data protection
- Malicious URL detection
- Harmful content filtering
"""
import os
from typing import Tuple, Dict, Any

try:
    from google.cloud import modelarmor_v1
    MODEL_ARMOR_AVAILABLE = True
except ImportError:
    MODEL_ARMOR_AVAILABLE = False
    print("Warning: google-cloud-modelarmor not installed. Using fallback guardrails.")

from google.api_core import exceptions as api_exceptions


PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")
LOCATION = os.getenv("LOCATION", "us-central1")

# Model Armor template configuration
# Templates define which protections are enabled
DEFAULT_TEMPLATE_ID = "hr-agent-safety-template"


def create_model_armor_client():
    """Create Model Armor client if available."""
    if not MODEL_ARMOR_AVAILABLE:
        return None
    return modelarmor_v1.ModelArmorClient()


def sanitize_user_prompt(
    prompt: str,
    filter_config: Dict[str, Any] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Sanitize user prompt using Model Armor.
    
    Args:
        prompt: The user's input prompt
        filter_config: Optional filter configuration
        
    Returns:
        Tuple of (is_safe, sanitized_prompt, detection_results)
    """
    if not MODEL_ARMOR_AVAILABLE:
        # Fallback to basic guardrails
        return True, prompt, {"model_armor": False, "reason": "SDK not installed"}
    
    client = create_model_armor_client()
    
    try:
        # Create sanitize request
        request = modelarmor_v1.SanitizeUserPromptRequest(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
            user_prompt_data=modelarmor_v1.DataItem(text=prompt),
            filter_config=filter_config or get_default_filter_config(),
        )
        
        response = client.sanitize_user_prompt(request=request)
        
        # Check if prompt was blocked or modified
        is_safe = response.sanitize_result.filter_match_state != \
                  modelarmor_v1.FilterMatchState.MATCH_FOUND
        
        # Get sanitized text or original
        sanitized = response.sanitize_result.sanitized_data.text \
                    if response.sanitize_result.sanitized_data.text \
                    else prompt
        
        detection_results = {
            "model_armor": True,
            "match_state": str(response.sanitize_result.filter_match_state),
            "invocation_result": str(response.sanitize_result.invocation_result),
        }
        
        return is_safe, sanitized, detection_results

    except (api_exceptions.PermissionDenied, api_exceptions.Unauthenticated) as e:
        # Fail closed on auth errors — don't silently pass unsafe prompts through
        raise RuntimeError(f"Model Armor auth failure, cannot validate prompt: {e}") from e
    except Exception as e:
        # Fail open for transient errors (network blips, quota, etc.) with a warning
        print(f"Warning: Model Armor prompt check failed with transient error: {e}")
        return True, prompt, {"model_armor": True, "error": str(e)}


def sanitize_model_response(
    response: str,
    filter_config: Dict[str, Any] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Sanitize model response using Model Armor.
    
    Args:
        response: The model's output response
        filter_config: Optional filter configuration
        
    Returns:
        Tuple of (is_safe, sanitized_response, detection_results)
    """
    if not MODEL_ARMOR_AVAILABLE:
        return True, response, {"model_armor": False, "reason": "SDK not installed"}
    
    client = create_model_armor_client()
    
    try:
        request = modelarmor_v1.SanitizeModelResponseRequest(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
            model_response_data=modelarmor_v1.DataItem(text=response),
            filter_config=filter_config or get_default_filter_config(),
        )
        
        response_result = client.sanitize_model_response(request=request)
        
        is_safe = response_result.sanitize_result.filter_match_state != \
                  modelarmor_v1.FilterMatchState.MATCH_FOUND
        
        sanitized = response_result.sanitize_result.sanitized_data.text \
                    if response_result.sanitize_result.sanitized_data.text \
                    else response
        
        detection_results = {
            "model_armor": True,
            "match_state": str(response_result.sanitize_result.filter_match_state),
        }
        
        return is_safe, sanitized, detection_results

    except (api_exceptions.PermissionDenied, api_exceptions.Unauthenticated) as e:
        raise RuntimeError(f"Model Armor auth failure, cannot validate response: {e}") from e
    except Exception as e:
        print(f"Warning: Model Armor response check failed with transient error: {e}")
        return True, response, {"model_armor": True, "error": str(e)}


def get_default_filter_config():
    """Get default filter configuration for HR agent."""
    if not MODEL_ARMOR_AVAILABLE:
        return None
        
    return modelarmor_v1.FilterConfig(
        # Enable all safety filters
        rai_settings=modelarmor_v1.RaiFilterSettings(
            rai_filters=[
                modelarmor_v1.RaiFilter(
                    filter_type=modelarmor_v1.RaiFilterType.DANGEROUS,
                    confidence_level=modelarmor_v1.ConfidenceLevel.MEDIUM_AND_ABOVE,
                ),
                modelarmor_v1.RaiFilter(
                    filter_type=modelarmor_v1.RaiFilterType.HARASSMENT,
                    confidence_level=modelarmor_v1.ConfidenceLevel.MEDIUM_AND_ABOVE,
                ),
                modelarmor_v1.RaiFilter(
                    filter_type=modelarmor_v1.RaiFilterType.HATE_SPEECH,
                    confidence_level=modelarmor_v1.ConfidenceLevel.MEDIUM_AND_ABOVE,
                ),
                modelarmor_v1.RaiFilter(
                    filter_type=modelarmor_v1.RaiFilterType.SEXUALLY_EXPLICIT,
                    confidence_level=modelarmor_v1.ConfidenceLevel.MEDIUM_AND_ABOVE,
                ),
            ]
        ),
        # Enable prompt injection / jailbreak detection
        pi_and_jailbreak_filter_settings=modelarmor_v1.PiAndJailbreakFilterSettings(
            filter_enforcement=modelarmor_v1.PiAndJailbreakFilterSettings.PiAndJailbreakFilterEnforcement.ENABLED,
            confidence_level=modelarmor_v1.ConfidenceLevel.LOW_AND_ABOVE,
        ),
        # Enable malicious URL detection
        malicious_uri_filter_settings=modelarmor_v1.MaliciousUriFilterSettings(
            filter_enforcement=modelarmor_v1.MaliciousUriFilterSettings.MaliciousUriFilterEnforcement.ENABLED,
        ),
    )


# Convenience wrapper for ADK integration
def model_armor_input_callback(context, user_message: str) -> Tuple[bool, str]:
    """ADK-compatible callback for Model Armor input filtering."""
    is_safe, sanitized, _ = sanitize_user_prompt(user_message)
    if not is_safe:
        return False, "I'm sorry, I cannot process that request."
    return True, sanitized


def model_armor_output_callback(context, agent_response: str) -> Tuple[bool, str]:
    """ADK-compatible callback for Model Armor output filtering."""
    is_safe, sanitized, _ = sanitize_model_response(agent_response)
    return True, sanitized  # Always return, but sanitized

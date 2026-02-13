import os
from typing import Generator, Any, Dict, List, Optional, Union
from vertexai.preview import reasoning_engines
from hr_agent.agents.orchestrator import hr_orchestrator


class HRAgentWrapper(reasoning_engines.AdkApp):
    """
    Wrapper for ADK Agent compatible with Vertex AI Reasoning Engine.
    Inherits from AdkApp to ensure Console compatibility (fixes Error 9).
    """
    agent_framework = "google-adk"

    def __init__(self, project_id: str = "hr-policy-agent-486811"):
        super().__init__(
            agent=hr_orchestrator,
            enable_tracing=True,
        )
        self._project_id = project_id

    def clone(self):
        """Creates a copy of this wrapper."""
        new = HRAgentWrapper(self._project_id)
        # We need to ensure internal state is copied if needed, 
        # but AdkApp might handle some of this. For now, fresh init is safer for simple agents.
        return new

    def register_operations(self) -> Dict[str, List[str]]:
        """
        Override to include 'query' in the registered operations.
        This ensures the SDK can see and call the synchronous query method.
        """
        ops = super().register_operations()
        # Add 'query' to available operations (empty string key usually denotes root/sync ops)
        if "" not in ops:
            ops[""] = []
        if "query" not in ops[""]:
            ops[""].append("query")
        return ops

    def query(
        self,
        *,
        message: str,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        run_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> str:
        """
        Synchronous query that aggregates text from the event stream.
        Compatible with both SDK and Console invocation.
        """
        response_text = []
        try:
             # Use the parent's stream_query handling which should support the agent framework
             iterator = self.stream_query(message=message, user_id=user_id, session_id=session_id)
            
             for event in iterator:
                text = ""
                # Handle ADK ModelResponse / Generic Object / Dict
                if hasattr(event, "text"):
                    text = event.text
                elif hasattr(event, "content"):
                    if isinstance(event.content, str):
                        text = event.content
                    elif hasattr(event.content, "parts"):
                            for part in event.content.parts:
                                if hasattr(part, "text"):
                                    text += part.text
                elif isinstance(event, dict):
                     content = event.get("content", {})
                     if isinstance(content, dict):
                         parts = content.get("parts", [])
                         for part in parts:
                             text += part.get("text", "")

                if text:
                    response_text.append(text)

             return "\n".join(response_text)
        except Exception as e:
            return f"Error processing query: {str(e)}"

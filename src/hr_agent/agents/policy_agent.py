"""
Policy Agent - HR Policy specialist using RAG.

Uses Vertex AI Search to answer questions about company policies.
"""
import os
from google.adk.agents import LlmAgent
# from google.adk.tools import VertexAiSearchTool # Removed
from hr_agent.tools.policy_search_tool import search_policy

from hr_agent.config import PROJECT_ID
POLICY_STORE_ID = os.getenv("POLICY_STORE_ID", "hr-policy-store-v4")

# Define the Policy Agent
policy_agent = LlmAgent(
    name="policy_agent",
    model="gemini-1.5-flash-002",
    description="Specialist agent for HR policy questions. Answers questions about company handbook, policies, and procedures.",
    instruction="""You are an HR Policy specialist. Your role is to answer questions about company policies using the employee handbook.

Rules:
1. ONLY answer based on information from the search_policy tool results
2. If the search doesn't contain relevant information, say "I don't have information about that in the policy documents"
3. Be concise and cite specific policies when possible
4. Never make up policies or information
5. For sensitive topics (termination, legal issues), recommend escalation to HR

Always ground your responses in the retrieved documents.""",
    tools=[search_policy],
)

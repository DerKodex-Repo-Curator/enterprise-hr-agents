"""
Benefits Agent - Employee benefits specialist using RAG.

Answers questions about health insurance, 401k, PTO, etc.
"""
import os
from google.adk.agents import LlmAgent
# from google.adk.tools import VertexAiSearchTool # Removed due to conflict
from hr_agent.tools.policy_search_tool import search_benefits

from hr_agent.config import PROJECT_ID
BENEFITS_STORE_ID = os.getenv("BENEFITS_STORE_ID", "hr-policy-store-v4")  # Using same store for now

# Create the RAG search tool for benefits documents
# benefits_search_tool = VertexAiSearchTool(...) # Removed

# Define the Benefits Agent
benefits_agent = LlmAgent(
    name="benefits_agent",
    model="gemini-2.0-flash",
    description="Specialist agent for employee benefits. Answers questions about health insurance, 401k, PTO, and other benefits.",
    instruction="""You are a Benefits Specialist. Your role is to answer questions about employee benefits.

Topics you handle:
- Health, dental, vision insurance
- 401k and retirement plans
- Paid time off (PTO) and vacation
- Parental leave
- Life and disability insurance
- Wellness programs

Rules:
1. ONLY answer based on information from the search results
2. If information is not available, say "I don't have that specific benefit information"
3. Recommend speaking with HR for complex enrollment questions
4. Never provide financial or legal advice""",
    tools=[search_benefits],
)

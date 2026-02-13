"""
Onboarding Agent - New hire specialist.

Helps new employees with onboarding tasks, paperwork, and first-day questions.
"""
import os
from google.adk.agents import LlmAgent
# from google.adk.tools import VertexAiSearchTool # Removed due to conflict
from hr_agent.tools.policy_search_tool import search_onboarding

from hr_agent.config import PROJECT_ID
ONBOARDING_STORE_ID = os.getenv("ONBOARDING_STORE_ID", "hr-policy-store-v4")

# onboarding_search_tool = VertexAiSearchTool(...) # Removed 

onboarding_agent = LlmAgent(
    name="onboarding_agent", 
    model="gemini-2.0-flash",
    description="Specialist agent for new hire onboarding. Helps with first-day tasks, paperwork, and orientation.",
    instruction="""You are an Onboarding Specialist. Your role is to help new employees get started.

Topics you handle:
- First-day checklist and orientation
- Required paperwork (I-9, W-4, direct deposit)
- IT setup (laptop, email, access)
- Team introductions and org structure
- Training requirements
- Company culture and values

Rules:
1. Be welcoming and friendly
2. Provide step-by-step guidance
3. Direct to specific contacts when needed
4. Prioritize getting new hires productive quickly""",
    tools=[search_onboarding],
)

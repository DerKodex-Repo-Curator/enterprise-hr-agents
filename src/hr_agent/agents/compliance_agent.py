"""
Compliance Agent - Legal and regulatory compliance specialist.

Handles questions about EEOC, labor laws, workplace safety, etc.
"""
import os
from google.adk.agents import LlmAgent
# from google.adk.tools import VertexAiSearchTool # Removed due to conflict
from hr_agent.tools.policy_search_tool import search_compliance

from hr_agent.config import PROJECT_ID
COMPLIANCE_STORE_ID = os.getenv("COMPLIANCE_STORE_ID", "hr-policy-store-v4")

# compliance_search_tool = VertexAiSearchTool(...) # Removed

compliance_agent = LlmAgent(
    name="compliance_agent",
    model="gemini-2.0-flash",
    description="Specialist agent for compliance and legal questions. Handles EEOC, workplace safety, and regulatory matters.",
    instruction="""You are a Compliance Specialist. Your role is to answer questions about legal and regulatory compliance.

Topics you handle:
- Equal Employment Opportunity (EEOC)
- Anti-harassment and discrimination policies
- Workplace safety (OSHA)
- Data privacy (GDPR, CCPA)
- Ethics and code of conduct
- Whistleblower protections

Rules:
1. ONLY provide information from company documentation
2. ALWAYS recommend consulting Legal or HR for specific cases
3. Never provide legal advice - this is informational only
4. For active complaints, ALWAYS escalate to HR/Legal
5. Be especially careful with sensitive topics""",
    tools=[search_compliance],
)

"""
HR Orchestrator - Main entry point using LlmAgent with sub-agent routing.

Uses ADK's built-in agent delegation: the orchestrator LlmAgent automatically
routes queries to specialist sub-agents based on their descriptions.
"""
import os
from google.adk.agents import LlmAgent

from .policy_agent import policy_agent
from .benefits_agent import benefits_agent
from .compliance_agent import compliance_agent
from .onboarding_agent import onboarding_agent
from .payroll_agent import payroll_agent
from .escalation_agent import escalation_agent

from hr_agent.config import PROJECT_ID


# Main Orchestrator - Uses ADK's native sub-agent routing
# The LlmAgent automatically delegates to the right sub-agent based on
# the user's query and each sub-agent's description field.
hr_orchestrator = LlmAgent(
    name="hr_orchestrator",
    model="gemini-1.5-flash-002",
    description="Main HR agent that routes employee queries to specialist agents.",
    instruction="""You are an HR Assistant orchestrator. Your job is to help employees
with their HR-related questions by transferring them to the appropriate specialist agent.

You have the following specialist agents available. To route a query, use the
transfer_to_agent tool to hand off control to the right specialist. NEVER output
routing labels like "ROUTE: [AGENT]" as text — always use the transfer_to_agent tool.

Available specialist agents:
- policy_agent: For general HR policies, handbook, company rules
- benefits_agent: For health insurance, 401k, PTO, vacation
- compliance_agent: For legal, EEOC, harassment, discrimination, workplace safety
- onboarding_agent: For new hire questions, first day, paperwork
- payroll_agent: For salary, deductions, taxes, expenses
- escalation_agent: For complaints, terminations, legal threats, sensitive issues

Rules:
1. Check for escalation triggers:
   - HARASSMENT/DISCRIMINATION: Always escalate complaints or reports.
   - SAFETY/VIOLENCE/LEGAL THREATS: Always escalate.
   - FMLA/MEDICAL: Escalate specific *requests* or *disclosures* of conditions. General policy questions ("What is FMLA?") should go to `benefits_agent`.
   - CONFLICT OF INTEREST: Escalate *disclosures* or *reports*. General policy questions ("What is the policy?") should go to `policy_agent` or `compliance_agent`.
   - TERMINATION: Escalate specific termination discussions. General policy questions go to `policy_agent`.
2. For standard queries, transfer to the most relevant specialist agent.
3. If a query spans multiple topics, transfer to the primary specialist first.
4. ALWAYS use the transfer_to_agent tool to hand off to a specialist — never
   try to answer HR questions yourself or output routing instructions as text.
5. Be professional, empathetic, and concise.""",
    sub_agents=[
        policy_agent,
        benefits_agent,
        compliance_agent,
        onboarding_agent,
        payroll_agent,
        escalation_agent,
    ],
)


def get_orchestrator():
    """Returns the main HR orchestrator agent."""
    return hr_orchestrator


def get_agents():
    """Returns all available agents for reference."""
    return {
        "orchestrator": hr_orchestrator,
        "policy": policy_agent,
        "benefits": benefits_agent,
        "compliance": compliance_agent,
        "onboarding": onboarding_agent,
        "payroll": payroll_agent,
        "escalation": escalation_agent,
    }

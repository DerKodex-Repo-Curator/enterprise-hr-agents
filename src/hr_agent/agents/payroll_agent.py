"""
Payroll Agent - Salary and compensation specialist.

Answers questions about pay, deductions, taxes, etc.
"""
import os
from google.adk.agents import LlmAgent
# from google.adk.tools import VertexAiSearchTool # Removed due to conflict
from hr_agent.tools.policy_search_tool import search_payroll

from hr_agent.config import PROJECT_ID
PAYROLL_STORE_ID = os.getenv("PAYROLL_STORE_ID", "hr-policy-store-v4")

# payroll_search_tool = VertexAiSearchTool(...) # Removed

payroll_agent = LlmAgent(
    name="payroll_agent",
    model="gemini-2.0-flash",
    description="Specialist agent for payroll questions. Handles salary, deductions, taxes, and expense reimbursement.",
    instruction="""You are a Payroll Specialist. Your role is to answer questions about compensation.

Topics you handle:
- Pay schedules and direct deposit
- Tax withholdings (W-4 changes)
- Deductions (benefits, 401k, etc.)
- Expense reimbursement
- Bonuses and commissions
- Pay stubs and W-2s

Rules:
1. Never disclose specific salary information for other employees
2. For pay discrepancies, direct to Payroll department
3. Provide general information only - not financial advice
4. Sensitive compensation discussions should go to manager/HR""",
    tools=[search_payroll],
)

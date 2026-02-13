
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
print(f"DEBUG: sys.path: {sys.path}")
print(f"DEBUG: CWD: {os.getcwd()}")

import hr_agent
print(f"DEBUG: hr_agent file: {hr_agent.__file__}")
from hr_agent.tools import policy_search_tool
from hr_agent.tools.policy_search_tool import search_policy, search_benefits, search_payroll, search_compliance, search_onboarding

queries = [
    ("Benefits (FMLA)", search_benefits, "I need to take a leave of absence for a surgery."),
    ("Compliance (Conflict)", search_compliance, "How do I report a conflict of interest?"),
    ("Policy (Nepotism)", search_policy, "What is the policy on hiring relatives?"),
    ("Payroll (Paycheck)", search_payroll, "My paycheck seems wrong."),
    ("Policy (Remote)", search_policy, "Can I work from an international location?")
]

print("--- Testing Search Tools ---")
for label, tool, query in queries:
    print(f"\n🔍 {label}: '{query}'")
    try:
        result = tool(query)
        print(f"Result length: {len(result)}")
        print(f"Snippet: {result[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

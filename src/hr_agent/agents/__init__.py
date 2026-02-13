# HR Multi-Agent System - Agents Package
"""
This package contains all specialist agents for the HR multi-agent system.

Architecture:
- orchestrator.py: ParallelAgent that routes and aggregates
- policy_agent.py: HR policies (RAG)
- benefits_agent.py: Benefits information (RAG)
- compliance_agent.py: Legal/regulatory (RAG)
- onboarding_agent.py: New hire processes (RAG)
- payroll_agent.py: Salary/tax info (RAG)
- escalation_agent.py: Routes sensitive topics to humans
"""

from .orchestrator import hr_orchestrator
from .policy_agent import policy_agent

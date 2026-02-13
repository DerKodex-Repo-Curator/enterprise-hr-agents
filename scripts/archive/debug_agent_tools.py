from hr_agent.agents.policy_agent import policy_agent
from hr_agent.agent_wrapper import HRAgentWrapper

# Initialize wrapper which sets up agents
wrapper = HRAgentWrapper()
# Force setup
if hasattr(wrapper._adk_app, "set_up"):
    wrapper._adk_app.set_up()

print(f"Agent: {policy_agent.name}")
print(f"Model: {policy_agent.model}")
print(f"Tools ({len(policy_agent.tools)}):")
for tool in policy_agent.tools:
    print(f" - {tool}")
    if hasattr(tool, "tools"):
        print(f"   - Sub-tools: {tool.tools}")

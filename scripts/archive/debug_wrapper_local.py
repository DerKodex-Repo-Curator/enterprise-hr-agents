import os
import asyncio
from hr_agent.agent_wrapper import HRAgentWrapper

# Setup env vars for local run
os.environ["PROJECT_ID"] = "hr-policy-agent-486811"
os.environ["LOCATION"] = "us-central1"

def debug_wrapper():
    print("Initializing HRAgentWrapper...")
    wrapper = HRAgentWrapper()
    
    query = "What is the vacation policy?"
    print(f"\nQuerying: {query}")
    
    # Test high-level query method
    response = wrapper.query(query, user_id="debug_user")
    print(f"\nResponse: {response}")

if __name__ == "__main__":
    debug_wrapper()

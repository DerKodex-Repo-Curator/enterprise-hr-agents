from vertexai.preview import reasoning_engines
import vertexai
import os

PROJECT_ID = "hr-agent-staging-8751"
LOCATION = "us-central1"
# RESOURCE_NAME = "projects/725040224810/locations/us-central1/reasoningEngines/8646879398714146816"

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    # We don't need the exact resource to check client methods, 
    # but we need an instance of ReasoningEngine (even if remote is mock)
    # Actually, we can just inspect the class or a dummy instance.
    # But `execution_api_client` is created on `get`.
    
    # Use list to get an instance
    client = reasoning_engines.ReasoningEngine.list(project=PROJECT_ID, location=LOCATION)
    if not client:
        print("No agents found.")
    else:
        agent = client[0]
        print("Execution Client Methods:")
        # execution_api_client is populated
        if hasattr(agent, "execution_api_client"):
            print(dir(agent.execution_api_client))
        else:
            print("No execution_api_client attribute.")
    
except Exception as e:
    print(f"Error: {e}")

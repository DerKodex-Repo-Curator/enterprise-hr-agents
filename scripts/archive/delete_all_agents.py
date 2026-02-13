import os
import vertexai
from vertexai import agent_engines

PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")
LOCATION = os.getenv("LOCATION", "us-central1")

vertexai.init(project=PROJECT_ID, location=LOCATION)

print(f"Listing reasoning engines in {PROJECT_ID}/{LOCATION}...")
try:
    print("Calling agent_engines.list()...")
    agents_gen = agent_engines.list()
    # Convert generator to list
    agents = list(agents_gen)
    print(f"List returned {len(agents)} agents.")
    
    if not agents:
        print("No agents found in list.")
    
    for agent in agents:
        print(f"Found agent: {agent.resource_name} ({agent.display_name})")
        print(f"Deleting agent: {agent.resource_name}...")
        try:
            agent.delete()
            print(f"Successfully deleted {agent.resource_name}")
        except Exception as e:
            print(f"Failed to delete {agent.resource_name}: {e}")
            
except Exception as e:
    print(f"Critical Error during listing/deletion: {e}")
    import traceback
    traceback.print_exc()

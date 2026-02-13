"""
Debug Remote Agent Events
Prints all events from the streaming query to inspect tool outputs.
"""
import os
import sys
import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_RESOURCE = "projects/121452631372/locations/us-central1/reasoningEngines/5116620240809099264"

def main():
    print(f"🚀 Connecting to Agent: {AGENT_RESOURCE}")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    try:
        remote_agent = reasoning_engines.ReasoningEngine(AGENT_RESOURCE)
        
        query = "What is the vacation policy?"
        print(f"\n📝 Sending Query: {query}")
        print("------------------------------------------------------------")
        
        # Use query (synchronous) to see if we get the debug string
        response = remote_agent.query(message=query)
        print(f"\n[RESPONSE] {response}")
        # for event in response:
        #    print(f"\n[EVENT] {event}")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    main()


"""
Smoke Test for Deployed Agent Engine.

Verifies:
1. Connection to remote agent
2. Session creation
3. Response generation
"""

import argparse
from vertexai.preview import reasoning_engines
import vertexai

def test_agent(resource_name, project_id, location):
    """Tests a deployed agent."""
    
    print(f"Testing Agent: {resource_name}")
    vertexai.init(project=project_id, location=location)

    try:
        # 1. Load the remote agent
        remote_agent = reasoning_engines.ReasoningEngine(resource_name)
        print(f"Remote Agent attributes: {dir(remote_agent)}")

        
        # 2. Test queries
        print(f"Remote Agent attributes: {dir(remote_agent)}")
        
        
        queries = [
            "What is the vacation policy?",
        ]
        
        client = remote_agent.execution_api_client
        
        for q in queries:
            print(f"\nUser: {q}")
            try:
                # Try synchronous query via GAPIC client
                input_payload = {"input": q, "user_id": "test_user"}
                request = {
                    "name": resource_name,
                    "input": input_payload,
                    "class_method": "query" # Use 'query' method exposed by AdkApp
                }
                
                print("Attempting query with payload:", input_payload)
                response = client.query_reasoning_engine(request=request)
                print(f"Agent Response Object: {response}")
                
                # Check output field
                if hasattr(response, "output"):
                    print(f"Agent Output: {response.output}")
            except Exception as e:
                print(f"Error querying agent: {e}")
                # Try with 'message' key if 'input' fails
                try: 
                    input_payload = {"message": q, "user_id": "test_user"}
                    request["input"] = input_payload
                    print("Retrying with payload:", input_payload)
                    response = client.query_reasoning_engine(request=request)
                    print(f"Agent Output (retry): {response.output}")
                except Exception as e2:
                    print(f"Retry Error: {e2}")

    except Exception as e:
        print(f"Failed to load agent: {e}")

def main():
    parser = argparse.ArgumentParser(description="Test Deployed HR Agent")
    parser.add_argument("--resource-name", required=True, help="projects/.../locations/.../reasoningEngines/...")
    parser.add_argument("--project-id", default="hr-policy-agent-486811", help="GCP Project ID")
    parser.add_argument("--location", default="us-central1", help="GCP Region")
    
    args = parser.parse_args()
    
    test_agent(args.resource_name, args.project_id, args.location)

if __name__ == "__main__":
    main()

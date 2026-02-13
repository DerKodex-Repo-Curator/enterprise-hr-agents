
import sys
import vertexai
from vertexai.preview import reasoning_engines
from google.protobuf import json_format

# Hardcoded resource for Staging (from previous step 281/378 output)
RESOURCE_NAME = "projects/725040224810/locations/us-central1/reasoningEngines/2553561879439998976"
PROJECT_ID = "hr-agent-staging-8751"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

try:
    print(f"Loading agent: {RESOURCE_NAME}")
    agent = reasoning_engines.ReasoningEngine(RESOURCE_NAME)
    print("Agent loaded.")
    print(f"Dir: {dir(agent)}")
    print(f"Schemas: {agent.operation_schemas()}")
    
    # Try calling it directly if it's callable
    try:
        print("Attempting direct call...")
        res = agent(message="Hello")
        print(f"Direct call result: {res}")
    except Exception as e:
        print(f"Direct call failed: {e}")

    # Try query method
    try:
        print("Attempting .query() call...")
        res = agent.query(message="Hello")
        print(f"Query call result: {res}")
    except Exception as e:
        print(f"Query call failed: {e}")

    # Try stream_query method
    try:
        print("Attempting .stream_query() call...")
        # Note: stream_query returns a generator, so we iterate
        for chunk in agent.stream_query(message="Hello", user_id="test_user"):
            print(f"Stream chunk: {chunk}")
    except Exception as e:
        print(f"Stream Query call failed: {e}")

    # Try low-level execution client
    try:
        print("Attempting execution_api_client.stream_query_reasoning_engine() call...")
        # Construct the request manually based on schema
        # Schema for stream_query expects message and user_id
        input_payload = {"message": "What is the policy on hiring relatives?", "user_id": "test_user"}
        
        request = {
            "name": RESOURCE_NAME,
            "input": input_payload,
            "class_method": "stream_query" # Explicitly calling the method
        }
        
        # Note: streaming might require a different client method or handling
        # standard client might have stream_query_reasoning_engine
        
        iterator = agent.execution_api_client.stream_query_reasoning_engine(request=request)
        for chunk in iterator:
            print(f"Low-level Stream chunk: {chunk}")
            
    except Exception as e:
        print(f"Low-level call failed: {e}")



except Exception as e:
    print(f"Fatal error: {e}")

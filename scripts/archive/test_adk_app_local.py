
from vertexai.preview import reasoning_engines
from hr_agent.agents.orchestrator import hr_orchestrator

def test_local():
    app = reasoning_engines.AdkApp(
        agent=hr_orchestrator,
        enable_tracing=False, # Tracing requires project setup, might fail locally if not auth'd
    )
    
    print("Querying local AdkApp...")
    try:
        # Try stream_query with required args
        for event in app.stream_query(message="Hello", user_id="test_user"):
            print(f"Event: {event} (Type: {type(event)})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_local()

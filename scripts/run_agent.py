import sys
import os

# Add src to path to resolve imports if running directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from hr_agent.agent import HRPolicyAgent, PROJECT_ID, LOCATION, DATA_STORE_ID, DATASET_ID, TABLE_ID

def main():
    if not PROJECT_ID:
        print("Please set PROJECT_ID environment variable.")
        return

    print("Initializing HR Policy Agent (Reasoning Engine)...")
    agent = HRPolicyAgent(
        project_id=PROJECT_ID,
        location=LOCATION,
        datastore_id=DATA_STORE_ID,
        dataset_id=DATASET_ID,
        table_id=TABLE_ID,
        model_name="gemini-2.0-flash"
    )
    agent.set_up()
    
    print("HR Compliance Agent Ready (Type 'quit' to exit)")
    while True:
        try:
            query = input("User: ")
            if query.lower() in ["quit", "exit"]:
                break
            
            response = agent.query(query)
            print(f"Agent: {response}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()

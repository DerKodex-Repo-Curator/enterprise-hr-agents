"""
Configure Memory Bank for the deployed HR Agent.

Uses the vertexai.Client() API to update the Agent Engine instance
with Memory Bank configuration (generational model + embedding model).
"""
import argparse
import vertexai

DEFAULT_RESOURCE_NAME = "projects/121452631372/locations/us-central1/reasoningEngines/3196820162154070016"

def configure_memory_bank(resource_name: str):
    """Configures Memory Bank on the deployed agent."""
    
    # Extract project and location from resource name
    parts = resource_name.split("/")
    project = parts[1]
    location = parts[3]
    
    print(f"📝 Configuring Memory Bank for {resource_name}...")
    
    client = vertexai.Client(project=project, location=location)
    
    # Memory Bank configuration
    embedding_model = f"projects/{project}/locations/{location}/publishers/google/models/text-embedding-005"
    generation_model = f"projects/{project}/locations/{location}/publishers/google/models/gemini-2.0-flash"
    
    memory_bank_config = {
        "similarity_search_config": {
            "embedding_model": embedding_model,
        },
        "generation_config": {
            "model": generation_model,
        },
    }
    
    # Update the agent engine with Memory Bank config
    agent_engine = client.agent_engines.update(
        name=resource_name,
        config={
            "context_spec": {
                "memory_bank_config": memory_bank_config
            }
        }
    )
    
    print("✅ Memory Bank configured!")
    print(f"  - Embedding Model: text-embedding-005")
    print(f"  - Generation Model: gemini-2.5-flash")
    print(f"  - Resource: {resource_name}")
    return agent_engine


def main():
    parser = argparse.ArgumentParser(description="Configure Memory Bank for HR Agent")
    parser.add_argument("--resource-name", default=DEFAULT_RESOURCE_NAME, help="Agent Engine resource name")
    args = parser.parse_args()
    
    configure_memory_bank(args.resource_name)


if __name__ == "__main__":
    main()


import argparse
from vertexai.preview import reasoning_engines
import vertexai

def inspect_agent(resource_name, project_id, location):
    vertexai.init(project=project_id, location=location)
    try:
        remote_agent = reasoning_engines.ReasoningEngine(resource_name)
        print("Remote Agent Attributes/Methods:")
        print(dir(remote_agent))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resource-name", required=True)
    parser.add_argument("--project-id", default="hr-policy-agent-486811")
    parser.add_argument("--location", default="us-central1")
    args = parser.parse_args()
    inspect_agent(args.resource_name, args.project_id, args.location)

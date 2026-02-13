
"""
Debug script to inspect remote Reasoning Engine environment.
Deploys a minimal agent that returns sys.path and directory listing.
"""
import os
import sys
import vertexai
from vertexai.preview import reasoning_engines

# Minimal agent that doesn't depend on ADK
class DebugAgent:
    def __init__(self):
        pass
        
    def query(self, question: str) -> str:
        """Returns environment info."""
        import os
        import sys
        
        info = []
        info.append("=== Current Working Directory ===")
        info.append(os.getcwd())
        
        info.append("\n=== Directory Listing (.) ===")
        try:
            info.append(str(os.listdir('.')))
        except Exception as e:
            info.append(f"Error listing .: {e}")
            
        info.append("\n=== Directory Listing (..) ===")
        try:
            info.append(str(os.listdir('..')))
        except Exception as e:
            info.append(f"Error listing ..: {e}")

        info.append("\n=== Directory Listing (/code if exists) ===")
        try:
            if os.path.exists('/code'):
                 info.append(str(os.listdir('/code')))
            else:
                 info.append("/code does not exist")
        except Exception as e:
            info.append(f"Error listing /code: {e}")

        info.append("\n=== sys.path ===")
        info.append(str(sys.path))
        
        return "\n".join(info)

def deploy_debug_agent(project_id, staging_bucket):
    vertexai.init(project=project_id, location="us-central1", staging_bucket=staging_bucket)
    
    agent = DebugAgent()
    
    # Try sending src/hr_agent
    print("Deploying DebugAgent with extra_packages=['src/hr_agent']...")
    remote_agent = reasoning_engines.ReasoningEngine.create(
        agent,
        requirements=[],
        display_name="debug-agent-v1",
        sys_version="3.13",
        extra_packages=["src/hr_agent"],
    )
    return remote_agent

if __name__ == "__main__":
    PROJECT_ID = "hr-policy-agent-486811"
    STAGING_BUCKET = f"gs://{PROJECT_ID}-hr-agent-staging"
    
    try:
        remote_agent = deploy_debug_agent(PROJECT_ID, STAGING_BUCKET)
        print(f"Debug Agent Deployed: {remote_agent.resource_name}")
        
        # Query it immediately
        print("Querying agent...")
        response = remote_agent.query(question="debug")
        print("Response:")
        print(response)
        
    except Exception as e:
        print(f"Deployment failed: {e}")

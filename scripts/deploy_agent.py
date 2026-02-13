
"""
Deploy HR Multi-Agent System to Vertex AI Agent Engine.

This script deploys the ADK-based HR orchestrator to Vertex AI's managed runtime.
It supports multiple environments (dev, int, staging, prod) via config/environments.yaml.

Usage:
    python scripts/deploy_agent.py --env dev
    python scripts/deploy_agent.py --env staging
"""

import os
import argparse
import yaml
import sys
from typing import Dict, Any, Optional
from vertexai import agent_engines
import vertexai
from google.cloud import aiplatform_v1beta1 as aip
from google.protobuf import field_mask_pb2

# Add src to sys.path to ensure we can import hr_agent correctly
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from hr_agent.agent_wrapper import HRAgentWrapper

# Default paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "environments.yaml")


def load_config(env: str) -> Dict[str, Any]:
    """Load configuration for the specified environment."""
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, "r") as f:
        config_data = yaml.safe_load(f)
        
    if env not in config_data.get("environments", {}):
        raise ValueError(f"Environment '{env}' not found in {CONFIG_PATH}")
        
    env_config = config_data["environments"][env]
    defaults = config_data.get("default", {})
    
    # Merge defaults with env config (env config takes precedence)
    final_config = {**defaults, **env_config}
    return final_config


def deploy_agent(env: str, config: Dict[str, Any]):
    """Deploys the agent to Vertex AI Agent Engine."""
    
    project_id = config["project_id"]
    location = config["location"]
    staging_bucket = config["staging_bucket"]
    display_name = config["display_name"]
    
    print(f"\n🚀 Deploying HR Agent to [{env}]")
    print(f"   Project: {project_id}")
    print(f"   Location: {location}")
    print(f"   Bucket: {staging_bucket}")
    print(f"   Agent Name: {display_name}")
    
    vertexai.init(project=project_id, location=location, staging_bucket=staging_bucket)

    print("   Using Real HR Agent Orchestrator")
    app = HRAgentWrapper(project_id=project_id)

    # 2. Define runtime dependencies
    requirements = [
        "google-adk>=1.5.0",
        "google-cloud-aiplatform[adk,agent-engines]>=1.93.0",
        "google-genai>=1.9.0",
        "pydantic>=2.10.6",
        "absl-py>=2.2.1",
        "python-dotenv>=1.0.1",
        "google-cloud-bigquery",
        "google-cloud-discoveryengine",
        "google-cloud-storage",
        "vertexai",
        "nest_asyncio",
        "pyyaml",  # Added for config loading in remote if needed
    ]

    # Temporary workaround: Copy src/hr_agent to root hr_agent to verify import path
    import shutil
    try:
        if os.path.exists("hr_agent"):
            shutil.rmtree("hr_agent")
        shutil.copytree("src/hr_agent", "hr_agent")
        
        # Inject Project ID into config to avoid runtime detection issues in Reasoning Engine
        config_path = os.path.join("hr_agent", "config.py")
        if os.path.exists(config_path):
            print(f"   Injecting PROJECT_ID='{project_id}' into {config_path}")
            with open(config_path, "a") as f:
                f.write(f"\n# Injected by deploy_agent.py\nPROJECT_ID = '{project_id}'\n")
        else:
            print(f"⚠️ Warning: {config_path} not found. Runtime project detection might fail.")

        # 3. Deploy
        remote_app = agent_engines.create(
            app,
            requirements=requirements,
            display_name=display_name,
            description=f"HR Multi-Agent System ({env})",
            extra_packages=["hr_agent"],
        )
        
        # 4. Configure Memory Bank if enabled
        if config.get("memory_bank", False):
            print("🔧 Configuring Memory Bank...")
            configure_memory_bank(
                project_id, 
                location, 
                remote_app.resource_name, 
                config.get("memory_bank_config", {})
            )
        else:
            print("ℹ️ Memory Bank is disabled for this environment.")
        
        print("\n✅ Deployment Successful!")
        print(f"Resource Name: {remote_app.resource_name}")
        # print(f"Operation Name: {remote_app.operation_name}")
        print("\nTo test, run:")
        print(f"python scripts/test_agent_engine.py --resource-name {remote_app.resource_name}")
        
        # Update config file with resource name (optional, best effort)
        # In a real CI/CD, we might output this to a file for downstream steps
        
        return remote_app.resource_name
        
    except Exception as e:
        print(f"\n❌ Deployment Failed: {e}")
        return None
    finally:
        # Cleanup
        if os.path.exists("hr_agent"):
            shutil.rmtree("hr_agent")


def configure_memory_bank(project_id: str, location: str, resource_name: str, config: Dict[str, str]):
    """Configures the Memory Bank for the deployed agent."""
    try:
        client = aip.ReasoningEngineServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )
        
        gen_model = config.get("generation_model", "gemini-1.5-pro-002")
        emb_model = config.get("embedding_model", "text-embedding-005")
        
        # We need to provide the Generational and Embedding models
        memory_bank_config = aip.ReasoningEngineContextSpec.MemoryBankConfig(
            generation_config=aip.ReasoningEngineContextSpec.MemoryBankConfig.GenerationConfig(
                model=f"projects/{project_id}/locations/{location}/publishers/google/models/{gen_model}"
            ),
            similarity_search_config=aip.ReasoningEngineContextSpec.MemoryBankConfig.SimilaritySearchConfig(
                embedding_model=f"projects/{project_id}/locations/{location}/publishers/google/models/{emb_model}"
            )
        )
        
        context_spec = aip.ReasoningEngineContextSpec(
            memory_bank_config=memory_bank_config
        )
        
        reasoning_engine_patch = aip.ReasoningEngine(
            name=resource_name,
            context_spec=context_spec
        )
        
        update_mask = field_mask_pb2.FieldMask(paths=["context_spec"])
        
        client.update_reasoning_engine(
            reasoning_engine=reasoning_engine_patch,
            update_mask=update_mask
        )
        print("✅ Memory Bank configured successfully.")
        
    except Exception as patch_e:
        print(f"⚠️ Warning: Failed to patch Memory Bank configuration: {patch_e}")


def main():
    parser = argparse.ArgumentParser(description="Deploy HR Agent to Vertex AI Agent Engine")
    parser.add_argument("--env", type=str, required=True, 
                        help="Target environment (dev, int, staging, prod)")
    
    args = parser.parse_args()
    
    try:
        config = load_config(args.env)
        deploy_agent(args.env, config)
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


"""
HR Agent Promotion Script.

Promotes the agent from Staging to Production.
1. Deploys the codebase to the Production environment.
2. "Replays" successful interactions from Staging to seed the Production Memory Bank.

Usage:
    python scripts/promote_agent.py
"""

import os
import sys
import json
import argparse
import subprocess
import time
from typing import List, Dict

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import vertexai
from vertexai.preview import reasoning_engines

def deploy_to_prod():
    """Run the deploy script for prod."""
    print("🚀 Promoting Code to Production...")
    try:
        # We call the deploy script as a subprocess to ensure clean state
        subprocess.check_call([sys.executable, "scripts/deploy_agent.py", "--env", "prod"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e}")
        return False

def replay_memories(agent_resource_name: str, examples_path: str):
    """Replay successful examples against the Prod agent to seed memory."""
    print(f"\n🧠 Seeding Production Memory Bank from {examples_path}...")
    
    if not os.path.exists(examples_path):
        print("⚠️ No training examples found. Skipping memory seeding.")
        return

    with open(examples_path, "r") as f:
        examples = json.load(f)

    print(f"   Found {len(examples)} memories to transfer.")
    
    try:
        agent = reasoning_engines.ReasoningEngine(agent_resource_name)
    except Exception as e:
        print(f"⚠️ Could not load remote agent: {e}")
        return

    for i, ex in enumerate(examples):
        prompt = ex["prompt"]
        print(f"   [{i+1}/{len(examples)}] Replaying: {prompt[:50]}...")
        try:
            # We just query it. The Memory Bank (if enabled) will capture this interaction.
            # Ideally, we would force the "correct" response, but standard Reasoning Engine 
            # query just generates a new one. 
            # To strictly "teach" it, we would need a fine-tuning or example-store API.
            # For this "Generational Memory" demo, re-asking high-quality questions 
            # usually yields similar high-quality answers (deterministic-ish), 
            # effectively priming the history.
            agent.query(input=prompt)
            time.sleep(1) # Rate limit protection
        except Exception as e:
            print(f"   ❌ Failed to replay: {e}")

    print("✅ Memory Seeding Complete.")

def get_prod_agent_resource():
    """Find the prod agent resource name."""
    project_id = os.environ.get("PROJECT_ID", "hr-policy-agent-486811")
    location = os.environ.get("LOCATION", "us-central1")
    agent_name = "hr-agent-prod"
    
    vertexai.init(project=project_id, location=location)
    client = vertexai.preview.reasoning_engines.ReasoningEngine.list(project=project_id, location=location)
    
    for agent in client:
        if agent.display_name == agent_name:
            return agent.resource_name
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-deploy", action="store_true", help="Skip deployment, just seed memory")
    args = parser.parse_args()

    # 1. Deploy
    if not args.skip_deploy:
        if not deploy_to_prod():
            sys.exit(1)
    
    # 2. Identify Prod Agent
    # We wait a bit for consistency if we just deployed
    print("Waiting for deployment to settle...")
    time.sleep(5) 
    
    resource_name = get_prod_agent_resource()
    if not resource_name:
        print("❌ Could not find Production Agent. Promotion incomplete.")
        sys.exit(1)
        
    print(f"found Prod Agent: {resource_name}")
    
    # 3. Transfer Memories
    replay_memories(resource_name, "data/training_success.json")
    
    print("\n✨ Promotion to Production Successful!")

if __name__ == "__main__":
    main()

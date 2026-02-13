
"""
Enterprise Setup Automation Script

This script automates the creation of GCP projects for the HR Agent.
It:
1. Prompts for a Billing Account ID.
2. Prompts for Project IDs for Dev, Staging, and Prod (offering defaults).
3. Creates the projects using `gcloud`.
4. Links them to the billing account.
5. Enables required APIs (Vertex AI, Storage, Build).
6. Updates `config/environments.yaml` with the new IDs.

Usage:
    python scripts/setup_enterprise.py
"""

import os
import sys
import subprocess
import argparse
import random
import string
import time

def run_command(cmd, check=True):
    """Run a shell command."""
    print(f"Running: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=check, executable='/bin/bash')
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return False

def get_billing_accounts():
    """Get list of available billing accounts."""
    try:
        result = subprocess.check_output("gcloud beta billing accounts list --format='value(name,displayName)'", shell=True)
        accounts = []
        for line in result.decode('utf-8').strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) >= 1:
                    accounts.append(parts[0]) # ID is usually the first part
        return accounts
    except:
        return []

def prompt_with_default(question, default):
    """Prompt user with a default value."""
    response = input(f"{question} [{default}]: ").strip()
    return response if response else default

def generate_suffix():
    """Generate a random 4-digit suffix."""
    return ''.join(random.choices(string.digits, k=4))

def setup_project(project_id, billing_account):
    """Create project, link billing, enable APIs."""
    print(f"\n🚀 Setting up project: {project_id}...")
    
    # 1. Create Project
    if not run_command(f"gcloud projects create {project_id} --name='HR Agent {project_id.split('-')[-1].capitalize()}'", check=False):
        print(f"⚠️ Project creation failed (maybe it exists?). Attempting to proceed...")

    # 2. Link Billing
    print(f"💳 Linking billing...")
    run_command(f"gcloud beta billing projects link {project_id} --billing-account={billing_account}")

    # 3. Enable APIs
    print(f"🔌 Enabling APIs (this may take a minute)...")
    apis = [
        "aiplatform.googleapis.com",
        "storage.googleapis.com",
        "cloudbuild.googleapis.com",
        "discoveryengine.googleapis.com",
        "bigquery.googleapis.com",
        "iam.googleapis.com"
    ]
    run_command(f"gcloud services enable {' '.join(apis)} --project {project_id}")

    print(f"✅ Project {project_id} setup complete.")

def update_config(dev_id, staging_id, prod_id):
    """Update environments.yaml with real IDs."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "environments.yaml")
    
    if not os.path.exists(config_path):
        print(f"❌ Config file not found at {config_path}")
        return

    with open(config_path, 'r') as f:
        content = f.read()
    
    # Simple string replacement to preserve comments
    new_content = content.replace("REPLACE_WITH_DEV_PROJECT_ID", dev_id)
    new_content = new_content.replace("REPLACE_WITH_STAGING_PROJECT_ID", staging_id)
    new_content = new_content.replace("REPLACE_WITH_PROD_PROJECT_ID", prod_id)
    
    with open(config_path, 'w') as f:
        f.write(new_content)
    
    print(f"\n📝 Updated {config_path} with new Project IDs.")

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   HR Agent - Enterprise Setup Wizard                         ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("This script will create 3 GCP projects for Dev, Staging, and Prod.\n")

    # 1. Get Billing Account
    print("Fetching billing accounts...")
    accounts = get_billing_accounts()
    if not accounts:
        print("❌ No billing accounts found. Please run 'gcloud auth login' and ensure you have billing access.")
        sys.exit(1)
    
    billing_account = accounts[0] 
    if len(accounts) > 1:
        print(f"Found multiple billing accounts. Using the first one: {billing_account}")
        # In a real CLI we might let them choose, but keep it simple as requested "default value"
    
    billing_account = prompt_with_default("Billing Account ID", billing_account)

    # 2. Get Project IDs
    suffix = generate_suffix()
    
    print("\nProposed Project IDs:")
    dev_default = f"hr-agent-dev-{suffix}"
    staging_default = f"hr-agent-staging-{suffix}"
    prod_default = f"hr-agent-prod-{suffix}"

    dev_id = prompt_with_default("Dev Project ID", dev_default)
    staging_id = prompt_with_default("Staging Project ID", staging_default)
    prod_id = prompt_with_default("Prod Project ID", prod_default)

    print(f"\nReview Plan:")
    print(f"  Dev:     {dev_id}")
    print(f"  Staging: {staging_id}")
    print(f"  Prod:    {prod_id}")
    print(f"  Billing: {billing_account}")
    
    confirm = input("\nProceed? [y/N]: ").lower()
    if confirm != 'y':
        print("Aborted.")
        sys.exit(0)

    # 3. Execute
    setup_project(dev_id, billing_account)
    setup_project(staging_id, billing_account)
    setup_project(prod_id, billing_account)

    # 4. Update Config
    update_config(dev_id, staging_id, prod_id)

    print("\n✨ Enterprise Setup Complete!")
    print("\nNext Steps:")
    print(f"1. python scripts/deploy_agent.py --env dev")

if __name__ == "__main__":
    main()

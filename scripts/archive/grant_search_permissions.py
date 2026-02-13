"""
Grant Discovery Engine Permissions to Service Account using gcloud
"""
import os
import subprocess
import json

PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")

def get_project_number(project_id):
    cmd = f"gcloud projects describe {project_id} --format='value(projectNumber)'"
    return subprocess.check_output(cmd, shell=True).decode().strip()

def run_cmd(cmd):
    print(f"Running: {cmd}")
    try:
        subprocess.check_call(cmd, shell=True)
        print("✅ Success")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")

def grant_permissions(project_id):
    print(f"Getting Project Number for {project_id}...")
    try:
        project_number = get_project_number(project_id)
    except Exception as e:
        print(f"Failed to get project number: {e}")
        return

    print(f"Project Number: {project_number}")
    
    # Default Compute Engine Service Account
    service_account_email = f"{project_number}-compute@developer.gserviceaccount.com"
    member = f"serviceAccount:{service_account_email}"
    
    roles_to_grant = [
        "roles/discoveryengine.editor",
        "roles/discoveryengine.viewer", # Redundant if editor is there, but harmless
        "roles/aiplatform.user",
        "roles/storage.objectViewer" # Read access to GCS just in case
    ]
    
    for role in roles_to_grant:
        cmd = f"gcloud projects add-iam-policy-binding {project_id} --member={member} --role={role} --condition=None"
        run_cmd(cmd)

if __name__ == "__main__":
    grant_permissions(PROJECT_ID)

import os
import argparse
from google.cloud import storage
from google.cloud import resourcemanager_v3

def fix_iam(project_id, bucket_name, project_number=None):
    # 1. Get Project Number
    if not project_number:
        rm_client = resourcemanager_v3.ProjectsClient()
        project_name = f"projects/{project_id}"
        project = rm_client.get_project(name=project_name)
        project_number = project.name.split("/")[1]
    
    print(f"Project Number: {project_number}")

    # 2. Construct Service Agent Email
    service_agent_email = f"service-{project_number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
    member = f"serviceAccount:{service_agent_email}"
    print(f"Service Agent: {member}")

    # 3. Grant Permissions on Bucket
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)

    policy = bucket.get_iam_policy(requested_policy_version=3)
    
    # Check if already has roles
    roles_to_grant = ["roles/storage.objectViewer", "roles/storage.legacyBucketReader"]
    
    for role in roles_to_grant:
        has_role = False
        for binding in policy.bindings:
            if binding["role"] == role and member in binding["members"]:
                has_role = True
                break
        
        if has_role:
            print(f"Service Agent already has {role} on {bucket_name}")
        else:
            print(f"Granting {role} to {member} on {bucket_name}...")
            policy.bindings.append({"role": role, "members": {member}})
    
    bucket.set_iam_policy(policy)
    print("Permissions update completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_id", required=True)
    parser.add_argument("--bucket_name", required=True)
    parser.add_argument("--project_number", help="Project Number (optional, to bypass lookup)")
    args = parser.parse_args()
    
    fix_iam(args.project_id, args.bucket_name, args.project_number)

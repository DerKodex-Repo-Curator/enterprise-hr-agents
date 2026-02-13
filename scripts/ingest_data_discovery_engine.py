"""
Ingest Data into Discovery Engine (Vertex AI Search)
"""
import os
import sys
from google.cloud import storage
from google.cloud import discoveryengine_v1beta as discoveryengine

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")
LOCATION = "global"  # Discovery Engine is global
DATA_DIR = "data"
BUCKET_NAME = f"{PROJECT_ID}-hr-agent-docs"

# Store IDs (Must match what is used in the agent)
STORES = {
    # Using the new v4 store that supports Content
    "policy": os.getenv("POLICY_STORE_ID", "hr-policy-store-v4"),
    "benefits": os.getenv("BENEFITS_STORE_ID", "hr-policy-store-v4"), 
    "compliance": os.getenv("COMPLIANCE_STORE_ID", "hr-policy-store-v4"),
    "payroll": os.getenv("PAYROLL_STORE_ID", "hr-policy-store-v4"),
    "onboarding": os.getenv("ONBOARDING_STORE_ID", "hr-policy-store-v4"),
}

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to gs://{bucket_name}/{destination_blob_name}.")
    return f"gs://{bucket_name}/{destination_blob_name}"

def import_documents(project_id, location, data_store_id, gcs_uri):
    """Imports documents from GCS."""
    client = discoveryengine.DocumentServiceClient()
    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        branch="default_branch",
    )

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri], data_schema="content"
        ),
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    operation = client.import_documents(request=request)
    print(f"Waiting for operation to complete: {operation.operation.name}")
    response = operation.result()
    print(f"Imported documents to {data_store_id}: {response}")

def main():
    # 1. Ensure bucket exists
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    if not bucket.exists():
        print(f"Creating bucket {BUCKET_NAME}...")
        bucket.create(location="US")
    
    # 2. Convert, Upload and Import Handbook
    handbook_path = os.path.join(DATA_DIR, "employee_handbook.md")
    if os.path.exists(handbook_path):
        import markdown
        
        # Convert MD to HTML
        with open(handbook_path, "r") as f:
            text = f.read()
        html = markdown.markdown(text)
        
        html_path = os.path.join(DATA_DIR, "employee_handbook.html")
        with open(html_path, "w") as f:
            f.write(html)
            
        print(f"Converted {handbook_path} to {html_path}")
        
        gcs_uri = upload_to_gcs(BUCKET_NAME, html_path, "employee_handbook.html")
        
        # Import to ALL relevant stores (since we might be using one shared store or split stores)
        # In this demo, defaults often point to the same store, so we'll iterate unique IDs
        processed_stores = set()
        
        for name, store_id in STORES.items():
            if store_id not in processed_stores:
                print(f"📥 Importing handbook to Store: {store_id} ({name})")
                try:
                    import_documents(PROJECT_ID, LOCATION, store_id, gcs_uri)
                    processed_stores.add(store_id)
                except Exception as e:
                    print(f"❌ Failed to import to {store_id}: {e}")
    else:
        print(f"❌ Handbook not found at {handbook_path}")

if __name__ == "__main__":
    main()

import os
import sys
from google.cloud import storage
from google.cloud import discoveryengine_v1 as discoveryengine

def upload_to_gcs(bucket_name, source_folder):
    """Uploads files from a local folder to a GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    for root, _, files in os.walk(source_folder):
        for filename in files:
            local_path = os.path.join(root, filename)
            blob_path = os.path.relpath(local_path, source_folder)
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_path)
            print(f"Uploaded {local_path} to gs://{bucket_name}/{blob_path}")

def import_documents(project_id, location, data_store_id, gcs_uri):
    """Imports documents from GCS to Vertex AI Search Data Store."""
    client = discoveryengine.DocumentServiceClient()
    parent = client.data_store_path(
        project=project_id, location=location, data_store=data_store_id
    )

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri], data_schema="content" # 'content' for unstructured
        ),
        # Options: FULL, INCREMENTAL. Defaults to INCREMENTAL if not specified? 
        # Actually default might replace? strict check needed.
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
    )

    operation = client.import_documents(request=request)
    print(f"Waiting for import operation to complete: {operation.operation.name}")
    response = operation.result()
    print(f"Import completed: {response}")

if __name__ == "__main__":
    PROJECT_ID = os.getenv("PROJECT_ID")
    BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
    DATA_STORE_ID = os.getenv("DATA_STORE_ID")
    LOCATION = os.getenv("LOCATION", "global") # or us-central1 etc.

    if not all([PROJECT_ID, BUCKET_NAME, DATA_STORE_ID]):
        print("Please set PROJECT_ID, GCS_BUCKET_NAME, and DATA_STORE_ID environment variables.")
        sys.exit(1)
    else:
        # 1. Upload
        upload_to_gcs(BUCKET_NAME, "data")
        # 2. Import
        gcs_uri = f"gs://{BUCKET_NAME}/*" # Wildcard to import all
        import_documents(PROJECT_ID, LOCATION, DATA_STORE_ID, gcs_uri)

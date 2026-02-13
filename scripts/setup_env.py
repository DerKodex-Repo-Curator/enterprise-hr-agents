
import os
import argparse
from google.cloud import storage
from google.cloud import bigquery
from google.cloud import discoveryengine
from google.api_core.exceptions import NotFound, AlreadyExists

def create_gcs_bucket(project_id, location, bucket_name):
    """Creates a GCS bucket."""
    storage_client = storage.Client(project=project_id)
    try:
        bucket = storage_client.get_bucket(bucket_name)
        print(f"Bucket {bucket_name} already exists.")
    except NotFound:
        bucket = storage_client.bucket(bucket_name)

        bucket = storage_client.create_bucket(bucket, location=location)
        print(f"Created bucket {bucket.name} in {location}")
    return bucket

def upload_blob(project_id, bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")
    return f"gs://{bucket_name}/{destination_blob_name}"

def create_bq_dataset_and_table(project_id, dataset_id, table_id, location):
    """Creates BigQuery dataset and table."""
    bq_client = bigquery.Client(project=project_id, location=location)
    dataset_ref = f"{project_id}.{dataset_id}"
    
    try:
        bq_client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_id} already exists.")
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        bq_client.create_dataset(dataset)
        print(f"Created dataset {dataset_id}")

    table_ref = f"{dataset_ref}.{table_id}"
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("query", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("response", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("reason", "STRING", mode="NULLABLE"),
    ]
    
    try:
        bq_client.get_table(table_ref)
        print(f"Table {table_id} already exists.")
    except NotFound:
        table = bigquery.Table(table_ref, schema=schema)
        bq_client.create_table(table)
        print(f"Created table {table_id}")

def create_data_store(project_id, location, data_store_id):
    """Creates a Vertex AI Search Data Store (simplified)."""
    # Note: This is complex to fully automate idempotently with all settings. 
    # This serves as a placeholder or basic implementation.
    client = discoveryengine.DataStoreServiceClient()
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
    data_store_name = f"{parent}/dataStores/{data_store_id}"
    
    try:
        client.get_data_store(name=data_store_name)
        print(f"Data Store {data_store_id} already exists.")
        return data_store_id
    except Exception as e:
        # Check if it's a NotFound
        # Creating data store requires more configuration (schema, industry vertical, etc.)
        # For this demo, we might want to guide the user to the console or assume it exists
        print(f"Data Store {data_store_id} check failed or does not exist: {e}")
        print("Please create the Data Store in Vertex AI Console if not exists.")
        return None

def main():
    parser = argparse.ArgumentParser(description="Setup GCP Environment for HR Agent")
    parser.add_argument("--project_id", required=True, help="Google Cloud Project ID")
    parser.add_argument("--location", default="us-central1", help="Google Cloud Region")
    parser.add_argument("--bucket_name", help="GCS Bucket Name (defaults to project-id-hr-data)")
    parser.add_argument("--dataset_id", default="hr_agent_logs", help="BigQuery Dataset ID")
    parser.add_argument("--table_id", default="interactions", help="BigQuery Table ID")
    parser.add_argument("--data_store_id", default="hr-policy-store", help="Vertex AI Search Data Store ID")
    
    args = parser.parse_args()
    
    bucket_name = args.bucket_name or f"{args.project_id}-hr-data"
    
    print(f"Setting up environment for project {args.project_id} in {args.location}...")
    
    # 1. GCS
    print("\n--- GCS Setup ---")
    create_gcs_bucket(args.project_id, args.location, bucket_name)
    
    # Upload Handbook
    handbook_path = os.path.join(os.path.dirname(__file__), "../data/employee_handbook.md")
    if os.path.exists(handbook_path):
        gcs_uri = upload_blob(args.project_id, bucket_name, handbook_path, "employee_handbook.md")
        print(f"Data uploaded to: {gcs_uri}")
    else:
        print(f"Warning: {handbook_path} not found. Skipping upload.")

    # 2. BigQuery
    print("\n--- BigQuery Setup ---")
    create_bq_dataset_and_table(args.project_id, args.dataset_id, args.table_id, args.location)
    
    # 3. Vertex AI Search (Placeholder)
    print("\n--- Vertex AI Search Setup ---")
    print(f"Target Data Store ID: {args.data_store_id}")
    # We skip full creation here to avoid complexity, usually done via Terraform or Console for initial setup
    # but we can check if it exists.
    create_data_store(args.project_id, "global", args.data_store_id) # Vertex AI Search is often global or multi-region

    print("\nSetup Complete!")
    print(f"Set your environment variables:")
    print(f"export PROJECT_ID={args.project_id}")
    print(f"export LOCATION={args.location}")
    print(f"export DATA_STORE_ID={args.data_store_id}")
    print(f"export BQ_DATASET_ID={args.dataset_id}")
    print(f"export BQ_TABLE_ID={args.table_id}")

if __name__ == "__main__":
    main()

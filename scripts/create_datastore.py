import logging
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine

def create_data_store(project_id: str, location: str, data_store_id: str) -> str:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/create-data-store-es#create-data-store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)

    # The full resource name of the data store
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection"

    # Initialize request argument(s)
    data_store = discoveryengine.DataStore(
        display_name="HR Policy Store v4",
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
    )

    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store=data_store,
        data_store_id=data_store_id,
    )

    # Make the request
    operation = client.create_data_store(request=request)
    print(f"Waiting for operation to complete... {operation.operation.name}")
    response = operation.result()
    print(f"Created Data Store: {response.name}")
    return response.name

def import_documents(
    project_id: str,
    location: str,
    data_store_id: str,
    gcs_uri: str,
) -> str:
    #  For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/import-documents-es#import-data
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    # The full resource name of the search engine branch.
    # e.g. projects/{project}/locations/{location}/dataStores/{data_store_id}/branches/{branch}
    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        branch="default_branch",
    )

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[gcs_uri]
        ),
        # Options: `FULL`, `INCREMENTAL`
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )

    # Make the request
    operation = client.import_documents(request=request)
    print(f"Waiting for operation to complete... {operation.operation.name}")
    response = operation.result()

    # Once the operation is complete,
    # get information from operation metadata
    metadata = discoveryengine.ImportDocumentsMetadata(operation.metadata)

    # Handle the response
    print(response)
    print(metadata)

    return operation.operation.name

if __name__ == "__main__":
    import os
    PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")
    LOCATION = "global"
    DATA_STORE_ID = "hr-policy-store-v4"
    GCS_URI = f"gs://{PROJECT_ID}-hr-data/*.md" # Import all markdown files

    try:
        print("Creating Data Store...")
        create_data_store(PROJECT_ID, LOCATION, DATA_STORE_ID)
    except Exception as e:
        print(f"Data Store creation failed (or likely already exists): {e}")

    try:
        print("Importing Documents...")
        import_documents(PROJECT_ID, LOCATION, DATA_STORE_ID, GCS_URI)
    except Exception as e:
        print(f"Import failed: {e}")

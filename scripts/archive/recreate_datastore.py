"""
Recreate Data Store with Content Support
"""
import os
import time
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine

PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")
LOCATION = "global"
# Using a NEW store ID to avoid immediate deletion consistency issues if possible, 
# or we can try to delete and wait. Let's try v4.
DATA_STORE_ID = "hr-policy-store-v4" 

def create_data_store(project_id: str, location: str, data_store_id: str) -> str:
    print(f"Creating Data Store: {data_store_id}...")
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )
    client = discoveryengine.DataStoreServiceClient(client_options=client_options)
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection"

    data_store = discoveryengine.DataStore(
        display_name="HR Policy Store V4",
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        # CRITICAL FIX: Allow content
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
    )

    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store=data_store,
        data_store_id=data_store_id,
    )

    operation = client.create_data_store(request=request)
    print(f"Waiting for creation... {operation.operation.name}")
    response = operation.result()
    print(f"Created Data Store: {response.name}")
    return response.name

if __name__ == "__main__":
    try:
        create_data_store(PROJECT_ID, LOCATION, DATA_STORE_ID)
        print("\n✅ New Data Store Created Successfully!")
        print(f"👉 Update your .env or Agent Config to use: {DATA_STORE_ID}")
    except Exception as e:
        print(f"Creation failed: {e}")

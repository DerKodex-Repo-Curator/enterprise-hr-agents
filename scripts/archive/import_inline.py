import os
from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine
from google.protobuf import struct_pb2

def create_single_document(project_id, location, data_store_id, file_path):
    """Creates a single document in the Data Store using create_document API."""
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    client = discoveryengine.DocumentServiceClient(client_options=client_options)

    # Branch path
    parent = client.branch_path(
        project=project_id,
        location=location,
        data_store=data_store_id,
        branch="default_branch",
    )

    # Read file content
    with open(file_path, "r") as f:
        content = f.read()

    # Create document ID from filename
    doc_id = os.path.basename(file_path).replace(".", "_").replace(" ", "_")

    # For CONTENT_REQUIRED data stores, we provide content via json_data
    # The content field is for extracted content, not user-provided
    # We'll use struct_data with a "content" key
    struct_data = struct_pb2.Struct()
    struct_data.fields["content"].string_value = content
    struct_data.fields["title"].string_value = os.path.basename(file_path)
    struct_data.fields["category"].string_value = "HR Policy"

    document = discoveryengine.Document(
        id=doc_id,
        struct_data=struct_data,
    )

    request = discoveryengine.CreateDocumentRequest(
        parent=parent,
        document=document,
        document_id=doc_id,
    )

    print(f"Creating document {doc_id} in {data_store_id}...")
    response = client.create_document(request=request)
    print(f"Created document: {response.name}")
    return response.name

if __name__ == "__main__":
    PROJECT_ID = "hr-policy-agent-486811"
    LOCATION = "global"
    DATA_STORE_ID = "hr-policy-store-v3"
    FILE_PATH = "data/employee_handbook.md"

    try:
        create_single_document(PROJECT_ID, LOCATION, DATA_STORE_ID, FILE_PATH)
        print("Document created successfully!")
    except Exception as e:
        print(f"Failed: {e}")

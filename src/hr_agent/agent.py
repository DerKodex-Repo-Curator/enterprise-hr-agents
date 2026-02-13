import os
import vertexai
from vertexai.preview import reasoning_engines
from vertexai.preview.generative_models import GenerativeModel, Tool, SafetySetting, Part
from vertexai.preview.generative_models import GenerativeModel, Tool, SafetySetting, Part
from .bq_logger import BigQueryLogger

# Initialize Vertex AI - Env vars expected
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
DATA_STORE_ID = os.getenv("DATA_STORE_ID", "hr-policy-store-v3")
DATASET_ID = os.getenv("BQ_DATASET_ID", "hr_agent_logs")
TABLE_ID = os.getenv("BQ_TABLE_ID", "interactions")

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)

class HRPolicyAgent:
    """HR Policy Agent using Vertex AI Reasoning Engine."""
    
    def __init__(self, project_id: str, location: str, datastore_id: str, dataset_id: str, table_id: str, model_name: str):
        self.project_id = project_id
        self.location = location
        self.datastore_id = datastore_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.model_name = model_name
        self.model = None
        self.bq_logger = None
        
    def set_up(self):
        """Initializes the model and tools."""
        # Initialize Logger
        self.bq_logger = BigQueryLogger(self.project_id, self.dataset_id, self.table_id)
        
        # Configure Tool (Vertex AI Search)
        datastore_resource_name = f"projects/{self.project_id}/locations/{self.location}/collections/default_collection/dataStores/{self.datastore_id}"
        
        tools = [
            Tool.from_retrieval(
                retrieval=vertexai.preview.generative_models.grounding.Retrieval(
                    source=vertexai.preview.generative_models.grounding.VertexAISearch(
                        datastore=self.datastore_id,
                        project=self.project_id,
                        location="global" # Vertex AI Search data stores are often global
                    )
                )
            )
        ]
        
        # Initialize Model
        # Using Gemini 3.0 Pro as requested
        self.model = GenerativeModel(
            self.model_name,
            tools=tools,
            system_instruction="You are an expert HR Policy Agent. Answer questions strictly based on the provided documents. If the answer is not in the documents, say 'I don't know'."
        )

    def query(self, question: str) -> str:
        """
        Queries the HR Policy Agent.
        
        Args:
            question: The user's question about HR policies.
            
        Returns:
            The agent's response.
        """
        if not self.model:
            self.set_up()
            
        try:
            # We use start_chat(history=[]) for a stateless single-turn query typical of Reasoning Engine entry points
            # for now, but we could also maintain history if we pass it in. 
            # For simplicity and aligning with common Reasoning Engine patterns, we'll treat it as single turn here 
            # or rely on the client to manage history if we were passing it.
            # But the requirement is just to update the model and use the engine structure.
            
            chat = self.model.start_chat()
            response = chat.send_message(question)
            text = response.text
            
            # Grounding check (simplified for now, consistent with previous logic)
            grounding_metadata = response.candidates[0].grounding_metadata
            has_attribution = False
            if grounding_metadata and grounding_metadata.grounding_chunks:
                has_attribution = True
                
            final_response = text
            log_reason = "Success"
            
            if not has_attribution and "I don't know" not in text:
                 final_response = "I don't know. (Reason: answer not grounded in policy documents)"
                 log_reason = "Low Grounding / No Citations"
            
            # Log to BigQuery
            if self.bq_logger:
                self.bq_logger.log_interaction(question, final_response, reason=log_reason)
                
            return final_response
            
        except Exception as e:
            print(f"Error: {e}")
            if self.bq_logger:
                self.bq_logger.log_interaction(question, "Error", reason=str(e))
            return f"I'm sorry, I encountered an error: {str(e)}"

# Reasoning Engine Deployment
# To deploy: 
# reasoning_engines.ReasoningEngine.create(
#     HRPolicyAgent(
#         project_id=PROJECT_ID,
#         location=LOCATION,
#         datastore_id=DATA_STORE_ID,
#         dataset_id=DATASET_ID,
#         table_id=TABLE_ID,
#         model_name="gemini-3.0-pro-preview"
#     ),
#     requirements=["google-cloud-aiplatform", "google-cloud-bigquery", "google-cloud-discoveryengine"]
# )

if __name__ == "__main__":
    # Local verification loop
    if not PROJECT_ID:
        print("Set setup env vars first.")
    else:
        print("HR Compliance Agent (Reasoning Engine Mode) - Type 'quit' to exit")
        # We need to manually call set_up for local execution if not using the engine wrapper's deployment
        # The ReasoningEngine wrapper might not auto-call set_up when just instantiating the class, 
        # but the `agent` object above is the Engine. 
        # Actually, when running locally we can just use the instance.
        
        local_agent = HRPolicyAgent(
            project_id=PROJECT_ID,
            location=LOCATION,
            datastore_id=DATA_STORE_ID,
            dataset_id=DATASET_ID,
            table_id=TABLE_ID,
            model_name="gemini-3.0-pro-preview"
        )
        local_agent.set_up()
        
        while True:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit"]:
                break
            
            response = local_agent.query(user_input)
            print(f"Agent: {response}")

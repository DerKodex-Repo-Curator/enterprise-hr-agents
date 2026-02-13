import datetime
from google.cloud import bigquery
import os

class BigQueryLogger:
    def __init__(self, project_id, dataset_id, table_id):
        self.client = bigquery.Client(project=project_id)
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("query", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("response", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("reason", "STRING", mode="NULLABLE"),
        ]
        try:
            self.client.get_table(self.table_ref)
        except Exception:
            # Create table if it doesn't exist
            table = bigquery.Table(self.table_ref, schema=schema)
            self.client.create_table(table)
            print(f"Created table {self.table_ref}")

    def log_interaction(self, query, response, reason=None):
        rows_to_insert = [
            {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "query": query,
                "response": response,
                "reason": reason
            }
        ]
        errors = self.client.insert_rows_json(self.table_ref, rows_to_insert)
        if errors:
            print(f"Encountered errors while inserting rows: {errors}")
        else:
            print("Logged interaction to BigQuery.")

if __name__ == "__main__":
    # Test logging
    PROJECT_ID = os.getenv("PROJECT_ID", "your-project-id")
    logger = BigQueryLogger(PROJECT_ID, "hr_agent_logs", "interactions")
    logger.log_interaction("Test Query", "I don't know.", "Low Grounding")

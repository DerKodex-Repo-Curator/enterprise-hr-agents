# Acme Corp HR Agent

This project implements an enterprise-grade HR policy agent for "Acme Corp", leveraging Google Cloud Vertex AI's Reasoning Engine and Agent Development Kit (ADK).

The agent is designed to assist employees with inquiries about company policies, benefits, payroll, and more, using a multi-agent orchestration pattern.

## Architecture

The system uses a **Hub-and-Spoke** architecture where a central **Orchestrator Agent** delegates specialized queries to domain-specific sub-agents.

![Architecture Diagram](docs/architecture.mmd)

### Components

*   **`HRAgentWrapper`**: A custom wrapper extending the Vertex AI `AdkApp`. It handles:
    *   Session management.
    *   Integration with the Reasoning Engine runtime.
    *   **Correct Invocation**: Bridges the gap between the synchronous `query()` interface and the asynchronous `stream_query()` method of the underlying ADK agent.
*   **`hr_orchestrator` (`LlmAgent`)**: The main entry point. It understands user intent and routes queries to the appropriate specialist.
*   **Sub-Agents**:
    *   **Policy Agent**: Answers general policy questions (PTO, Remote Work, etc.) using `policy_search_tool`.
    *   **Benefits Agent**: Handles 401k, insurance, and enrollment queries.
    *   **Payroll Agent**: Addresses salary, tax, and pay stub questions.
    *   **Onboarding Agent**: Guides new hires through the onboarding process.

## Setup & Configuration

1.  **Environment Configuration**:
    *   Edit `config/environments.yaml` to define project IDs, locations, and staging buckets for `dev`, `staging`, and `prod` environments.
    

2.  **Prerequisites**:
    *   Python 3.9+
    *   Install dependencies:
        ```bash
        pip install -r requirements.txt
        ```

3.  **Authentication**:
    *   Maximize your terminal and authenticate with `gcloud`:
        ```bash
        gcloud auth login
        gcloud config set project <YOUR_PROJECT_ID>
        ```

> [!NOTE]
> **For Developers**: This project uses a custom deployment script (`scripts/deploy_agent.py`) rather than the standard `adk deploy` command. This script handles:
> *   **Runtime Wrapping**: Ensures the agent is correctly wrapped to handle Vertex AI's async streaming interface.
> *   **Configuration**: Injects environment-specific settings (project ID, buckets).
> *   **Packaging**: Bundles local source code correctly.
>
> Please use the python scripts provided below for all deployments. The `agent.yaml` file is included for reference but is not currently used by the deployment pipeline.

## Deployment

Deploy the agent to Vertex AI Reason Engine using the deployment script:

```bash
# Deploy to Development
python scripts/deploy_agent.py --env dev

# Deploy to Staging (if configured)
python scripts/deploy_agent.py --env staging
```

This script handles:
*   Packaging dependencies (including local `src/` code).
*   Creating/Updating the Reasoning Engine resource.
*   Configuring the Memory Bank (if enabled).

## Usage & Evaluation

Once deployed, you can interact with the agent using the provided evaluation tools.

### Live Chat / Smoke Test
Use `scripts/test_agent_engine.py` for a quick interactive session:
```bash
python scripts/test_agent_engine.py --resource-name <YOUR_AGENT_RESOURCE_NAME>
```

### Automated Evaluation
Run the evaluation suite against a golden dataset (`data/golden_dataset.jsonl`) to measure accuracy and latency:
```bash
python eval/run_agent_eval.py --resource-name <YOUR_AGENT_RESOURCE_NAME>
```

## Directory Structure

*   `src/`: Agent source code (agents, tools, wrappers).
*   `config/`: Environment configurations.
*   `data/`: Employee handbook and golden datasets.
*   `scripts/`: Deployment and utility scripts.
*   `eval/`: Evaluation logic and metrics.
*   `docs/`: Documentation and architecture diagrams.

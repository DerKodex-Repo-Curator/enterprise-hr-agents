# Enterprise Setup Guide: Multi-Project Isolation

This guide explains how to set up "Physical Isolation" for your HR Agent by deploying to separate Google Cloud Projects.

## 1. Create Projects

You need three distinct GCP projects. This creates hard boundaries for data, quota, and access.

| Environment | Suggested Project ID Pattern | Purpose |
| :--- | :--- | :--- |
| **Dev** | `hr-agent-dev-[unique-id]` | Developers deploy here for testing. |
| **Staging** | `hr-agent-staging-[unique-id]` | CI/CD deploys here for training & eval. |
| **Prod** | `hr-agent-prod-[unique-id]` | Locked down. Only CI/CD promotes here. |
| **Ops/Build** | `hr-agent-ops-[unique-id]` | (Optional) Hosts Cloud Build & Artifact Registry. |

*If you don't have an Ops project, you can run Cloud Build in the Dev or Staging project.*

### Commands
```bash
# Create projects (replace [id] with your actual suffixes)
gcloud projects create hr-agent-dev-[id] --name="HR Agent Dev"
gcloud projects create hr-agent-staging-[id] --name="HR Agent Staging"
gcloud projects create hr-agent-prod-[id] --name="HR Agent Prod"

# Enable Billing (Required for Vertex AI)
# Link each project to your billing account
gcloud beta billing projects link hr-agent-dev-[id] --billing-account=[YOUR_BILLING_ACCOUNT_ID]
# ... repeat for staging and prod
```

## 2. Enable APIs

Enable the required APIs in **ALL** projects.

```bash
# Loop through your projects
for PROJECT in hr-agent-dev-[id] hr-agent-staging-[id] hr-agent-prod-[id]; do
  gcloud services enable aiplatform.googleapis.com \
                         storage.googleapis.com \
                         cloudbuild.googleapis.com \
                         discoveryengine.googleapis.com \
                         bigquery.googleapis.com \
                         --project $PROJECT
done
```

## 3. Cross-Project IAM for CI/CD

If running Cloud Build in one project (e.g., `dev` or `ops`), its Service Account needs permission to deploy to the others.

1.  **Identify Cloud Build Service Account**:
    ```bash
    BUILD_PROJECT_ID=hr-agent-dev-[id] # Or wherever you run builds
    BUILD_SA=$(gcloud projects describe $BUILD_PROJECT_ID \
        --format="value(projectNumber)")@cloudbuild.gserviceaccount.com
    ```

2.  **Grant Permissions in Target Projects**:
    Grant `Vertex AI Administrator` and `Storage Admin` to the Build SA in Staging and Prod.

    ```bash
    # Grant in Staging
    gcloud projects add-iam-policy-binding hr-agent-staging-[id] \
        --member="serviceAccount:$BUILD_SA" \
        --role="roles/aiplatform.admin"

    gcloud projects add-iam-policy-binding hr-agent-staging-[id] \
        --member="serviceAccount:$BUILD_SA" \
        --role="roles/storage.admin"

    # Grant in Prod
    gcloud projects add-iam-policy-binding hr-agent-prod-[id] \
        --member="serviceAccount:$BUILD_SA" \
        --role="roles/aiplatform.admin"

    gcloud projects add-iam-policy-binding hr-agent-prod-[id] \
        --member="serviceAccount:$BUILD_SA" \
        --role="roles/storage.admin"
    ```

## 4. Updates Configuration

Once created, update `config/environments.yaml` with the new Project IDs.

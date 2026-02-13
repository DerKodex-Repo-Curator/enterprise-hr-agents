import os

# Default configuration
# This file is modified during deployment to inject environment-specific values
PROJECT_ID = os.getenv("PROJECT_ID", "hr-policy-agent-486811")

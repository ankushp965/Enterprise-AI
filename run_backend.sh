#!/bin/bash

# Navigate to the directory where the script is located (project root)
cd "$(dirname "$0")"

echo "Starting FastAPI Backend..."
# Activate the virtual environment and start the Uvicorn server
source venv/bin/activate
uvicorn app.api:app --reload
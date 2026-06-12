#!/bin/bash

# Navigate to the directory where the script is located (project root)
cd "$(dirname "$0")"

echo "Generating traces in Arize Phoenix..."
# Activate the virtual environment
source venv/bin/activate

# Run the python script
python scripts/generate_traces.py

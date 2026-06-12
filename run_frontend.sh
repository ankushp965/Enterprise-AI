#!/bin/bash

# Navigate to the directory where the script is located (project root)
cd "$(dirname "$0")"

echo "Starting React Frontend..."
cd frontend
npm run dev

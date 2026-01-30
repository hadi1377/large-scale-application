#!/bin/bash
set -e

echo "Running seed command..."
python seed.py

echo "Starting FastAPI server..."
# Use command arguments if provided, otherwise use default
if [ $# -eq 0 ]; then
    exec uvicorn main:app --host 0.0.0.0 --port 8000
else
    exec "$@"
fi


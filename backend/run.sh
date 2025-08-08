#!/bin/bash
# Backend startup script

echo "Starting JIRA Sync Dashboard Backend..."

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Load environment variables
if [ -f "../.env" ]; then
    echo "Loading environment variables..."
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Use venv's python directly
VENV_PYTHON="./venv/bin/python3"
VENV_PIP="./venv/bin/pip3"

# Upgrade pip in virtual environment
echo "Upgrading pip..."
$VENV_PIP install --upgrade pip

# Install requirements in virtual environment
echo "Installing/updating requirements..."
$VENV_PIP install -r requirements.txt

# Start FastAPI with uvicorn using venv's python
echo "Starting FastAPI server on http://127.0.0.1:8987"
$VENV_PYTHON -m uvicorn main:app --host 127.0.0.1 --port 8987 --reload
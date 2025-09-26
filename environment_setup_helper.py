#!/bin/bash
# This helper script sets up the environment for the entire pipeline using uv.

echo "--- Initializing Environment Setup ---"

# Check for uv and install if missing
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.cargo/env"
    if ! command -v uv &> /dev/null; then
        echo "ERROR: uv installation failed."
        exit 1
    fi
else
    echo "uv is already installed."
fi

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating new virtual environment '.venv'..."
    uv venv
else
    echo "Using existing '.venv' directory."
fi

# Activate venv and install all dependencies for the entire pipeline
source .venv/bin/activate
echo "Installing/verifying all pipeline dependencies..."
uv pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Dependency installation failed."
    exit 1
fi

echo "Environment setup complete."


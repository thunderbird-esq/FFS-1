#!/bin/bash
# environment_setup_helper.sh
#
# This script is responsible for preparing the Python virtual environment.
# It ensures 'uv' is installed, creates a virtual environment, and synchronizes
# it with the dependencies specified in requirements.txt.
# It is designed to be idempotent and can be run safely multiple times.

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error.
set -u

echo "--- Initializing Environment Setup ---"

# --- Step 1: Ensure uv is installed ---

if command -v uv &> /dev/null; then
    echo "INFO: uv is already installed."
else
    echo "INFO: uv not found. Installing now..."
    # Using the recommended installation method from the uv project
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to the current session's PATH
    source "$HOME/.cargo/env"
    echo "INFO: uv has been installed."
fi

# --- Step 2: Create or validate the virtual environment ---

VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "INFO: Creating Python virtual environment at './${VENV_DIR}'..."
    uv venv "$VENV_DIR" -p python3
    echo "INFO: Virtual environment created."
else
    echo "INFO: Using existing '${VENV_DIR}' directory."
fi

# Activate the virtual environment
source "${VENV_DIR}/bin/activate"

# --- Step 3: Synchronize dependencies ---

REQUIREMENTS_FILE="requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "ERROR: ${REQUIREMENTS_FILE} not found. Cannot install dependencies."
    exit 1
fi

echo "INFO: Synchronizing environment with '${REQUIREMENTS_FILE}'..."
# 'uv pip sync' is idempotent: it ensures the environment exactly matches
# the requirements file, adding missing packages and removing extraneous ones.
uv pip sync "$REQUIREMENTS_FILE"

echo "--- Environment setup complete. ---"



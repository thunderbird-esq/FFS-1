#!/bin/bash
# environment_setup_helper.sh
#
# This script is responsible for preparing a reliable and reproducible execution environment.
# It validates system dependencies, ensures 'uv' is installed, creates a virtual
# environment, and synchronizes it with the dependencies in requirements.txt.
# It is designed to be idempotent and can be run safely multiple times.

# --- Strict Mode ---
# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error.
set -u
# Exit if any command in a pipeline fails.
set -o pipefail

# --- Color Definitions for Logging ---
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Logging Functions ---
# Note: These are standalone so the script can be run independently for debugging.
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"
}
log_error() {
    echo -e "${RED}[ERROR]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"
}

# --- Core Functions ---

validate_system_dependencies() {
    log_info "Validating required system dependencies..."
    local missing_deps=0
    
    # Check for Homebrew itself first
    if ! command -v brew &> /dev/null; then
        log_error "Homebrew is not installed. Please install it from https://brew.sh/"
        missing_deps=$((missing_deps + 1))
    fi

    # Check for Tesseract and Poppler
    for dep in tesseract poppler; do
        if ! brew list "$dep" &> /dev/null; then
            log_error "System dependency '$dep' is not installed via Homebrew. Please run: brew install $dep"
            missing_deps=$((missing_deps + 1))
        fi
    done

    if [ $missing_deps -gt 0 ]; then
        log_error "Halting setup due to missing system dependencies."
        exit 1
    fi
    log_info "All system dependencies are satisfied."
}

ensure_uv_installed() {
    log_info "Checking for 'uv' installer..."
    if command -v uv &> /dev/null; then
        log_info "'uv' is already installed."
    else
        log_info "'uv' not found. Installing now via official script..."
        # Using the recommended installation method from the uv project
        if curl -LsSf https://astral.sh/uv/install.sh | sh; then
            # Add uv to the current session's PATH
            source "$HOME/.cargo/env"
            log_info "'uv' has been installed successfully."
        else
            log_error "Failed to install 'uv'. Please check your network connection or try installing it manually."
            exit 1
        fi
    fi
}

setup_python_environment() {
    local venv_dir=".venv"
    local requirements_file="requirements.txt"

    log_info "Setting up Python virtual environment..."
    if [ ! -d "$venv_dir" ]; then
        log_info "Creating Python virtual environment at './${venv_dir}'..."
        uv venv "$venv_dir" -p python3
        log_info "Virtual environment created."
    else
        log_info "Using existing '${venv_dir}' directory."
    fi

    # Activate the virtual environment for the dependency sync
    source "${venv_dir}/bin/activate"

    if [ ! -f "$requirements_file" ]; then
        log_error "'${requirements_file}' not found. Cannot install dependencies."
        exit 1
    fi

    log_info "Synchronizing environment with '${requirements_file}'..."
    # 'uv pip sync' is idempotent: it ensures the environment *exactly* matches
    # the requirements file, adding missing packages and removing extraneous ones.
    if uv pip sync "$requirements_file"; then
        log_info "Python environment is synchronized and ready."
    else
        log_error "Dependency synchronization failed. Please check the output above."
        exit 1
    fi
}


# --- Main Execution Logic ---
main() {
    echo -e "${BLUE}--- Initializing Environment Setup ---${NC}"
    
    validate_system_dependencies
    ensure_uv_installed
    setup_python_environment
    
    echo -e "${GREEN}--- Environment Setup Complete ---${NC}"
}

# Run the main function
main


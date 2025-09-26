#!/bin/bash
# run_pipeline.sh - Master Pipeline Orchestration Script
#
# This script manages the entire 3-stage document processing pipeline.
# It handles environment setup, configuration, and sequential execution of each stage,
# with robust logging and error handling.

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

# --- Logging Configuration ---
LOG_DIR="pipeline_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MAIN_LOG="${LOG_DIR}/pipeline_${TIMESTAMP}.log"
ERROR_LOG="${LOG_DIR}/errors_${TIMESTAMP}.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# --- Logging Functions ---
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "$MAIN_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "$MAIN_LOG" "$ERROR_LOG"
}

log_stage() {
    echo -e "\n${BLUE}>>> STAGE: $1${NC}\n" | tee -a "$MAIN_LOG"
}

# --- Pipeline Configuration ---
# All paths are defined here as the single source of truth.
PDF_SOURCE_DIR="."
STAGE1_MD_DIR="preprocessed_markdown"
STAGE1_ASSET_DIR="document_assets"
STAGE2_MD_DIR="final_markdown"
STAGE3_OUTPUT_DIR="markitdown_output"

# --- Main Pipeline Logic ---
main() {
    log_info "--- Starting Document Processing Pipeline ---"

    # Step 1: Set up the environment
    log_stage "ENVIRONMENT SETUP"
    ./environment_setup_helper.sh

    # Activate the virtual environment for this script's session
    source .venv/bin/activate
    log_info "Virtual environment activated."

    # Load secrets from .env file into the environment if it exists
    if [ -f .env ]; then
        log_info "Loading secrets from .env file."
        export $(grep -v '^#' .env | xargs)
    else
        log_info "No .env file found, assuming environment variables are set externally."
    fi

    # Step 2: Execute Stage 1
    log_stage "STAGE 1: OCR and Image Extraction"
    python3 stage_1_processing.py \
        --pdf-dir "${PDF_SOURCE_DIR}" \
        --md-dir "${STAGE1_MD_DIR}" \
        --asset-dir "${STAGE1_ASSET_DIR}"

    # Step 3: Execute Stage 2
    log_stage "STAGE 2: LLM Vision Analysis and Text Cleanup"
    python3 stage_2_processing.py \
        --source-md-dir "${STAGE1_MD_DIR}" \
        --asset-dir "${STAGE1_ASSET_DIR}" \
        --output-dir "${STAGE2_MD_DIR}"

    # Step 4: Execute Stage 3
    log_stage "STAGE 3: Markitdown Final Processing"
    python3 stage_3_processing.py \
        --source-dir "${STAGE2_MD_DIR}" \
        --output-dir "${STAGE3_OUTPUT_DIR}"

    log_info "--- Document Processing Pipeline Finished Successfully ---"
}

# --- Script Entry Point ---
# The 'main' function is called to start the pipeline.
# Any errors will cause the script to exit due to 'set -e'.
main


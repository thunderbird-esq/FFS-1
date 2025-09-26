#!/bin/bash
# run_pipeline.sh - Definitive Master Pipeline Orchestration Script
#
# This script manages the entire 3-stage document processing pipeline.
# It handles environment setup, configuration, pre-flight checks,
# sequential execution with timeouts, and post-flight validation.

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
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Logging Configuration ---
LOG_DIR="pipeline_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MAIN_LOG="${LOG_DIR}/pipeline_${TIMESTAMP}.log"
ERROR_LOG="${LOG_DIR}/errors.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# --- Logging Functions ---
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "$MAIN_LOG"
}
log_error() {
    echo -e "${RED}[ERROR]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "$MAIN_LOG" >> "$ERROR_LOG"
}
log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "$MAIN_LOG"
}
log_stage() {
    echo -e "\n${BLUE}>>> STAGE: $1${NC}\n" | tee -a "$MAIN_LOG"
}

# --- Centralized Configuration ---
PDF_SOURCE_DIR="."
STAGE1_MD_DIR="preprocessed_markdown"
STAGE1_ASSET_DIR="document_assets"
STAGE2_MD_DIR="final_markdown"
STAGE3_OUTPUT_DIR="markitdown_output"

# Timeouts in seconds (e.g., 3600s = 1 hour)
STAGE1_TIMEOUT=3600
STAGE2_TIMEOUT=7200
STAGE3_TIMEOUT=3600

# --- Helper Functions ---

validate_system_deps() {
    log_info "Running pre-flight check: Validating system dependencies..."
    local missing_deps=0
    for dep in uv tesseract poppler; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "System dependency '$dep' not found. Please install it."
            missing_deps=$((missing_deps + 1))
        fi
    done
    if [ $missing_deps -gt 0 ]; then
        log_error "Halting pipeline due to missing system dependencies."
        exit 1
    fi
    log_info "System dependencies are satisfied."
}

validate_azure_creds() {
    log_info "Running pre-flight check: Validating Azure credentials..."
    local missing_vars=0
    local required_vars=(
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
        "AZURE_DOCUMENT_INTELLIGENCE_KEY"
        "AZURE_OPENAI_ENDPOINT"
        "AZURE_OPENAI_KEY"
        "AZURE_OPENAI_DEPLOYMENT_NAME"
        "OPENAI_API_VERSION"
    )
    for var in "${required_vars[@]}"; do
        if [ -z "${!var-}" ]; then
            log_error "Environment variable '$var' is not set. Please set it before running."
            missing_vars=$((missing_vars + 1))
        fi
    done
    if [ $missing_vars -gt 0 ]; then
        log_error "Halting pipeline due to missing Azure credentials."
        exit 1
    fi
    log_info "Azure credentials are set."
}

check_for_pdfs() {
    log_info "Running pre-flight check: Looking for source PDF files..."
    if ! ls ${PDF_SOURCE_DIR}/*.pdf 1> /dev/null 2>&1; then
        log_error "No PDF files found in '${PDF_SOURCE_DIR}'. Nothing to process."
        exit 1
    fi
    local count=$(ls ${PDF_SOURCE_DIR}/*.pdf | wc -l | xargs)
    log_info "Found ${count} PDF file(s) to process."
}

execute_stage() {
    local stage_num=$1
    local stage_name=$2
    local stage_script=$3
    local stage_timeout=$4
    shift 4 # All remaining arguments are for the python script
    
    log_stage "STAGE ${stage_num}: ${stage_name}"
    
    if timeout "${stage_timeout}" python3 "${stage_script}" "$@"; then
        log_info "Stage ${stage_num} completed successfully."
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_error "Stage ${stage_num} failed: Timed out after ${stage_timeout} seconds."
        else
            log_error "Stage ${stage_num} failed with exit code ${exit_code}."
        fi
        exit 1
    fi
}

validate_outputs() {
    log_info "Running post-flight check: Validating pipeline outputs..."
    local errors=0
    for dir in "$STAGE1_MD_DIR" "$STAGE1_ASSET_DIR" "$STAGE2_MD_DIR" "$STAGE3_OUTPUT_DIR"; do
        if [ ! -d "$dir" ] || [ -z "$(ls -A "$dir")" ]; then
            log_error "Validation failed: Output directory '$dir' is missing or empty."
            errors=$((errors + 1))
        fi
    done
    if [ $errors -gt 0 ]; then
        log_error "Pipeline finished with validation errors."
        exit 1
    fi
    log_info "All output directories contain data. Validation successful."
}

# --- Main Pipeline Execution ---
main() {
    local pipeline_start_time=$(date +%s)
    log_info "--- Document Processing Pipeline Initializing ---"

    # Load secrets from .env file if it exists
    if [ -f .env ]; then
        log_info "Loading secrets from .env file."
        export $(grep -v '^#' .env | xargs)
    else
        log_warning "No .env file found. Assuming environment variables are set externally."
    fi

    # Run pre-flight checks
    validate_system_deps
    validate_azure_creds
    check_for_pdfs

    # Setup Python environment
    log_stage "ENVIRONMENT SETUP"
    ./environment_setup_helper.sh
    source .venv/bin/activate
    log_info "Virtual environment is ready."
    
    # Run pipeline stages
    execute_stage 1 "OCR and Asset Extraction" "stage_1_processing.py" "$STAGE1_TIMEOUT" \
        --pdf-dir "$PDF_SOURCE_DIR" \
        --md-dir "$STAGE1_MD_DIR" \
        --asset-dir "$STAGE1_ASSET_DIR"

    execute_stage 2 "LLM Vision and Cleanup" "stage_2_processing.py" "$STAGE2_TIMEOUT" \
        --source-md-dir "$STAGE1_MD_DIR" \
        --asset-dir "$STAGE1_ASSET_DIR" \
        --output-dir "$STAGE2_MD_DIR"

    execute_stage 3 "Final Document Synthesis" "stage_3_processing.py" "$STAGE3_TIMEOUT" \
        --source-dir "$STAGE2_MD_DIR" \
        --output-dir "$STAGE3_OUTPUT_DIR"
    
    # Run post-flight validation
    validate_outputs
    
    local pipeline_end_time=$(date +%s)
    local duration=$((pipeline_end_time - pipeline_start_time))
    
    log_info "--- Document Processing Pipeline Finished Successfully ---"
    log_info "Total execution time: ${duration} seconds."
    log_info "All logs saved in '${LOG_DIR}'."
    log_info "Final documents are available in '${STAGE3_OUTPUT_DIR}'."
}

# Run the main function and handle potential errors
main


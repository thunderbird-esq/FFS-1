#!/bin/bash
# Master pipeline script - robust, configurable, and fails fast.

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error.
set -u
# Exit if any command in a pipeline fails.
set -o pipefail

echo "--- Starting Document Processing Pipeline ---"

# --- Configuration ---
# All paths are now defined here. No hardcoding in Python scripts.
export PDF_SOURCE_DIR="."
export STAGE1_OUTPUT_MD_DIR="preprocessed_markdown"
export STAGE1_OUTPUT_ASSET_DIR="document_assets"
export STAGE2_OUTPUT_MD_DIR="final_markdown"
export STAGE3_OUTPUT_DIR="markitdown_output"

# Load secrets from .env file into the environment
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# --- Environment Setup ---
echo "INFO: Setting up Python environment..."
# (Assuming setup_pipeline_env.sh or similar has been run to create venv and install requirements)
if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment .venv not found. Please run the setup script."
    exit 1
fi
source .venv/bin/activate
echo "INFO: Virtual environment activated."

# --- Execute Pipeline Stages ---
echo "INFO: Executing Stage 1: OCR and Image Extraction..."
python3 stage_1_processing_final.py \
  --pdf-dir "${PDF_SOURCE_DIR}" \
  --md-dir "${STAGE1_OUTPUT_MD_DIR}" \
  --asset-dir "${STAGE1_OUTPUT_ASSET_DIR}"

echo "INFO: Executing Stage 2: LLM Vision Analysis and Cleanup..."
python3 stage_2_processing_enhanced.py \
  --source-md-dir "${STAGE1_OUTPUT_MD_DIR}" \
  --asset-dir "${STAGE1_OUTPUT_ASSET_DIR}" \
  --output-dir "${STAGE2_OUTPUT_MD_DIR}"

echo "INFO: Executing Stage 3: Final Markitdown Processing..."
python3 stage_3_processing_final.py \
  --source-dir "${STAGE2_OUTPUT_MD_DIR}" \
  --output-dir "${STAGE3_OUTPUT_DIR}"

echo "--- Document Processing Pipeline Finished Successfully ---"

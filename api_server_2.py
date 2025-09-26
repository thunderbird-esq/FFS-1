# api_server.py
#
# This script creates a fully functional FastAPI web server that acts as a
# front-end for the document processing pipeline. It exposes an endpoint
# to upload a PDF, which then triggers the full 3-stage pipeline as a
# background task using the actual, imported processing functions.

import os
import shutil
import logging
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from typing import Dict, Any

# --- Direct imports of the core processing functions from our pipeline scripts ---
# These are the actual workhorses of the pipeline.
from stage_1_processing import process_single_pdf
from stage_2_processing import initialize_llm, process_single_document
from stage_3_processing import initialize_markitdown_client, process_single_markdown_file

# --- Centralized Pipeline Configuration ---
# All directory paths are managed here, providing a single source of truth.
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "api_uploads"
STAGE1_MD_DIR = BASE_DIR / "preprocessed_markdown"
STAGE1_ASSET_DIR = BASE_DIR / "document_assets"
STAGE2_MD_DIR = BASE_DIR / "final_markdown"
STAGE3_OUTPUT_DIR = BASE_DIR / "markitdown_output"

# Create all necessary directories on startup
for dir_path in [UPLOAD_DIR, STAGE1_MD_DIR, STAGE1_ASSET_DIR, STAGE2_MD_DIR, STAGE3_OUTPUT_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Initialize API Clients (Singleton Pattern) ---
# Clients are initialized once when the application starts to avoid
# the overhead of re-authentication on every request.
logging.info("Initializing API clients...")
llm_client = initialize_llm()
md_client = initialize_markitdown_client()
if not llm_client or not md_client:
    logging.error("FATAL: Could not initialize Azure API clients. Check environment variables. Server will not be fully functional.")
    # In a production scenario, you might want to exit here if clients are essential.
    # For now, we'll allow the server to run but processing will fail.
logging.info("API clients initialized successfully.")


# --- FastAPI Application ---
app = FastAPI(
    title="Document Processing Pipeline API",
    description="An API to process scanned PDF documents through a 3-stage AI pipeline.",
    version="1.0.0"
)


def process_pipeline_task(temp_pdf_path: str, base_filename: str):
    """
    The main background task that runs the entire pipeline sequentially on a single file.
    """
    logging.info(f"PIPELINE STARTING for document: {base_filename}")
    try:
        # --- Stage 1: Local OCR and Asset Extraction ---
        stage1_result = process_single_pdf(
            pdf_path=str(temp_pdf_path),
            md_dir=str(STAGE1_MD_DIR),
            asset_dir=str(STAGE1_ASSET_DIR)
        )
        if stage1_result["status"] != "success":
            raise RuntimeError(f"Stage 1 failed: {stage1_result.get('error', 'Unknown error')}")
        logging.info(f"Stage 1 SUCCESS for {base_filename}")

        # --- Stage 2: LLM Vision Analysis and Cleanup ---
        stage1_md_path = STAGE1_MD_DIR / f"{base_filename}.md"
        stage1_doc_asset_dir = STAGE1_ASSET_DIR / base_filename
        stage2_result = process_single_document(
            llm=llm_client,
            md_path=str(stage1_md_path),
            asset_dir=str(stage1_doc_asset_dir),
            output_dir=str(STAGE2_MD_DIR)
        )
        if stage2_result["status"] != "success":
            raise RuntimeError(f"Stage 2 failed: {stage2_result.get('error', 'Unknown error')}")
        logging.info(f"Stage 2 SUCCESS for {base_filename}")

        # --- Stage 3: Final Document Synthesis ---
        stage2_md_path = STAGE2_MD_DIR / f"{base_filename}.md"
        stage3_result = process_single_markdown_file(
            md_client=md_client,
            md_path=str(stage2_md_path),
            output_dir=str(STAGE3_OUTPUT_DIR)
        )
        if stage3_result["status"] != "success":
            raise RuntimeError(f"Stage 3 failed: {stage3_result.get('error', 'Unknown error')}")
        logging.info(f"Stage 3 SUCCESS for {base_filename}")
        
        logging.info(f"PIPELINE COMPLETE for document: {base_filename}")

    except Exception as e:
        logging.error(f"PIPELINE FAILED for {base_filename}: {e}", exc_info=True)
    finally:
        # Clean up the uploaded file after processing is complete, regardless of success
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            logging.info(f"Cleaned up temporary file: {temp_pdf_path}")

@app.post("/process", status_code=202)
async def create_upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, Any]:
    """
    Endpoint to upload a PDF and trigger the processing pipeline.

    This endpoint accepts a PDF file, saves it temporarily with a unique name
    to avoid collisions, and starts the full 3-stage processing pipeline
    as a background task. It returns an immediate response to the client.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are accepted.")

    # Generate a unique ID to prevent filename collisions from multiple uploads
    unique_id = str(uuid.uuid4())
    original_base_filename = os.path.splitext(file.filename)[0]
    unique_filename = f"{original_base_filename}_{unique_id}.pdf"
    temp_pdf_path = UPLOAD_DIR / unique_filename

    # Save the uploaded file to a temporary location
    try:
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")
    finally:
        file.file.close()

    logging.info(f"Received file '{file.filename}'. Starting pipeline in background for task ID: {unique_id}")

    # Add the long-running job to the background tasks
    # The base filename for output artifacts will not have the unique ID
    background_tasks.add_task(process_pipeline_task, str(temp_pdf_path), original_base_filename)

    return {
        "message": "File accepted. Processing has started in the background.",
        "original_filename": file.filename,
        "task_id": unique_id,
        "status_info": "The pipeline will run asynchronously. Check server logs for progress."
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to the Document Processing Pipeline API. Navigate to /docs for the API documentation."}



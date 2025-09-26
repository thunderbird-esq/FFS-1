# api_server.py
#
# This script creates a fully functional FastAPI web server that acts as a
# front-end for the document processing pipeline. It exposes an endpoint
# to upload multiple documents of various types, intelligently routing them
# through the appropriate processing path as background tasks.

import os
import shutil
import logging
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, status
from typing import Dict, Any, List

# --- Direct imports of the core processing functions from our pipeline scripts ---
from stage_1_processing import process_single_pdf
from stage_2_processing import initialize_llm, process_single_document
from stage_3_processing import initialize_markitdown_client, process_single_markdown_file

# --- Centralized Pipeline Configuration ---
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
logging.info("Initializing API clients...")
llm_client = initialize_llm()
md_client = initialize_markitdown_client()
if not llm_client or not md_client:
    logging.error("FATAL: Could not initialize one or more Azure API clients. Check environment variables.")
    logging.error("The API will run, but processing endpoints will be unavailable.")

# --- FastAPI Application ---
app = FastAPI(
    title="Document Processing Pipeline API",
    description="An API to process documents through a multi-stage AI pipeline.",
    version="1.2.0"
)

# --- Background Task Definitions ---

def process_pdf_pipeline_task(temp_pdf_path: str, base_filename: str):
    """Background task for the full 3-stage PDF processing pipeline."""
    logging.info(f"PDF PIPELINE STARTING for document: {base_filename}")
    try:
        # Stage 1: Local OCR and Asset Extraction
        s1_result = process_single_pdf(str(temp_pdf_path), str(STAGE1_MD_DIR), str(STAGE1_ASSET_DIR))
        if s1_result["status"] != "success":
            raise RuntimeError(f"Stage 1 failed: {s1_result.get('error', 'Unknown error')}")
        logging.info(f"Stage 1 SUCCESS for {base_filename}")

        # Stage 2: LLM Vision Analysis and Cleanup
        s1_md_path = STAGE1_MD_DIR / f"{base_filename}.md"
        s1_asset_dir = STAGE1_ASSET_DIR / base_filename
        s2_result = process_single_document(llm_client, str(s1_md_path), str(s1_asset_dir), str(STAGE2_MD_DIR))
        if s2_result["status"] != "success":
            raise RuntimeError(f"Stage 2 failed: {s2_result.get('error', 'Unknown error')}")
        logging.info(f"Stage 2 SUCCESS for {base_filename}")

        # Stage 3: Final Document Synthesis
        s2_md_path = STAGE2_MD_DIR / f"{base_filename}.md"
        s3_result = process_single_markdown_file(md_client, str(s2_md_path), str(STAGE3_OUTPUT_DIR))
        if s3_result["status"] != "success":
            raise RuntimeError(f"Stage 3 failed: {s3_result.get('error', 'Unknown error')}")
        logging.info(f"Stage 3 SUCCESS for {base_filename}")
        
    except Exception as e:
        logging.error(f"PDF PIPELINE FAILED for {base_filename}: {e}", exc_info=True)
    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            logging.info(f"Cleaned up temporary file: {temp_pdf_path}")

def process_text_pipeline_task(temp_doc_path: str, base_filename: str):
    """Background task for the 'fast path' text-based document processing."""
    logging.info(f"TEXT PIPELINE STARTING for document: {base_filename}")
    try:
        # For text files, we bypass Stages 1 and 2.
        # MarkItDown's `convert` method can take the file path directly.
        # This is a simplified version of our Stage 3 logic.
        logging.info(f"Bypassing Stage 1 & 2 for text file: {base_filename}")
        
        # We can reuse the Stage 3 processor, but might use a different prompt
        # in a future version. For now, the standard one is fine.
        s3_result = process_single_markdown_file(md_client, str(temp_doc_path), str(STAGE3_OUTPUT_DIR))
        
        if s3_result["status"] != "success":
             raise RuntimeError(f"Stage 3 (fast path) failed: {s3_result.get('error', 'Unknown error')}")
        logging.info(f"Stage 3 (fast path) SUCCESS for {base_filename}")

    except Exception as e:
        logging.error(f"TEXT PIPELINE FAILED for {base_filename}: {e}", exc_info=True)
    finally:
        if os.path.exists(temp_doc_path):
            os.remove(temp_doc_path)
            logging.info(f"Cleaned up temporary file: {temp_doc_path}")


@app.post("/process", status_code=status.HTTP_202_ACCEPTED)
async def create_upload_files(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Dict[str, Any]:
    """
    Endpoint to upload one or more documents and trigger the appropriate
    processing pipeline for each.
    """
    if not llm_client or not md_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API clients are not initialized. Check server logs and environment variables."
        )

    processed_files = []
    for file in files:
        if not file.filename:
            logging.warning("Skipping a file with no filename.")
            continue
        
        file_extension = Path(file.filename).suffix.lower()
        original_base_filename = os.path.splitext(file.filename)[0]
        
        # Use a unique ID to prevent filename collisions
        unique_id = str(uuid.uuid4())
        unique_filename = f"{original_base_filename}_{unique_id}{file_extension}"
        temp_doc_path = UPLOAD_DIR / unique_filename

        try:
            # Save the file temporarily
            with open(temp_doc_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # --- Content-Aware Routing ---
            if file_extension == ".pdf":
                logging.info(f"Routing '{file.filename}' to PDF pipeline.")
                background_tasks.add_task(process_pdf_pipeline_task, str(temp_doc_path), original_base_filename)
                processed_files.append({"filename": file.filename, "task_id": unique_id, "status": "accepted_for_pdf_pipeline"})
            
            elif file_extension in [".txt", ".md", ".docx"]:
                 logging.info(f"Routing '{file.filename}' to Text pipeline (fast path).")
                 # NOTE: Markitdown needs the file path, so we still save it.
                 background_tasks.add_task(process_text_pipeline_task, str(temp_doc_path), original_base_filename)
                 processed_files.append({"filename": file.filename, "task_id": unique_id, "status": "accepted_for_text_pipeline"})
            
            else:
                os.remove(temp_doc_path) # Clean up unsupported file
                processed_files.append({"filename": file.filename, "task_id": None, "status": "rejected", "detail": f"Unsupported file type: '{file_extension}'"})

        except Exception as e:
            processed_files.append({"filename": file.filename, "task_id": None, "status": "error", "detail": f"Failed to save uploaded file: {e}"})
        finally:
            file.file.close()

    if not processed_files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid files were provided for processing.")

    return {
        "message": "Request processed. Check status for each file.",
        "results": processed_files
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to the Document Processing Pipeline API. Navigate to /docs for the API documentation."}



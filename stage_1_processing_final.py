# stage_1_processing.py
#
# This script performs the first stage of the document processing pipeline.
# It converts PDF files into Markdown text and extracts all embedded images.
# It is designed to be robust, with a fallback OCR mechanism for difficult documents,
# and generates a comprehensive log of its operations.

import os
import fitz  # PyMuPDF
from pymupdf4llm import to_markdown
from PIL import Image
import io
import logging
import argparse
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

# Conditional import for fallback OCR; gracefully handle if not installed.
try:
    import pytesseract
    from pdf2image import convert_from_path
    FALLBACK_OCR_AVAILABLE = True
except ImportError:
    FALLBACK_OCR_AVAILABLE = False

# --- Configuration Constants ---
PROCESSING_LOG_FILE = "_stage1_processing.json"

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Core Functions ---

def calculate_file_hash(filepath: str) -> str:
    """Calculates the SHA256 hash of a file for traceability."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fallback_ocr(pdf_path: str) -> str:
    """
    Performs a brute-force OCR by converting each page to an image
    and running Tesseract. This is a fallback for when pymupdf4llm fails.
    """
    if not FALLBACK_OCR_AVAILABLE:
        logging.warning("Fallback OCR is not available. pytesseract or pdf2image is not installed.")
        return ""

    logging.warning(f"Primary OCR returned empty. Engaging fallback for {os.path.basename(pdf_path)}.")
    try:
        images = convert_from_path(pdf_path)
        full_text = []
        for i, image in enumerate(images):
            logging.debug(f"Fallback OCR on page {i+1}...")
            page_text = pytesseract.image_to_string(image)
            full_text.append(page_text)
        return "\n\n--- Page Break ---\n\n".join(full_text)
    except Exception as e:
        logging.error(f"Error during fallback OCR for {pdf_path}: {e}")
        return ""

def extract_images_from_pdf(doc: fitz.Document, asset_dir: str) -> int:
    """Extracts all images from a PyMuPDF document object and saves them."""
    os.makedirs(asset_dir, exist_ok=True)
    image_count = 0
    for page_num, page in enumerate(doc):
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                image = Image.open(io.BytesIO(image_bytes))
                # Use Pillow's detected format if available, otherwise use original
                ext = image.format.lower() if image.format else image_ext
                image_filename = f"page{page_num + 1:03d}_img{img_index + 1:02d}.{ext}"
                image_path = os.path.join(asset_dir, image_filename)
                
                # Convert to RGB to avoid issues with paletted images (like GIFs)
                if image.mode in ("P", "PA"):
                    image = image.convert("RGB")
                
                image.save(image_path)
                image_count += 1
            except Exception as e:
                logging.warning(f"Could not process image idx {img_index} on page {page_num + 1}: {e}")
    return image_count

def process_single_pdf(pdf_path: str, md_dir: str, asset_dir: str) -> Dict[str, Any]:
    """Orchestrates the full Stage 1 processing for a single PDF."""
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    md_output_path = os.path.join(md_dir, f"{base_filename}.md")
    doc_asset_dir = os.path.join(asset_dir, base_filename)
    
    stats = {
        "document": base_filename,
        "status": "skipped",
        "source_hash": "N/A",
        "ocr_method": "N/A",
        "char_count": 0,
        "image_count": 0,
        "error": None
    }

    if os.path.exists(md_output_path) and os.path.exists(doc_asset_dir):
        logging.info(f"Skipping '{base_filename}', output already exists.")
        return stats

    logging.info(f"--- Processing document: {base_filename} ---")
    stats["status"] = "processing"
    
    try:
        stats["source_hash"] = calculate_file_hash(pdf_path)

        # 1. Primary OCR attempt with pymupdf4llm
        md_text = to_markdown(pdf_path)
        stats["ocr_method"] = "pymupdf4llm"

        # 2. Check for failure and engage fallback if necessary
        if not md_text or md_text.strip() == "":
            md_text = fallback_ocr(pdf_path)
            stats["ocr_method"] = "fallback_tesseract"

        stats["char_count"] = len(md_text)

        # 3. Write Markdown output
        with open(md_output_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        logging.info(f"Saved Markdown ({stats['char_count']} chars) to '{md_output_path}'")

        # 4. Image Extraction
        doc = fitz.open(pdf_path) # Open document for image extraction
        image_count = extract_images_from_pdf(doc, doc_asset_dir)
        stats["image_count"] = image_count
        doc.close()
        logging.info(f"Extracted {image_count} images to '{doc_asset_dir}'")
        
        stats["status"] = "success"

    except Exception as e:
        logging.error(f"FATAL ERROR processing {base_filename}: {e}", exc_info=True)
        stats["status"] = "failed"
        stats["error"] = str(e)
    
    return stats


def main(args):
    """Main function to find PDFs and loop through them, generating a summary log."""
    os.makedirs(args.md_dir, exist_ok=True)
    os.makedirs(args.asset_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(args.pdf_dir) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        logging.warning(f"No PDF files found in '{args.pdf_dir}'.")
        return

    logging.info(f"Found {len(pdf_files)} PDF(s) to process for Stage 1.")
    
    overall_stats = {
        "start_time": datetime.now().isoformat(),
        "total_files": len(pdf_files),
        "successful": 0, "failed": 0, "skipped": 0,
        "total_chars_extracted": 0, "total_images_extracted": 0,
        "processing_details": []
    }

    for pdf_filename in pdf_files:
        pdf_path = os.path.join(args.pdf_dir, pdf_filename)
        result = process_single_pdf(pdf_path, args.md_dir, args.asset_dir)
        
        overall_stats["processing_details"].append(result)
        if result["status"] == "success":
            overall_stats["successful"] += 1
            overall_stats["total_chars_extracted"] += result["char_count"]
            overall_stats["total_images_extracted"] += result["image_count"]
        elif result["status"] == "failed":
            overall_stats["failed"] += 1
        else: # skipped
            overall_stats["skipped"] += 1

    overall_stats["end_time"] = datetime.now().isoformat()
    log_path = os.path.join(args.md_dir, PROCESSING_LOG_FILE)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(overall_stats, f, indent=2)

    logging.info("--- Stage 1 Complete: Summary ---")
    logging.info(f"  Files processed: {overall_stats['successful']}/{overall_stats['total_files']}")
    logging.info(f"  Files skipped:   {overall_stats['skipped']}")
    logging.info(f"  Files failed:    {overall_stats['failed']}")
    logging.info(f"  Total characters extracted: {overall_stats['total_chars_extracted']:,}")
    logging.info(f"  Total images extracted:     {overall_stats['total_images_extracted']:,}")
    logging.info(f"  Detailed log saved to: {log_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 1: PDF to Markdown OCR and Image Extraction.")
    parser.add_argument("--pdf-dir", required=True, help="Directory containing source PDF files.")
    parser.add_argument("--md-dir", required=True, help="Directory to save the processed Markdown files.")
    parser.add_argument("--asset-dir", required=True, help="Root directory to save the extracted image assets.")
    
    args = parser.parse_args()
    main(args)

# stage_1_processing.py
#
# This script performs the first stage of the document processing pipeline.
# It converts PDF files into Markdown text and extracts all embedded images.
# It is designed to be robust, with a fallback OCR mechanism for difficult documents.

import os
import fitz  # PyMuPDF
from pymupdf4llm import to_markdown
from PIL import Image
import io
import logging
import argparse

# Conditional import for fallback OCR; gracefully handle if not installed.
try:
    import pytesseract
    from pdf2image import convert_from_path
    FALLBACK_OCR_AVAILABLE = True
except ImportError:
    FALLBACK_OCR_AVAILABLE = False

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def fallback_ocr(pdf_path: str) -> str:
    """
    Performs a brute-force OCR on a PDF by converting each page to an image
    and running Tesseract. This is a fallback for when pymupdf4llm fails.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        The extracted text content as a single string.
    """
    if not FALLBACK_OCR_AVAILABLE:
        logging.warning("Fallback OCR is not available. pytesseract or pdf2image is not installed.")
        return ""

    logging.warning(f"Primary OCR failed for {os.path.basename(pdf_path)}. Engaging fallback OCR.")
    try:
        images = convert_from_path(pdf_path)
        full_text = []
        for i, image in enumerate(images):
            logging.info(f"  -> Fallback OCR on page {i + 1}/{len(images)}")
            text = pytesseract.image_to_string(image)
            full_text.append(f"\n\n--- Page {i + 1} (Fallback OCR) ---\n\n{text}")
        return "".join(full_text)
    except Exception as e:
        logging.error(f"Fallback OCR process failed for {os.path.basename(pdf_path)}: {e}")
        return ""

def extract_images_from_pdf(pdf_path: str, asset_dir: str) -> int:
    """
    Extracts all images from a PDF and saves them to a specified directory.

    Args:
        pdf_path: The path to the PDF file.
        asset_dir: The directory to save the extracted images.

    Returns:
        The total count of images extracted.
    """
    image_count = 0
    try:
        doc = fitz.open(pdf_path)
        os.makedirs(asset_dir, exist_ok=True)
        for page_num, page in enumerate(doc):
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Use Pillow to identify format and save, ensuring compatibility
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                    ext = image.format.lower() if image.format else 'png'
                    image_filename = f"page{page_num + 1:03d}_img{img_index + 1:02d}.{ext}"
                    image_path = os.path.join(asset_dir, image_filename)
                    image.save(image_path)
                    image_count += 1
                except Exception as img_e:
                    logging.warning(f"Could not process an image on page {page_num + 1}: {img_e}")
        doc.close()
    except Exception as e:
        logging.error(f"Failed to extract images from {os.path.basename(pdf_path)}: {e}")
    return image_count

def process_single_pdf(pdf_path: str, md_dir: str, asset_dir: str):
    """
    Orchestrates the full Stage 1 processing for a single PDF file.

    Args:
        pdf_path: The path to the source PDF file.
        md_dir: The directory to save the output Markdown file.
        asset_dir: The root directory for storing image assets.
    """
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    md_output_path = os.path.join(md_dir, f"{base_filename}.md")
    doc_asset_dir = os.path.join(asset_dir, base_filename)

    # Idempotency check: skip if already processed
    if os.path.exists(md_output_path) and os.path.exists(doc_asset_dir):
        logging.info(f"Skipping '{base_filename}', already processed.")
        return

    logging.info(f"--- Processing document: {base_filename} ---")
    
    try:
        # 1. Primary OCR attempt
        md_text = to_markdown(pdf_path)

        # 2. Validate and Fallback
        if not md_text or md_text.strip() == "":
            md_text = fallback_ocr(pdf_path)

        with open(md_output_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        logging.info(f"Successfully saved Markdown to '{md_output_path}'")

        # 3. Image Extraction
        count = extract_images_from_pdf(pdf_path, doc_asset_dir)
        logging.info(f"Extracted {count} images to '{doc_asset_dir}'")

    except Exception as e:
        logging.error(f"FATAL ERROR processing {base_filename}: {e}")

def main(args):
    """
    Main function to find PDFs and loop through them.
    """
    os.makedirs(args.md_dir, exist_ok=True)
    os.makedirs(args.asset_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(args.pdf_dir) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        logging.warning(f"No PDF files found in '{args.pdf_dir}'.")
        return

    logging.info(f"Found {len(pdf_files)} PDF(s) to process.")
    for pdf_filename in pdf_files:
        pdf_path = os.path.join(args.pdf_dir, pdf_filename)
        process_single_pdf(pdf_path, args.md_dir, args.asset_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 1: PDF to Markdown OCR and Image Extraction.")
    parser.add_argument("--pdf-dir", required=True, help="Directory containing source PDF files.")
    parser.add_argument("--md-dir", required=True, help="Directory to save the processed Markdown files.")
    parser.add_argument("--asset-dir", required=True, help="Root directory to save extracted image assets.")
    
    args = parser.parse_args()
    main(args)


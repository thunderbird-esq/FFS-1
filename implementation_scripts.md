# Complete Implementation Scripts

## Stage 1: Enhanced OCR and Image Extraction
```python
# stage_1_processing_enhanced.py

import os
import fitz
from pymupdf4llm import to_markdown
from PIL import Image
import io
import sys
import json
import traceback
import hashlib
from datetime import datetime

# Conditional import for fallback OCR
try:
    import pytesseract
    from pdf2image import convert_from_path
    FALLBACK_OCR_AVAILABLE = True
except ImportError:
    FALLBACK_OCR_AVAILABLE = False
    print("WARNING: Fallback OCR unavailable - install pytesseract and pdf2image")

# Configuration
PDF_SOURCE_DIR = "."
MARKDOWN_OUTPUT_DIR = "preprocessed_markdown"
IMAGE_ASSET_DIR = "document_assets"
EXTRACTION_LOG_FILE = "_extraction_log.json"

def calculate_file_hash(filepath):
    """Calculate SHA256 hash of file for deduplication."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fallback_ocr_extraction(pdf_path):
    """
    Implements multi-strategy OCR fallback using pytesseract.
    Tries multiple PSM modes and selects best result.
    """
    if not FALLBACK_OCR_AVAILABLE:
        return {"text": "", "method": "unavailable", "page_count": 0}
    
    extraction_log = {
        "method": "pytesseract_fallback",
        "configs_tried": [],
        "page_results": []
    }
    
    try:
        # Convert PDF to images at optimal DPI for OCR
        images = convert_from_path(pdf_path, dpi=200)
        full_text = []
        
        for page_num, image in enumerate(images):
            # Multiple OCR configurations for different document types
            configs = [
                {"name": "uniform_block", "psm": r'--oem 3 --psm 6'},
                {"name": "single_column", "psm": r'--oem 3 --psm 4'},
                {"name": "automatic", "psm": r'--oem 3 --psm 3'},
                {"name": "sparse_text", "psm": r'--oem 3 --psm 11'}
            ]
            
            best_text = ""
            best_config = None
            best_confidence = 0
            
            for config in configs:
                try:
                    # Extract text with confidence scores
                    data = pytesseract.image_to_data(
                        image, 
                        config=config["psm"],
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Calculate average confidence
                    confidences = [int(c) for c in data['conf'] if int(c) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # Extract text
                    text = pytesseract.image_to_string(image, config=config["psm"])
                    
                    # Select best result based on text length and confidence
                    score = len(text.strip()) * (avg_confidence / 100)
                    if score > len(best_text.strip()) * (best_confidence / 100):
                        best_text = text
                        best_config = config["name"]
                        best_confidence = avg_confidence
                        
                except Exception as e:
                    extraction_log["configs_tried"].append({
                        "config": config["name"],
                        "error": str(e)
                    })
                    continue
            
            if best_text.strip():
                full_text.append(f"# Page {page_num + 1}\n\n{best_text.strip()}")
                extraction_log["page_results"].append({
                    "page": page_num + 1,
                    "config_used": best_config,
                    "confidence": best_confidence,
                    "text_length": len(best_text)
                })
        
        result_text = "\n\n---\n\n".join(full_text)
        extraction_log["total_pages"] = len(images)
        extraction_log["success"] = True
        
        return {
            "text": result_text,
            "method": "pytesseract_fallback",
            "page_count": len(images),
            "log": extraction_log
        }
        
    except Exception as e:
        extraction_log["error"] = str(e)
        extraction_log["success"] = False
        return {
            "text": f"Fallback OCR failed: {str(e)}",
            "method": "pytesseract_fallback_failed",
            "page_count": 0,
            "log": extraction_log
        }

def extract_images_with_metadata(pdf_path, output_dir):
    """
    Extract all images from PDF with comprehensive metadata.
    Returns detailed extraction log for debugging and quality control.
    """
    extraction_results = {
        "timestamp": datetime.now().isoformat(),
        "source_pdf": os.path.basename(pdf_path),
        "images_extracted": [],
        "extraction_errors": [],
        "total_pages": 0,
        "total_images": 0
    }
    
    try:
        doc = fitz.open(pdf_path)
        extraction_results["total_pages"] = len(doc)
        image_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image for processing
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Generate consistent filename
                    image_filename = f"page_{page_num + 1:03d}_img_{img_index:02d}.png"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    # Save as PNG with metadata
                    image.save(image_path, "PNG", optimize=True)
                    
                    # Calculate image hash for deduplication
                    image_hash = hashlib.md5(image_bytes).hexdigest()
                    
                    # Store metadata
                    extraction_results["images_extracted"].append({
                        "filename": image_filename,
                        "page": page_num + 1,
                        "index": img_index,
                        "width": image.width,
                        "height": image.height,
                        "format": base_image.get("ext", "unknown"),
                        "size_bytes": len(image_bytes),
                        "hash": image_hash
                    })
                    
                    image_count += 1
                    
                except Exception as img_e:
                    error_msg = f"Page {page_num + 1}, Image {img_index}: {str(img_e)}"
                    extraction_results["extraction_errors"].append(error_msg)
                    print(f"WARNING: {error_msg}")
                    continue
        
        doc.close()
        extraction_results["total_images"] = image_count
        return extraction_results
        
    except Exception as e:
        extraction_results["fatal_error"] = str(e)
        print(f"ERROR: Image extraction failed: {e}")
        return extraction_results

def process_pdf_document(pdf_path):
    """
    Main processing function for individual PDF document.
    Implements intelligent OCR strategy selection and fallback.
    """
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    md_path = os.path.join(MARKDOWN_OUTPUT_DIR, f"{base_filename}.md")
    doc_asset_folder = os.path.join(IMAGE_ASSET_DIR, base_filename)
    
    # Initialize processing log
    processing_log = {
        "timestamp": datetime.now().isoformat(),
        "pdf_file": os.path.basename(pdf_path),
        "file_hash": calculate_file_hash(pdf_path),
        "file_size_bytes": os.path.getsize(pdf_path),
        "processing_steps": []
    }
    
    # Skip if already processed
    if os.path.exists(md_path) and os.path.exists(doc_asset_folder):
        log_file = os.path.join(doc_asset_folder, EXTRACTION_LOG_FILE)
        if os.path.exists(log_file):
            print(f"Skipping {os.path.basename(pdf_path)} (already processed)")
            return {"status": "skipped", "reason": "already_processed"}
    
    print(f"Processing {os.path.basename(pdf_path)}...")
    
    try:
        # Step 1: Primary OCR with pymupdf4llm
        print("  -> Attempting primary OCR with pymupdf4llm...")
        primary_start = datetime.now()
        
        try:
            md_text = to_markdown(pdf_path)
            primary_time = (datetime.now() - primary_start).total_seconds()
            
            processing_log["processing_steps"].append({
                "step": "primary_ocr",
                "method": "pymupdf4llm",
                "success": True,
                "duration_seconds": primary_time,
                "text_length": len(md_text)
            })
            
            # Quality assessment
            if len(md_text.strip()) < 50:
                print("  -> Primary OCR returned minimal content, attempting fallback...")
                
                fallback_result = fallback_ocr_extraction(pdf_path)
                
                processing_log["processing_steps"].append({
                    "step": "fallback_ocr",
                    "method": fallback_result["method"],
                    "success": fallback_result["text"] != "",
                    "page_count": fallback_result["page_count"],
                    "text_length": len(fallback_result["text"])
                })
                
                # Use whichever produced more content
                if len(fallback_result["text"].strip()) > len(md_text.strip()):
                    md_text = fallback_result["text"]
                    print("  -> Using fallback OCR results")
                else:
                    print("  -> Keeping primary OCR results")
            else:
                print(f"  -> Primary OCR successful ({len(md_text)} characters)")
                
        except Exception as ocr_e:
            print(f"  -> Primary OCR failed: {ocr_e}")
            processing_log["processing_steps"].append({
                "step": "primary_ocr",
                "method": "pymupdf4llm",
                "success": False,
                "error": str(ocr_e)
            })
            
            print("  -> Attempting fallback OCR...")
            fallback_result = fallback_ocr_extraction(pdf_path)
            md_text = fallback_result["text"]
            
            processing_log["processing_steps"].append({
                "step": "fallback_ocr",
                "method": fallback_result["method"],
                "success": fallback_result["text"] != "",
                "text_length": len(fallback_result["text"])
            })
        
        # Step 2: Save extracted text
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)
        
        processing_log["markdown_output"] = {
            "path": md_path,
            "size_bytes": os.path.getsize(md_path),
            "character_count": len(md_text),
            "line_count": len(md_text.splitlines())
        }
        
        # Step 3: Extract images
        print("  -> Extracting images...")
        os.makedirs(doc_asset_folder, exist_ok=True)
        
        image_extraction_results = extract_images_with_metadata(pdf_path, doc_asset_folder)
        
        processing_log["image_extraction"] = image_extraction_results
        
        print(f"  -> Extracted {image_extraction_results['total_images']} images")
        
        # Step 4: Save processing log
        log_path = os.path.join(doc_asset_folder, EXTRACTION_LOG_FILE)
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(processing_log, f, indent=2)
        
        return {
            "status": "success",
            "text_extracted": len(md_text),
            "images_extracted": image_extraction_results["total_images"]
        }
        
    except Exception as e:
        print(f"ERROR processing {os.path.basename(pdf_path)}: {e}")
        traceback.print_exc()
        
        processing_log["fatal_error"] = str(e)
        processing_log["traceback"] = traceback.format_exc()
        
        # Save error log even on failure
        try:
            os.makedirs(doc_asset_folder, exist_ok=True)
            log_path = os.path.join(doc_asset_folder, EXTRACTION_LOG_FILE)
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(processing_log, f, indent=2)
        except:
            pass
        
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    # Create output directories
    os.makedirs(MARKDOWN_OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMAGE_ASSET_DIR, exist_ok=True)
    
    # Find all PDF files
    pdf_files = [f for f in os.listdir(PDF_SOURCE_DIR) if f.lower().endswith((".pdf", ".PDF"))]
    
    if not pdf_files:
        print("ERROR: No PDF files found in current directory")
        sys.exit(1)
    
    print(f"Stage 1: Processing {len(pdf_files)} PDF file(s)")
    print("-" * 50)
    
    # Process statistics
    stats = {
        "total_files": len(pdf_files),
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "total_text_extracted": 0,
        "total_images_extracted": 0
    }
    
    # Process each PDF
    for pdf_filename in pdf_files:
        pdf_path = os.path.join(PDF_SOURCE_DIR, pdf_filename)
        result = process_pdf_document(pdf_path)
        
        if result["status"] == "success":
            stats["successful"] += 1
            stats["total_text_extracted"] += result.get("text_extracted", 0)
            stats["total_images_extracted"] += result.get("images_extracted", 0)
        elif result["status"] == "failed":
            stats["failed"] += 1
        else:
            stats["skipped"] += 1
    
    # Print summary
    print("-" * 50)
    print("Stage 1 Complete - Summary:")
    print(f"  Files processed: {stats['successful']}/{stats['total_files']}")
    print(f"  Files skipped: {stats['skipped']}")
    print(f"  Files failed: {stats['failed']}")
    print(f"  Total text extracted: {stats['total_text_extracted']:,} characters")
    print(f"  Total images extracted: {stats['total_images_extracted']}")
    
    # Exit with appropriate code
    if stats["failed"] > 0 and stats["successful"] == 0:
        sys.exit(1)
    else:
        sys.exit(0)
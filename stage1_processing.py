import os
import fitz  # PyMuPDF
from pymupdf4llm import to_markdown
from PIL import Image
import io

# --- New Imports for Fallback OCR ---
import pytesseract
from pdf2image import convert_from_path

# --- Configuration ---
PDF_SOURCE_DIR = "."
MARKDOWN_OUTPUT_DIR = "preprocessed_markdown"
ASSET_OUTPUT_DIR = "document_assets"

# --- New Fallback OCR Function ---
def fallback_ocr_with_pytesseract(pdf_path):
    """
    A fallback OCR method for difficult PDFs. Converts each page to an image
    and runs Tesseract on it directly.
    """
    print("   -> Primary OCR failed. Trying fallback method...")
    try:
        images = convert_from_path(pdf_path)
        full_text = []
        for i, image in enumerate(images):
            print(f"      -> Processing page {i + 1} with fallback OCR...")
            text = pytesseract.image_to_string(image)
            full_text.append(text)
        return "\\n\\n--- Page Break ---\\n\\n".join(full_text)
    except Exception as e:
        print(f"      -> Fallback OCR also failed. Error: {e}")
        return "" # Return empty string if fallback also fails

# --- Main Script ---
if __name__ == "__main__":
    os.makedirs(MARKDOWN_OUTPUT_DIR, exist_ok=True)
    os.makedirs(ASSET_OUTPUT_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(PDF_SOURCE_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
    else:
        print(f"Found {len(pdf_files)} PDF(s) to process...")

    for pdf_filename in pdf_files:
        try:
            base_filename = os.path.splitext(pdf_filename)[0]
            pdf_path = os.path.join(PDF_SOURCE_DIR, pdf_filename)
            
            md_path = os.path.join(MARKDOWN_OUTPUT_DIR, f"{base_filename}.md")
            doc_asset_dir = os.path.join(ASSET_OUTPUT_DIR, base_filename)

            if os.path.exists(md_path) and os.path.exists(doc_asset_dir):
                print(f"Skipping '{pdf_filename}' (already processed).")
                continue

            print(f"Processing '{pdf_filename}'...")

            # --- 1. OCR to Markdown (with new fallback logic) ---
            md_text = to_markdown(pdf_path)
            
            # Check if the primary method failed
            if not md_text or not md_text.strip():
                md_text = fallback_ocr_with_pytesseract(pdf_path)

            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_text)
            print(f" -> Successfully saved Markdown to '{md_path}'")

            # --- 2. Image Extraction ---
            os.makedirs(doc_asset_dir, exist_ok=True)
            doc = fitz.open(pdf_path)
            image_count = 0
            for page_num, page in enumerate(doc):
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    try:
                        image = Image.open(io.BytesIO(image_bytes))
                        image_filename = f"page{page_num + 1}_img{img_index + 1}.{image.format.lower()}"
                        image_path = os.path.join(doc_asset_dir, image_filename)
                        image.save(image_path)
                        image_count += 1
                    except Exception as img_e:
                        print(f"   -> Warning: Could not process an image on page {page_num + 1}. Error: {img_e}")

            if image_count > 0:
                print(f" -> Extracted {image_count} images to '{doc_asset_dir}'")
            doc.close()

        except Exception as e:
            print(f" -> FAILED to process '{pdf_filename}'. Error: {e}")

    print("\nStage 1 processing complete.")



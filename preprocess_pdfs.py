import os
import fitz  # PyMuPDF
from pymupdf4llm import to_markdown

# --- Configuration ---
# The folder where your original PDFs are located.
# The '.' means the current directory.
PDF_SOURCE_DIR = "." 

# The folder where the processed Markdown files will be saved.
# We'll create it if it doesn't exist.
MARKDOWN_OUTPUT_DIR = "preprocessed_markdown" 

# --- Main Script ---
if __name__ == "__main__":
    # Create the output directory if it's not already there
    if not os.path.exists(MARKDOWN_OUTPUT_DIR):
        os.makedirs(MARKDOWN_OUTPUT_DIR)

    # Find all PDF files in the source directory
    pdf_files = [f for f in os.listdir(PDF_SOURCE_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("No PDF files found in the current directory.")
    else:
        print(f"Found {len(pdf_files)} PDF(s) to preprocess...")

    # Process each PDF file
    for pdf_filename in pdf_files:
        try:
            pdf_path = os.path.join(PDF_SOURCE_DIR, pdf_filename)
            print(f"Processing '{pdf_filename}'...")

            # This is the core command. It opens the PDF and converts it to Markdown.
            # PyMuPDF will automatically detect image-only pages and use Tesseract for OCR.
            md_text = to_markdown(pdf_path)

            # Create a new filename for the Markdown output
            base_filename = os.path.splitext(pdf_filename)[0]
            md_filename = f"{base_filename}.md"
            md_path = os.path.join(MARKDOWN_OUTPUT_DIR, md_filename)

            # Save the processed Markdown to the output file
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_text)

            print(f" -> Successfully saved to '{md_path}'")

        except Exception as e:
            print(f" -> FAILED to process '{pdf_filename}'. Error: {e}")

    print("\nPreprocessing complete.")

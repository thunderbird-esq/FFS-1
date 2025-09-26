import os
import easyocr
import pytesseract
from pdf2image import convert_from_path
import pdfplumber
from unstructured.partition.pdf import partition_pdf

# Initialize OCR
reader = easyocr.Reader(['en'])

# Folder containing PDFs
pdf_folder = "."
output_folder = "./preprocessed_pdfs_2"
os.makedirs(output_folder, exist_ok=True)

def extract_text_with_pdfplumber(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages])
        return text
    except Exception as e:
        print(f"Error with pdfplumber on {pdf_path}: {e}")
        return ""

def extract_text_with_ocr(pdf_path):
    try:
        images = convert_from_path(pdf_path)
        text = []
        for image in images:
            result = reader.readtext(image)
            page_text = "\n".join([detection[1] for detection in result])
            text.append(page_text)
        return "\n".join(text)
    except Exception as e:
        print(f"Error with OCR on {pdf_path}: {e}")
        return ""

def extract_text_with_unstructured(pdf_path):
    try:
        elements = partition_pdf(pdf_path)
        return "\n".join([str(element) for element in elements])
    except Exception as e:
        print(f"Error with unstructured on {pdf_path}: {e}")
        return ""

def synthesize_text(pdf_text, ocr_text, unstructured_text):
    # Prefer unstructured if it's non-empty, otherwise fall back to OCR or PDF text
    if unstructured_text and len(unstructured_text.strip()) > 50:
        return unstructured_text
    elif ocr_text and len(ocr_text.strip()) > 50:
        return ocr_text
    else:
        return pdf_text

def process_pdf(pdf_path, output_folder):
    # Extract text with all methods
    pdf_text = extract_text_with_pdfplumber(pdf_path)
    ocr_text = extract_text_with_ocr(pdf_path)
    unstructured_text = extract_text_with_unstructured(pdf_path)

    # Synthesize the best text
    final_text = synthesize_text(pdf_text, ocr_text, unstructured_text)

    # Save to Markdown file
    output_file = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(pdf_path))[0]}.md")
    with open(output_file, "w") as f:
        f.write(final_text)
    print(f"Processed {pdf_path} -> {output_file}")

# Process all PDFs
for filename in os.listdir(pdf_folder):
    if filename.lower().endswith('.pdf'):
        process_pdf(os.path.join(pdf_folder, filename), output_folder)

print("Pipeline completed!")


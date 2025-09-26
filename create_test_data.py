# create_test_data.py
#
# This utility script programmatically generates a suite of PDF files for testing
# the document processing pipeline. It creates documents designed to test specific
# scenarios as outlined in TESTING.md.

import os
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
import io

# --- Configuration ---
TEST_DATA_DIR = "test_data"
LOREM_IPSUM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Donec euismod, nisl eget consectetur tempor, nisl nunc "
    "aliquam nunc, eget consectetur nisl nunc eget nisl. "
    "Nullam euismod, nisl eget consectetur tempor, nisl nunc "
    "aliquam nunc, eget consectetur nisl nunc eget nisl."
)

# --- Helper Functions ---

def create_text_only_pdf(path: str):
    """Creates a simple, multi-page, text-only PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Test Document: Text Only", ln=True, align='C')
    pdf.ln(10)
    for _ in range(20):
        pdf.multi_cell(0, 5, LOREM_IPSUM)
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', size=16)
    pdf.cell(0, 10, "Chapter 2: More Text", ln=True)
    pdf.set_font("Helvetica", size=12)
    for _ in range(10):
        pdf.multi_cell(0, 5, LOREM_IPSUM)
    pdf.output(path)

def create_image_heavy_pdf(path: str):
    """Creates a PDF with full-page images."""
    pdf = FPDF()
    for i in range(2):
        img = Image.new('RGB', (600, 800), color=f'rgb(100, 150, 20{i*20})')
        draw = ImageDraw.Draw(img)
        draw.text((100, 400), f"This is image {i+1}", fill='white')
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        pdf.add_page()
        # Use FPDF's image handling from a stream
        pdf.image(img_byte_arr, x=10, y=8, w=190)
    pdf.output(path)

def create_mixed_content_pdf(path: str):
    """Creates a PDF with a mix of text, an image, and a table-like structure."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Test Document: Mixed Content", ln=True, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 5, LOREM_IPSUM)
    
    # Add an image
    img = Image.new('RGB', (400, 200), color='gray')
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, 390, 190], outline="black", width=2)
    draw.text((150, 90), "A Sample Diagram", fill='black')
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    pdf.image(img_byte_arr, x=50, y=pdf.get_y(), w=100)
    pdf.ln(70) # Move below image

    # Add a simple table-like structure
    pdf.set_font("Courier", size=10)
    pdf.cell(0, 10, "PIN | VALUE | DESCRIPTION", ln=True)
    pdf.cell(0, 5, "--------------------------------", ln=True)
    pdf.cell(0, 5, " 1  | 0xFF00| DATA_BUS_0", ln=True)
    pdf.cell(0, 5, " 2  | 0xFF01| DATA_BUS_1", ln=True)
    
    pdf.output(path)

def create_difficult_scan_pdf(path: str):
    """Creates a PDF that simulates a low-quality scan to trigger fallback OCR."""
    # 1. Create text as a high-res image
    text = "This is a difficult scan.\nText is rendered as a low-quality JPEG.\nThis should trigger the fallback OCR in Stage 1.\n0ne l vs 1, O vs 0."
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)
    try:
        # Use a common system font, fallback to default if not found
        font = ImageFont.truetype("Arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()
    draw.text((50, 50), text, fill='black', font=font)

    # 2. Degrade the image by saving as a low-quality JPEG in memory
    jpeg_buffer = io.BytesIO()
    img.save(jpeg_buffer, format='JPEG', quality=30) # Low quality
    jpeg_buffer.seek(0)

    # 3. Create a PDF and insert the degraded image
    pdf = FPDF()
    pdf.add_page()
    pdf.image(jpeg_buffer, x=10, y=10, w=190)
    pdf.output(path)

def create_corrupted_pdf(path: str):
    """Creates a file with a .pdf extension that is not a valid PDF."""
    with open(path, "w") as f:
        f.write("%PDF-1.4\nThis is not a real PDF file. It is intentionally corrupted.\n%%EOF")

# --- Main Execution ---
if __name__ == "__main__":
    print(f"Generating test data in '{TEST_DATA_DIR}/'...")
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    creators = {
        "text_only.pdf": create_text_only_pdf,
        "image_heavy.pdf": create_image_heavy_pdf,
        "mixed_content.pdf": create_mixed_content_pdf,
        "difficult_scan.pdf": create_difficult_scan_pdf,
        "corrupted.pdf": create_corrupted_pdf,
    }
    
    for filename, function in creators.items():
        filepath = os.path.join(TEST_DATA_DIR, filename)
        print(f"  -> Creating '{filename}'...")
        function(filepath)
        
    print("Test data generation complete.")


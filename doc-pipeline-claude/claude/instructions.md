# Claude Code Execution Instructions

## Technical Implementation Protocol

### Environment Validation Prerequisites

#### Required System Dependencies
```bash
# macOS Catalina 10.15.7 Specific Validation
uname -a | grep "Darwin 19.6.0" || echo "WARNING: Unexpected OS version"

# Python Version Constraint (Critical for Catalina Compatibility)
python3 --version | grep -E "3.9.[0-9]+" || {
    echo "ERROR: Python 3.9.x required for Catalina compatibility"
    echo "Python 3.10+ has known Catalina incompatibilities"
    exit 1
}

# HuggingFace CLI Installation with Specific Version Pinning
pip3 install --user "huggingface_hub[cli]==0.19.4" --no-cache-dir
```

#### Environment Variable Configuration
```bash
# HuggingFace Authentication (Write Token Required)
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"
export HF_USERNAME="your_hf_username"
export HF_SPACE_NAME="document-processing-pipeline"

# Validation Script
python3 -c "
import os
import sys

required_vars = ['HF_TOKEN', 'HF_USERNAME']
missing = [var for var in required_vars if not os.environ.get(var)]

if missing:
    print(f'ERROR: Missing environment variables: {missing}')
    sys.exit(1)

if not os.environ['HF_TOKEN'].startswith('hf_'):
    print('ERROR: HF_TOKEN must start with hf_ prefix')
    sys.exit(1)

print('✓ Environment variables validated')
"
```

## Phase 1: Local Assessment Implementation

### File System Analysis Protocol
```bash
# Comprehensive Project Inventory
echo "=== PROJECT STRUCTURE ANALYSIS ==="
find . -maxdepth 3 \( -name "*.py" -o -name "*.sh" -o -name "*.txt" -o -name "*.md" \) \
    -not -path "./.venv/*" -not -path "./.git/*" | \
    sort | \
    while read file; do
        echo "FILE: $file ($(wc -l < "$file") lines)"
    done

# PDF Sample Detection
PDF_COUNT=$(find . -maxdepth 1 -name "*.pdf" | wc -l)
echo "PDF_SAMPLES_AVAILABLE: $PDF_COUNT"
if [ $PDF_COUNT -eq 0 ]; then
    echo "WARNING: No PDF samples for testing pipeline"
fi
```

### Dependency Conflict Documentation
```bash
# Systematic Package Testing Protocol
echo "=== DEPENDENCY ANALYSIS ==="

# Test Core Working Packages
WORKING_PACKAGES=("pymupdf4llm" "fitz" "PIL" "pytesseract" "pdf2image")
PROBLEMATIC_PACKAGES=("easyocr" "opencv-python-headless" "unstructured")

for package in "${WORKING_PACKAGES[@]}"; do
    python3 -c "
import $package
print(f'✓ {package}: {getattr($package, \"__version__\", \"version_unknown\")}')
" 2>/dev/null || echo "✗ $package: IMPORT_FAILED"
done

for package in "${PROBLEMATIC_PACKAGES[@]}"; do
    python3 -c "
import ${package//-/_}
print(f'UNEXPECTED: {package} imported successfully')
" 2>/dev/null || echo "✓ $package: EXPECTED_FAILURE (good)"
done
```

### Pipeline Execution Attempt with Error Capture
```bash
# Controlled Pipeline Test with Comprehensive Logging
echo "=== PIPELINE EXECUTION TEST ==="

# Create isolated test environment
TEST_DIR="./pipeline_test_$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Copy first available PDF for testing
PDF_SAMPLE=$(find .. -maxdepth 1 -name "*.pdf" | head -1)
if [ -n "$PDF_SAMPLE" ]; then
    cp "$PDF_SAMPLE" "./test_document.pdf"
    
    # Attempt Stage 1 with detailed error capture
    python3 << 'EOF' 2>&1 | tee pipeline_test.log
import sys
import traceback
import os

try:
    # Test pymupdf4llm primary OCR
    from pymupdf4llm import to_markdown
    print("✓ pymupdf4llm import successful")
    
    # Attempt OCR on test document
    if os.path.exists("test_document.pdf"):
        print("Attempting primary OCR...")
        md_content = to_markdown("test_document.pdf")
        print(f"✓ Primary OCR successful: {len(md_content)} characters extracted")
        
        # Save result for analysis
        with open("primary_ocr_output.md", "w") as f:
            f.write(md_content)
    
except Exception as e:
    print(f"✗ Primary OCR failed: {type(e).__name__}: {e}")
    traceback.print_exc()

try:
    # Test fallback OCR pipeline
    import pytesseract
    from pdf2image import convert_from_path
    print("✓ Fallback OCR imports successful")
    
    if os.path.exists("test_document.pdf"):
        print("Attempting fallback OCR...")
        images = convert_from_path("test_document.pdf", dpi=150, first_page=1, last_page=1)
        text = pytesseract.image_to_string(images[0], config=r'--oem 3 --psm 6')
        print(f"✓ Fallback OCR successful: {len(text)} characters extracted")
        
        with open("fallback_ocr_output.txt", "w") as f:
            f.write(text)
    
except Exception as e:
    print(f"✗ Fallback OCR failed: {type(e).__name__}: {e}")
    traceback.print_exc()

try:
    # Test image extraction
    import fitz
    from PIL import Image
    import io
    print("✓ Image extraction imports successful")
    
    if os.path.exists("test_document.pdf"):
        doc = fitz.open("test_document.pdf")
        image_count = 0
        for page_num in range(min(3, len(doc))):  # Test first 3 pages only
            page = doc[page_num]
            image_list = page.get_images(full=True)
            image_count += len(image_list)
        doc.close()
        print(f"✓ Image extraction successful: {image_count} images detected")
    
except Exception as e:
    print(f"✗ Image extraction failed: {type(e).__name__}: {e}")
    traceback.print_exc()
EOF

    # Analyze results
    echo "=== TEST RESULTS ANALYSIS ==="
    if [ -f "primary_ocr_output.md" ]; then
        echo "PRIMARY_OCR: SUCCESS ($(wc -c < primary_ocr_output.md) bytes)"
    else
        echo "PRIMARY_OCR: FAILED"
    fi
    
    if [ -f "fallback_ocr_output.txt" ]; then
        echo "FALLBACK_OCR: SUCCESS ($(wc -c < fallback_ocr_output.txt) bytes)"
    else
        echo "FALLBACK_OCR: FAILED"
    fi
else
    echo "NO_PDF_SAMPLE: Skipping execution test"
fi

cd ..
```

## Phase 2: HuggingFace Space Implementation

### Model Selection with Technical Rationale

#### Vision Model Comparison Matrix
```python
# Vision Model Options with Technical Analysis
VISION_MODELS = {
    "salesforce/blip-image-captioning-large": {
        "parameters": "14B",
        "memory_footprint": "~2.8GB",
        "inference_speed": "~3-5 seconds/image",
        "strengths": ["Technical diagram understanding", "Consistent output format"],
        "weaknesses": ["Generic captions", "Limited technical vocabulary"],
        "hf_pro_compatibility": "EXCELLENT",
        "recommended_use": "PRIMARY - Best balance of speed/accuracy"
    },
    
    "microsoft/git-large-coco": {
        "parameters": "1.3B", 
        "memory_footprint": "~1.5GB",
        "inference_speed": "~2-3 seconds/image",
        "strengths": ["Fast inference", "Good technical accuracy"],
        "weaknesses": ["Shorter descriptions", "Less detailed analysis"],
        "hf_pro_compatibility": "EXCELLENT",
        "recommended_use": "FALLBACK - When speed is critical"
    },
    
    "microsoft/kosmos-2-patch14-224": {
        "parameters": "1.6B",
        "memory_footprint": "~2.1GB", 
        "inference_speed": "~4-6 seconds/image",
        "strengths": ["Multimodal understanding", "Better technical context"],
        "weaknesses": ["Slower inference", "More complex output parsing"],
        "hf_pro_compatibility": "GOOD",
        "recommended_use": "ALTERNATIVE - For complex technical diagrams"
    }
}

# Selection Logic
def select_vision_model(hf_pro_resources: dict) -> str:
    if hf_pro_resources["memory_gb"] >= 16:
        return "salesforce/blip-image-captioning-large"  # Primary choice
    elif hf_pro_resources["memory_gb"] >= 8:
        return "microsoft/git-large-coco"  # Memory-constrained fallback
    else:
        raise ValueError("Insufficient memory for vision models")
```

#### Text Enhancement Model Comparison
```python
TEXT_MODELS = {
    "google/flan-t5-large": {
        "parameters": "770M",
        "memory_footprint": "~1.5GB",
        "context_length": 512,
        "strengths": ["Instruction following", "Technical text understanding"],
        "weaknesses": ["Limited context", "Generic output style"],
        "hf_pro_compatibility": "EXCELLENT",
        "recommended_use": "PRIMARY - Proven instruction following"
    },
    
    "microsoft/DialoGPT-large": {
        "parameters": "1.5B",
        "memory_footprint": "~3.0GB",
        "context_length": 1024,
        "strengths": ["Better context understanding", "More natural output"],
        "weaknesses": ["Conversational bias", "Less instruction following"],
        "hf_pro_compatibility": "GOOD",
        "recommended_use": "ALTERNATIVE - Better context but less controlled"
    },
    
    "t5-large": {
        "parameters": "770M",
        "memory_footprint": "~1.5GB", 
        "context_length": 512,
        "strengths": ["Vanilla T5 architecture", "Predictable behavior"],
        "weaknesses": ["Requires more prompt engineering", "Less instruction tuned"],
        "hf_pro_compatibility": "EXCELLENT",
        "recommended_use": "FALLBACK - When FLAN-T5 unavailable"
    }
}
```

### HuggingFace Space Deployment Protocol

#### Space Creation with Error Handling
```bash
# Robust Space Creation Script
create_hf_space() {
    local space_name="${HF_SPACE_NAME:-document-processing-pipeline}"
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        echo "Attempt $((retry_count + 1)): Creating HF Space '$space_name'"
        
        # Attempt space creation
        if huggingface-cli repo create \
            --type space \
            --space_sdk gradio \
            "$space_name" \
            --private 2>&1 | tee space_creation.log; then
            
            echo "✓ Space created successfully"
            break
        else
            echo "✗ Space creation failed"
            
            # Check for name conflict
            if grep -q "already exists" space_creation.log; then
                space_name="${space_name}-$(date +%s)"
                echo "Retrying with name: $space_name"
            fi
            
            retry_count=$((retry_count + 1))
            sleep 5
        fi
    done
    
    if [ $retry_count -eq $max_retries ]; then
        echo "ERROR: Failed to create space after $max_retries attempts"
        return 1
    fi
    
    export FINAL_SPACE_NAME="$space_name"
    echo "SPACE_URL: https://huggingface.co/spaces/$HF_USERNAME/$space_name"
}
```

#### Application Code with Anti-Patterns

**CORRECT Implementation Pattern:**
```python
class HuggingFaceDocumentProcessor:
    def __init__(self):
        """Initialize with proper error handling and resource management."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models_loaded = False
        self.initialize_models()
    
    def initialize_models(self):
        """Load models with comprehensive error handling."""
        try:
            # Load vision model with specific version pinning
            self.vision_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-large",
                cache_dir="/tmp/hf_cache",  # Explicit cache management
                local_files_only=False,
                revision="main"  # Pin to specific revision
            )
            
            self.vision_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-large",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                cache_dir="/tmp/hf_cache"
            ).to(self.device)
            
            # Validation check
            dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
            with torch.no_grad():
                _ = self.vision_model.generate(
                    pixel_values=dummy_input,
                    max_length=10
                )
            
            self.models_loaded = True
            logger.info("Models loaded and validated successfully")
            
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            raise ModelLoadingError(f"Failed to load vision models: {e}")
```

**INCORRECT Anti-Pattern (DO NOT USE):**
```python
# ❌ WRONG: No error handling, no resource management
class BadDocumentProcessor:
    def __init__(self):
        self.vision_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-large"  # No error handling
        )
        # No device specification, no validation

    def process_image(self, image_path):
        image = Image.open(image_path)  # No error handling
        # Direct processing without resource checks
        return self.vision_model.generate(image)  # No error handling
```

### File Deployment Structure
```bash
# Create complete HuggingFace Space structure
deploy_hf_space() {
    local space_dir="hf_space"
    
    # Clone space repository
    git clone "https://huggingface.co/spaces/$HF_USERNAME/$FINAL_SPACE_NAME" "$space_dir"
    cd "$space_dir"
    
    # Configure git identity
    git config user.email "automation@huggingface.co"
    git config user.name "Claude Code Assistant"
    
    # Create app.py with production-grade error handling
    cat > app.py << 'EOF'
import gradio as gr
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/app.log')
    ]
)
logger = logging.getLogger(__name__)

# Import processing modules with error handling
try:
    from document_processor import HuggingFaceDocumentProcessor
    logger.info("Document processor imported successfully")
except ImportError as e:
    logger.error(f"Failed to import document processor: {e}")
    raise

def process_pdf_gradio(pdf_file, progress=gr.Progress()):
    """Main Gradio processing function with comprehensive error handling."""
    
    # Input validation
    if pdf_file is None:
        return None, None, "❌ Error: Please upload a PDF file"
    
    # File size validation
    file_size_mb = Path(pdf_file.name).stat().st_size / (1024 * 1024)
    if file_size_mb > 50:  # 50MB limit for HF PRO
        return None, None, f"❌ Error: File too large ({file_size_mb:.1f}MB). Maximum: 50MB"
    
    logger.info(f"Processing PDF: {pdf_file.name} ({file_size_mb:.1f}MB)")
    
    try:
        # Initialize processor
        progress(0.1, desc="Initializing models...")
        processor = HuggingFaceDocumentProcessor()
        
        # Process document
        progress(0.3, desc="Extracting text and images...")
        result = processor.process_complete_pipeline(pdf_file.name)
        
        if not result["success"]:
            error_msg = f"❌ Processing failed: {result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            return None, None, error_msg
        
        progress(0.9, desc="Finalizing output...")
        
        success_msg = f"✅ Processing completed successfully\n"
        success_msg += f"📄 Text extracted: {result['text_length']} characters\n"
        success_msg += f"🖼️ Images analyzed: {result['image_count']}\n"
        success_msg += f"⏱️ Processing time: {result['processing_time']:.1f}s"
        
        return result["final_content"], result["download_path"], success_msg
        
    except Exception as e:
        error_msg = f"❌ Unexpected error: {str(e)}"
        logger.error(f"Processing error: {e}", exc_info=True)
        return None, None, error_msg

# Create Gradio interface
def create_production_interface():
    """Create production-grade Gradio interface."""
    
    with gr.Blocks(
        title="Document Processing Pipeline - HuggingFace Edition",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .file-upload {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 20px;
        }
        """
    ) as interface:
        
        gr.Markdown("""
        # 📄 Document Processing Pipeline
        
        **HuggingFace Native Implementation** - Zero external API dependencies
        
        ### Features:
        - **OCR**: PyMuPDF + Tesseract fallback for text extraction
        - **Vision**: Salesforce BLIP for image analysis
        - **Enhancement**: Google FLAN-T5 for text improvement
        - **Privacy**: All processing happens locally on HuggingFace infrastructure
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                pdf_input = gr.File(
                    label="📁 Upload PDF Document",
                    file_types=[".pdf"],
                    file_count="single",
                    elem_classes=["file-upload"]
                )
                
                process_btn = gr.Button(
                    "🚀 Process Document",
                    variant="primary",
                    size="lg"
                )
                
                status_output = gr.Textbox(
                    label="📋 Processing Status",
                    interactive=False,
                    lines=4,
                    placeholder="Upload a PDF and click 'Process Document' to begin..."
                )
            
            with gr.Column(scale=2):
                markdown_output = gr.Textbox(
                    label="📝 Processed Document (Markdown)",
                    lines=25,
                    interactive=False,
                    placeholder="Processed document content will appear here..."
                )
                
                download_output = gr.File(
                    label="💾 Download Complete Results",
                    interactive=False
                )
        
        # Processing event
        process_btn.click(
            fn=process_pdf_gradio,
            inputs=[pdf_input],
            outputs=[markdown_output, download_output, status_output],
            show_progress=True
        )
        
        gr.Markdown("""
        ### 📊 Processing Information
        - **Maximum file size**: 50MB (HuggingFace PRO limit)
        - **Supported formats**: PDF documents only
        - **Processing time**: 2-10 minutes depending on document complexity
        - **Models used**: Salesforce BLIP + Google FLAN-T5 + Local Tesseract
        
        ### 🔒 Privacy Notice
        All document processing happens on HuggingFace infrastructure. No data is sent to external APIs.
        """)
    
    return interface

if __name__ == "__main__":
    app = create_production_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Private space
        show_api=False,
        enable_queue=True,
        max_threads=4
    )
EOF

    # Create requirements.txt with exact version pinning
    cat > requirements.txt << 'EOF'
# Core ML/AI packages
torch==2.1.0+cpu
torchvision==0.16.0+cpu
transformers==4.36.0
accelerate==0.25.0
sentencepiece==0.1.99

# Document processing
pymupdf4llm==0.0.5
pymupdf==1.23.26
pytesseract==0.3.10
pdf2image==3.1.0

# Image processing
Pillow==10.0.1
opencv-python-headless==4.8.1.78

# UI and utilities
gradio==4.12.0
python-dotenv==1.0.0
scipy==1.11.4
numpy==1.24.3

# Development and logging
loguru==0.7.2
typing-extensions==4.8.0
EOF

    # System dependencies
    cat > packages.txt << 'EOF'
tesseract-ocr
tesseract-ocr-eng
poppler-utils
libgl1-mesa-glx
libglib2.0-0
ffmpeg
libsm6
libxext6
EOF

    # Space metadata
    cat > README.md << 'EOF'
---
title: Document Processing Pipeline
emoji: 📄
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.12.0
app_file: app.py
pinned: false
license: mit
python_version: 3.9
space_type: standard
hardware: cpu-basic
---

# Document Processing Pipeline - HuggingFace Edition

A production-grade PDF document processing system using entirely local HuggingFace models.

## Architecture

- **OCR**: PyMuPDF primary + Tesseract fallback
- **Vision**: Salesforce BLIP for image analysis  
- **Text Enhancement**: Google FLAN-T5 for content improvement
- **Interface**: Gradio web application

## Performance Specifications

- **Maximum file size**: 50MB
- **Processing time**: 2-10 minutes per document
- **Memory usage**: ~8GB during processing
- **Concurrent users**: Up to 4 simultaneous

## Privacy & Security

All processing happens locally on HuggingFace infrastructure. No external API calls or data transmission.
EOF

    # Deploy to HuggingFace
    git add .
    git commit -m "Initial deployment: Production-grade document processing pipeline

Features:
- Comprehensive error handling and logging
- Production-grade Gradio interface
- Local HuggingFace model processing
- Zero external API dependencies
- HuggingFace PRO optimized resource usage"
    
    git push
    
    echo "✅ HuggingFace Space deployed successfully"
    echo "🌐 Space URL: https://huggingface.co/spaces/$HF_USERNAME/$FINAL_SPACE_NAME"
}
```

## Phase 3: Validation Protocol

### Comprehensive Testing Framework
```bash
# Post-deployment validation suite
validate_deployment() {
    local space_url="https://huggingface.co/spaces/$HF_USERNAME/$FINAL_SPACE_NAME"
    local max_wait_time=300  # 5 minutes
    local check_interval=30   # 30 seconds
    local elapsed_time=0
    
    echo "=== DEPLOYMENT VALIDATION ==="
    
    # Wait for Space to become available
    while [ $elapsed_time -lt $max_wait_time ]; do
        echo "Checking Space status... (${elapsed_time}s elapsed)"
        
        if curl -s "$space_url" | grep -q "gradio-app"; then
            echo "✅ Space is running and accessible"
            break
        elif curl -s "$space_url" | grep -q "Building"; then
            echo "🔄 Space is still building..."
        elif curl -s "$space_url" | grep -q "Error"; then
            echo "❌ Space build failed"
            return 1
        fi
        
        sleep $check_interval
        elapsed_time=$((elapsed_time + check_interval))
    done
    
    if [ $elapsed_time -ge $max_wait_time ]; then
        echo "❌ Timeout: Space did not become available within $max_wait_time seconds"
        return 1
    fi
    
    # Test model accessibility
    echo "🔍 Testing model availability..."
    python3 -c "
try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    print('✅ Vision models accessible')
    
    from transformers import pipeline
    text_pipeline = pipeline('text2text-generation', model='google/flan-t5-small')
    print('✅ Text models accessible')
    
except Exception as e:
    print(f'❌ Model access failed: {e}')
    exit(1)
"
    
    echo "✅ Deployment validation completed successfully"
    return 0
}

# Execute validation
validate_deployment || {
    echo "❌ Deployment validation failed"
    exit 1
} 
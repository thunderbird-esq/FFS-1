# Troubleshooting Guide

## Common Installation Issues

### Issue 1: Package Installation Failures on macOS Catalina

#### Symptom
```
ERROR: Could not build wheels for opencv-python-headless
error: Microsoft Visual C++ 14.0 is required
```

#### Root Cause
Catalina's compilation toolchain limitations prevent building certain packages from source.

#### Solution
```bash
# Avoid packages requiring compilation
pip install --only-binary :all: -r requirements_locked.txt

# If specific package fails, install pre-built wheel
pip install --prefer-binary package_name

# Last resort: use conda for problematic packages
conda install -c conda-forge opencv
```

### Issue 2: OpenSSL Version Conflicts

#### Symptom
```
ImportError: urllib3 v2.0 only supports OpenSSL 1.1.1+
```

#### Solution
```bash
# Downgrade urllib3 to compatible version
pip install 'urllib3<2.0'

# Or use system OpenSSL
export DYLD_LIBRARY_PATH=/usr/local/opt/openssl@1.1/lib:$DYLD_LIBRARY_PATH
```

### Issue 3: Tesseract Not Found

#### Symptom
```
pytesseract.pytesseract.TesseractNotFoundError: tesseract is not installed
```

#### Solution
```bash
# Install via Homebrew
brew install tesseract

# Add to PATH if needed
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify installation
which tesseract
tesseract --version
```

## Azure Configuration Issues

### Issue 4: Azure Authentication Failures

#### Symptom
```
AuthenticationError: Invalid API key provided
```

#### Diagnostic Script
```python
# diagnose_azure.py

import os
import re
from dotenv import load_dotenv

load_dotenv()

def diagnose_azure_config():
    """Diagnose Azure configuration issues."""
    
    issues = []
    
    # Check endpoint format
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    if not endpoint:
        issues.append("AZURE_OPENAI_ENDPOINT not set")
    elif not endpoint.startswith("https://"):
        issues.append("Endpoint must start with https://")
    elif not endpoint.endswith("/"):
        issues.append("Endpoint must end with /")
    
    # Check API key format
    api_key = os.environ.get("AZURE_OPENAI_KEY", "")
    if not api_key:
        issues.append("AZURE_OPENAI_KEY not set")
    elif len(api_key) != 32:
        issues.append(f"API key wrong length: {len(api_key)} (should be 32)")
    elif not re.match(r'^[a-f0-9]{32}$', api_key):
        issues.append("API key contains invalid characters")
    
    # Check deployment name
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    if not deployment:
        issues.append("AZURE_OPENAI_DEPLOYMENT_NAME not set")
    
    # Check API version
    version = os.environ.get("OPENAI_API_VERSION", "")
    if not version:
        issues.append("OPENAI_API_VERSION not set")
    elif not re.match(r'^\d{4}-\d{2}-\d{2}', version):
        issues.append("API version wrong format (use YYYY-MM-DD-preview)")
    
    if issues:
        print("Azure Configuration Issues Found:")
        for issue in issues:
            print(f"  ✗ {issue}")
        return False
    else:
        print("✓ Azure configuration appears valid")
        return True

if __name__ == "__main__":
    diagnose_azure_config()
```

### Issue 5: Rate Limiting Errors

#### Symptom
```
RateLimitError: Requests to the ChatCompletions_Create Operation under Azure OpenAI have exceeded rate limit
```

#### Solution
```python
# rate_limit_handler.py

import time
from typing import Callable, Any
import random

def retry_with_exponential_backoff(
    func: Callable,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0
) -> Any:
    """Retry function with exponential backoff."""
    
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "rate limit" in str(e).lower():
                if attempt < max_retries - 1:
                    # Add jitter to prevent thundering herd
                    jitter = random.uniform(0, delay * 0.1)
                    sleep_time = min(delay + jitter, max_delay)
                    
                    print(f"Rate limited. Waiting {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)
                    
                    # Exponential backoff
                    delay *= 2
                else:
                    raise
            else:
                raise
    
    raise Exception(f"Max retries ({max_retries}) exceeded")

# Usage in pipeline
def analyze_image_with_retry(llm, image_path):
    return retry_with_exponential_backoff(
        lambda: analyze_image(llm, image_path),
        max_retries=5
    )
```

## OCR Quality Issues

### Issue 6: Poor OCR Results

#### Symptom
- Garbled text output
- Missing content
- Incorrect character recognition

#### Diagnostic and Solution
```python
# improve_ocr_quality.py

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

def preprocess_image_for_ocr(image_path):
    """Apply preprocessing to improve OCR quality."""
    
    # Load image
    img = Image.open(image_path)
    
    # Convert to grayscale
    img = img.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    # Apply sharpening
    img = img.filter(ImageFilter.SHARPEN)
    
    # Convert to numpy array for OpenCV
    img_array = np.array(img)
    
    # Apply thresholding
    _, img_array = cv2.threshold(
        img_array, 0, 255, 
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    
    # Denoise
    img_array = cv2.medianBlur(img_array, 3)
    
    # Deskew
    coords = np.column_stack(np.where(img_array > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    (h, w) = img_array.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    img_array = cv2.warpAffine(
        img_array, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    
    return Image.fromarray(img_array)

def multi_config_ocr(image_path):
    """Try multiple OCR configurations."""
    
    # Preprocess image
    processed_img = preprocess_image_for_ocr(image_path)
    
    configs = [
        '--oem 3 --psm 6',  # Uniform block
        '--oem 3 --psm 4',  # Single column
        '--oem 3 --psm 3',  # Automatic
        '--oem 3 --psm 11', # Sparse text
        '--oem 3 --psm 12', # Sparse text with OSD
    ]
    
    results = []
    
    for config in configs:
        try:
            text = pytesseract.image_to_string(processed_img, config=config)
            confidence = pytesseract.image_to_data(
                processed_img, config=config, 
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            conf_values = [int(c) for c in confidence['conf'] if int(c) > 0]
            avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0
            
            results.append({
                'config': config,
                'text': text,
                'confidence': avg_conf,
                'length': len(text.strip())
            })
        except Exception as e:
            print(f"Config {config} failed: {e}")
    
    # Select best result
    best_result = max(results, key=lambda x: x['confidence'] * len(x['text']))
    
    return best_result['text']
```

## Pipeline Execution Issues

### Issue 7: Memory Exhaustion

#### Symptom
```
MemoryError
Killed: 9
```

#### Solution
```python
# memory_manager.py

import gc
import resource
import psutil

def set_memory_limit(limit_gb: float):
    """Set memory limit for process."""
    limit_bytes = int(limit_gb * 1024 * 1024 * 1024)
    resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))

def check_memory_usage():
    """Check current memory usage."""
    process = psutil.Process()
    mem_info = process.memory_info()
    return mem_info.rss / 1024 / 1024  # MB

def process_with_memory_management(pdf_files, batch_size=5):
    """Process files in batches to manage memory."""
    
    for i in range(0, len(pdf_files), batch_size):
        batch = pdf_files[i:i+batch_size]
        
        for pdf in batch:
            # Check memory before processing
            mem_usage = check_memory_usage()
            if mem_usage > 4000:  # 4GB threshold
                print(f"High memory usage: {mem_usage}MB. Running garbage collection...")
                gc.collect()
            
            # Process file
            process_pdf(pdf)
        
        # Force garbage collection after batch
        gc.collect()
        
        print(f"Batch {i//batch_size + 1} complete. Memory: {check_memory_usage()}MB")
```

### Issue 8: Stage Failures

#### Recovery Script
```bash
#!/bin/bash
# recover_pipeline.sh

# Determine which stage failed and recover

echo "Pipeline Recovery Tool"
echo "===================="

# Check Stage 1
if [ ! -d "preprocessed_markdown" ] || [ -z "$(ls -A preprocessed_markdown 2>/dev/null)" ]; then
    echo "Stage 1 incomplete. Rerunning..."
    python stage_1_processing_enhanced.py || {
        echo "Stage 1 recovery failed"
        exit 1
    }
fi

# Check Stage 2
if [ ! -d "final_markdown" ] || [ -z "$(ls -A final_markdown 2>/dev/null)" ]; then
    echo "Stage 2 incomplete. Rerunning..."
    python stage_2_processing_enhanced.py || {
        echo "Stage 2 recovery failed"
        exit 1
    }
fi

# Check Stage 3
if [ ! -d "markitdown_output" ] || [ -z "$(ls -A markitdown_output 2>/dev/null)" ]; then
    echo "Stage 3 incomplete. Rerunning..."
    python stage_3_processing_enhanced.py || {
        echo "Stage 3 recovery failed"
        exit 1
    }
fi

echo "Pipeline recovery complete"
```

## Validation and Testing

### Comprehensive Test Suite
```python
# test_pipeline.py

import unittest
import os
import sys
from pathlib import Path

class TestPipelineComponents(unittest.TestCase):
    """Test suite for pipeline components."""
    
    def test_environment(self):
        """Test environment setup."""
        # Check Python version
        version = sys.version_info
        self.assertEqual(version.major, 3)
        self.assertEqual(version.minor, 9)
    
    def test_imports(self):
        """Test all required imports."""
        try:
            import pymupdf4llm
            import fitz
            import PIL
            import pytesseract
            import pdf2image
            import langchain_openai
            import markitdown
            import dotenv
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_azure_variables(self):
        """Test Azure environment variables."""
        required = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_KEY",
            "AZURE_OPENAI_DEPLOYMENT_NAME",
            "OPENAI_API_VERSION",
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
        ]
        
        for var in required:
            self.assertIn(var, os.environ, f"Missing: {var}")
    
    def test_system_commands(self):
        """Test system dependencies."""
        import subprocess
        
        # Test tesseract
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        # Test poppler
        result = subprocess.run(['pdftoppm', '-v'], 
                              capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
    
    def test_directory_structure(self):
        """Test pipeline directory structure."""
        directories = [
            "preprocessed_markdown",
            "document_assets",
            "final_markdown",
            "markitdown_output"
        ]
        
        for dir_name in directories:
            Path(dir_name).mkdir(exist_ok=True)
            self.assertTrue(Path(dir_name).exists(), f"Missing: {dir_name}")

if __name__ == "__main__":
    unittest.main()
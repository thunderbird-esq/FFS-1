# Document Processing Pipeline - Technical Implementation Specification

## System Architecture

### Three-Stage Processing Pipeline
```python
PIPELINE_ARCHITECTURE = {
    "stage_1": {
        "name": "Local OCR and Asset Extraction",
        "engines": {
            "primary": "pymupdf4llm==0.0.5",
            "pdf_manipulation": "pymupdf==1.23.26",
            "image_processing": "Pillow==8.4.0",
            "fallback_ocr": ["pytesseract==0.3.10", "pdf2image==3.1.0"]
        },
        "output": {
            "text": "preprocessed_markdown/*.md",
            "images": "document_assets/{base_filename}/*.png",
            "metadata": "document_assets/{base_filename}/_extraction_log.json"
        }
    },
    "stage_2": {
        "name": "Azure OpenAI Vision Enhancement",
        "engines": {
            "vision": "Azure OpenAI GPT-4V",
            "text_enhancement": "langchain-openai==0.1.7"
        },
        "output": {
            "enhanced_markdown": "final_markdown/*.md",
            "image_analysis": "document_assets/{base_filename}/_manifest.json"
        },
        "cost_model": {
            "per_image": 0.00765,
            "per_1k_tokens": 0.03
        }
    },
    "stage_3": {
        "name": "Final Document Intelligence",
        "engines": {
            "processor": "markitdown[all]==0.0.1a1",
            "azure_di": "Azure Document Intelligence",
            "llm": "gpt-4o"
        },
        "output": {
            "final_documents": "markitdown_output/*.md"
        },
        "cost_model": {
            "per_page_range": [0.50, 15.00]
        }
    }
}
```

## Environment Requirements

### macOS Catalina 10.15.7 Constraints
```python
SYSTEM_REQUIREMENTS = {
    "os_kernel": "Darwin 19.6.0",
    "openssl_version": "1.1.1",
    "xcode_tools_max": "12.4",
    "python_version": "3.9.x",
    "compilation_limits": {
        "cpp_standard": "C++14",
        "cmake_unavailable_for": ["opencv-python-headless", "easyocr"],
        "binary_only_packages": True
    }
}
```

## Execution Phases

### Phase 1: Environment Initialization (20 minutes)
```python
PHASE_1_STEPS = [
    {
        "step": "validate_system",
        "command": """
uname -a | grep -q "Darwin 19.6.0" || { echo "ERROR: Requires macOS Catalina 10.15.7"; exit 1; }
python3 --version | grep -qE "3\\.9\\.[0-9]+" || { echo "ERROR: Requires Python 3.9.x"; exit 1; }
        """,
        "timeout_seconds": 30,
        "failure_action": "halt"
    },
    {
        "step": "install_system_deps",
        "command": """
command -v brew &>/dev/null || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install tesseract poppler || exit 1
tesseract --version && pdftoppm -v || exit 1
        """,
        "timeout_seconds": 300,
        "failure_action": "halt"
    },
    {
        "step": "setup_python_env",
        "command": """
curl -LsSf https://astral.sh/uv/install.sh | sh && source "$HOME/.cargo/env"
rm -rf .venv && uv venv --python 3.9
source .venv/bin/activate
        """,
        "timeout_seconds": 180,
        "failure_action": "halt"
    },
    {
        "step": "install_packages",
        "command": """
cat > requirements_locked.txt << 'EOF'
pymupdf4llm==0.0.5
pymupdf==1.23.26
Pillow==8.4.0
python-dotenv==1.0.0
langchain-openai==0.1.7
markitdown[all]==0.0.1a1
pytesseract==0.3.10
pdf2image==3.1.0
typing-extensions==4.8.0
setuptools==68.2.2
wheel==0.42.0
EOF
uv pip install --no-cache-dir -r requirements_locked.txt
        """,
        "timeout_seconds": 300,
        "failure_action": "halt"
    }
]
```

### Phase 2: Azure Service Configuration (10 minutes)
```python
PHASE_2_AZURE_CONFIG = {
    "required_env_vars": {
        "AZURE_OPENAI_ENDPOINT": {
            "format": "https://*.openai.azure.com/",
            "validation_regex": "^https://.*\\.openai\\.azure\\.com/$"
        },
        "AZURE_OPENAI_KEY": {
            "format": "32-character hex string",
            "validation_regex": "^[a-f0-9]{32}$"
        },
        "AZURE_OPENAI_DEPLOYMENT_NAME": {
            "format": "alphanumeric with hyphens",
            "validation_regex": "^[a-zA-Z0-9-]+$"
        },
        "OPENAI_API_VERSION": {
            "format": "YYYY-MM-DD-preview",
            "validation_regex": "^[0-9]{4}-[0-9]{2}-[0-9]{2}.*$"
        },
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": {
            "format": "https://*.cognitiveservices.azure.com/",
            "validation_regex": "^https://.*\\.cognitiveservices\\.azure\\.com/$"
        }
    },
    "connectivity_test": """
from langchain_openai import AzureChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage
import os

llm = AzureChatOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    openai_api_version=os.environ["OPENAI_API_VERSION"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    temperature=0
)

response = llm.invoke([
    SystemMessage(content="Test"),
    HumanMessage(content="Respond with: Azure OpenAI working")
])

assert "working" in response.content.lower(), "Azure OpenAI test failed"
    """
}
```

### Phase 3: Pipeline Enhancement Scripts (15 minutes)
```python
PHASE_3_SCRIPT_GENERATION = {
    "stage_1_enhanced": "stage_1_processing_enhanced.py",
    "stage_2_enhanced": "stage_2_processing_enhanced.py",
    "stage_3_enhanced": "stage_3_processing_enhanced.py",
    "runner_script": "run_pipeline_enhanced.sh"
}
```

### Phase 4: Pipeline Execution (30 minutes)
```python
PHASE_4_EXECUTION = {
    "test_pdf_generation": """
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas('test_document.pdf', pagesize=letter)
c.drawString(100, 750, 'Pipeline Validation Document')
c.drawString(100, 720, 'Technical content: API HTTP JSON PDF OCR Azure OpenAI')
c.rect(100, 500, 200, 100, fill=1)
c.drawString(120, 540, 'Test Graphic')
c.showPage()
c.drawString(100, 750, 'Page 2 - Multi-page test')
c.save()
    """,
    "execution_command": "./run_pipeline_enhanced.sh",
    "timeout_seconds": 1800,
    "validation_checks": [
        "test -d preprocessed_markdown && test -n '$(ls -A preprocessed_markdown)'",
        "test -d document_assets && test -n '$(ls -A document_assets)'",
        "test -d final_markdown && test -n '$(ls -A final_markdown)'",
        "test -d markitdown_output && test -n '$(ls -A markitdown_output)'"
    ]
}
```

## Performance Metrics

### Expected Processing Times
```python
PERFORMANCE_BENCHMARKS = {
    "stage_1": {
        "per_page_seconds": [2, 5],
        "accuracy_range": [0.85, 0.95],
        "memory_usage_mb": 500
    },
    "stage_2": {
        "per_image_seconds": [1, 3],
        "api_latency_ms": [200, 1000],
        "memory_usage_mb": 1000
    },
    "stage_3": {
        "per_document_seconds": [10, 60],
        "memory_usage_mb": 2000
    }
}
```

## Error Recovery Procedures

### Package Installation Failures
```python
RECOVERY_PROCEDURES = {
    "package_installation": [
        "pip cache purge",
        "pip install --no-cache-dir --prefer-binary -r requirements_locked.txt",
        "for pkg in $(cat requirements_locked.txt); do pip install --no-cache-dir $pkg || true; done",
        "python -m pip install --upgrade pip setuptools wheel"
    ],
    "azure_connectivity": [
        "echo $AZURE_OPENAI_ENDPOINT | grep -q 'https://' || echo 'Invalid endpoint format'",
        "curl -I $AZURE_OPENAI_ENDPOINT 2>/dev/null | head -n 1 | grep 200",
        "python -c 'import os; print(len(os.environ.get(\"AZURE_OPENAI_KEY\", \"\")))'",
        "nslookup $(echo $AZURE_OPENAI_ENDPOINT | sed 's|https://||' | sed 's|/.*||')"
    ],
    "ocr_failure": [
        "tesseract --list-langs",
        "convert -version",
        "python -c 'import pytesseract; print(pytesseract.get_tesseract_version())'",
        "python -c 'from pdf2image import convert_from_path; print(\"pdf2image working\")'"
    ]
}
```

## Quality Validation

### OCR Quality Metrics
```python
QUALITY_CHECKS = {
    "ocr_validation": {
        "minimum_characters": 100,
        "required_term_presence": ["technical_terms", "document_structure", "readable_sentences"],
        "fallback_trigger_threshold": 50
    },
    "image_analysis_validation": {
        "required_fields": ["category", "description", "filename"],
        "category_values": ["Screenshot", "Diagram", "Code Snippet", "Illustration", "Table"],
        "description_min_length": 20
    },
    "final_document_validation": {
        "structure_elements": ["headers", "paragraphs", "lists", "code_blocks"],
        "minimum_sections": 2,
        "image_references": True
    }
}
```
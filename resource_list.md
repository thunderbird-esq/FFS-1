# External Resources and Dependencies

## Required System Resources

### Homebrew Packages
```bash
# Install via Homebrew
brew install tesseract poppler

# Verify installations
tesseract --version  # Should return 4.x or 5.x
pdftoppm -v         # Should return poppler utilities version
```

### Python Package Sources

#### Primary Repository (PyPI)
```python
PYPI_PACKAGES = {
    "pymupdf4llm": {
        "source": "https://pypi.org/project/pymupdf4llm/",
        "version": "0.0.5",
        "hash": "sha256:check_pypi_for_current_hash"
    },
    "pymupdf": {
        "source": "https://pypi.org/project/PyMuPDF/",
        "version": "1.23.26",
        "wheels": "pre-compiled for macOS available"
    },
    "langchain-openai": {
        "source": "https://pypi.org/project/langchain-openai/",
        "version": "0.1.7",
        "dependencies": ["openai", "langchain-core"]
    },
    "markitdown": {
        "source": "https://pypi.org/project/markitdown/",
        "version": "0.0.1a1",
        "extras": "[all]",
        "status": "alpha"
    }
}
```

## Azure Service Endpoints

### Required Azure Resources
```yaml
azure_resources:
  openai_service:
    type: "Azure OpenAI Service"
    required_models:
      - "gpt-4o"
      - "gpt-4-vision"
    endpoint_format: "https://{resource-name}.openai.azure.com/"
    api_version: "2024-02-15-preview"
    
  document_intelligence:
    type: "Azure AI Document Intelligence"
    tier: "Standard S0"
    endpoint_format: "https://{resource-name}.cognitiveservices.azure.com/"
    features_used:
      - "Layout API"
      - "General Document API"
```

## External Documentation References

### Pipeline Components
- **pymupdf4llm**: https://github.com/pymupdf/pymupdf4llm
- **Azure OpenAI**: https://learn.microsoft.com/azure/ai-services/openai/
- **Document Intelligence**: https://learn.microsoft.com/azure/ai-services/document-intelligence/
- **MarkItDown**: https://github.com/microsoft/markitdown

### Troubleshooting Resources
- **macOS Catalina Python Issues**: https://github.com/pyenv/pyenv/wiki/Common-build-problems#macos
- **Tesseract OCR Configuration**: https://github.com/tesseract-ocr/tesseract/wiki/ImproveQuality
- **Azure API Rate Limits**: https://learn.microsoft.com/azure/ai-services/openai/quotas-limits

## Cost Estimation

### API Pricing (as of 2024)
```python
AZURE_PRICING = {
    "gpt_4o": {
        "input": 0.03,  # per 1K tokens
        "output": 0.06,  # per 1K tokens
    },
    "gpt_4_vision": {
        "per_image": 0.00765,  # per image analysis
    },
    "document_intelligence": {
        "per_page": {
            "layout": 0.50,
            "general": 1.50,
            "custom": 15.00
        }
    }
}

def estimate_document_cost(pages, images):
    """Calculate estimated processing cost for a document."""
    stage1_cost = 0  # Local processing
    stage2_cost = images * AZURE_PRICING["gpt_4_vision"]["per_image"]
    stage3_cost = pages * AZURE_PRICING["document_intelligence"]["per_page"]["layout"]
    return {
        "stage1": stage1_cost,
        "stage2": stage2_cost,
        "stage3": stage3_cost,
        "total": stage1_cost + stage2_cost + stage3_cost
    }
```

## Performance Benchmarks

### Expected Processing Times
```python
PERFORMANCE_METRICS = {
    "stage1_ocr": {
        "pages_per_minute": 12,  # pymupdf4llm
        "fallback_pages_per_minute": 4,  # pytesseract
        "memory_usage_mb": 500
    },
    "stage2_vision": {
        "images_per_minute": 20,  # Azure API rate limit
        "api_latency_ms": [200, 1000],
        "memory_usage_mb": 1000
    },
    "stage3_synthesis": {
        "documents_per_minute": 2,  # MarkItDown with GPT-4o
        "memory_usage_mb": 2000
    }
}
```

## Network Requirements

### Bandwidth and Connectivity
```yaml
network_requirements:
  minimum_bandwidth: "10 Mbps"
  required_endpoints:
    - "*.openai.azure.com"
    - "*.cognitiveservices.azure.com"
    - "pypi.org"
    - "files.pythonhosted.org"
  firewall_rules:
    - "HTTPS (443) outbound"
    - "DNS (53) outbound"
```

## Data Storage Requirements

### Disk Space Estimation
```python
STORAGE_REQUIREMENTS = {
    "per_document": {
        "input_pdf_mb": 10,  # Average
        "extracted_images_mb": 50,  # Average
        "markdown_output_mb": 2,  # Average
        "total_multiplier": 7  # Input size * 7 for all stages
    },
    "system": {
        "python_venv_mb": 500,
        "packages_mb": 800,
        "logs_mb": 100,
        "temp_files_mb": 1000
    }
}

def calculate_storage_needed(num_documents, avg_pdf_size_mb):
    """Calculate total storage requirements."""
    document_storage = num_documents * avg_pdf_size_mb * STORAGE_REQUIREMENTS["per_document"]["total_multiplier"]
    system_storage = sum(STORAGE_REQUIREMENTS["system"].values())
    return {
        "documents_gb": document_storage / 1024,
        "system_gb": system_storage / 1024,
        "total_gb": (document_storage + system_storage) / 1024,
        "recommended_free_gb": ((document_storage + system_storage) * 1.5) / 1024
    }
```
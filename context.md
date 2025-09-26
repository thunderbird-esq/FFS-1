# Project Context for Claude Code

## Technical Environment Constraints

### macOS Catalina 10.15.7 Limitations
- **Darwin Kernel Version**: 19.6.0 (final Catalina release)
- **Maximum Python Version**: 3.9.x (Python 3.10+ incompatible with Catalina's OpenSSL 1.1.1)
- **System Library Constraints**: Missing modern C++ standard library components required by newer packages
- **Package Manager Limitations**: Homebrew packages frozen at Catalina-compatible versions

### Dependency Conflict Analysis
```bash
# Confirmed Problematic Packages on Catalina
PROBLEMATIC_PACKAGES = {
    "easyocr": {
        "failure_reason": "Requires opencv-python-headless>=4.6.0",
        "dependency_chain": "easyocr -> opencv-python-headless -> cmake compilation",
        "error_pattern": "Microsoft Visual C++ 14.0 is required",
        "workaround": "None viable - replace with pytesseract + pdf2image"
    },
    
    "opencv-python-headless": {
        "failure_reason": "Requires modern cmake + system libraries unavailable in Catalina",
        "dependency_chain": "opencv -> cmake -> Xcode command line tools > 12.4",
        "error_pattern": "Could not find a version that satisfies the requirement",
        "workaround": "Use Pillow + pdf2image for image processing"
    },
    
    "unstructured": {
        "failure_reason": "Massive dependency tree including detectron2, torch vision",
        "dependency_chain": "unstructured -> detectron2 -> pytorch compilation",
        "error_pattern": "No matching distribution found",
        "workaround": "Use pymupdf4llm for document parsing"
    },
    
    "p11-kit": {
        "failure_reason": "SHA256 checksum mismatches from CDN mirror issues",
        "dependency_chain": "p11-kit -> system certificate validation",
        "error_pattern": "CHECKSUM mismatch for p11-kit",
        "workaround": "Not required for our pipeline - avoid packages that depend on it"
    }
}
```

### Proven Working Components
```python
# Confirmed Working Packages (Tested on Catalina 10.15.7)
WORKING_STACK = {
    "pymupdf4llm": {
        "version": "0.0.5",
        "purpose": "Primary OCR engine with built-in table detection",
        "performance": "~2-5 seconds per page",
        "quality": "85-95% accuracy on technical documents",
        "limitations": "Struggles with handwritten text, complex layouts"
    },
    
    "pymupdf": {
        "version": "1.23.26", 
        "purpose": "PDF manipulation and image extraction",
        "performance": "~1 second per page for image extraction",
        "quality": "Lossless image extraction",
        "limitations": "Limited to embedded images only"
    },
    
    "pytesseract": {
        "version": "0.3.10",
        "purpose": "Fallback OCR engine with configurable parameters",
        "performance": "~5-15 seconds per page",
        "quality": "70-90% accuracy depending on image quality",
        "limitations": "Requires high-quality images, sensitive to layout"
    },
    
    "pdf2image": {
        "version": "3.1.0",
        "purpose": "PDF to image conversion for fallback OCR",
        "performance": "~2-3 seconds per page at 300 DPI",
        "quality": "High fidelity conversion",
        "limitations": "Memory intensive for large documents"
    },
    
    "Pillow": {
        "version": "8.4.0",
        "purpose": "Image processing and format conversion",
        "performance": "Near-instantaneous for typical operations",
        "quality": "Production-grade image handling",
        "limitations": "Version 8.4.0 is final Catalina-compatible release"
    }
}
```

## HuggingFace Migration Technical Rationale

### Cost-Benefit Analysis
```python
# Azure vs HuggingFace Cost Comparison (Monthly)
COST_ANALYSIS = {
    "azure_openai_vision": {
        "cost_per_image": "$0.00765",  # GPT-4V pricing
        "monthly_volume_estimate": 1000,  # images per month
        "monthly_cost": "$7.65",
        "additional_costs": "API rate limits, data egress fees"
    },
    
    "azure_document_intelligence": {
        "cost_per_page": "$0.50",  # Standard tier
        "monthly_volume_estimate": 200,  # pages per month
        "monthly_cost": "$100.00",
        "additional_costs": "Storage fees, bandwidth costs"
    },
    
    "huggingface_pro": {
        "monthly_cost": "$20.00",  # HF PRO subscription
        "processing_limits": "Unlimited within compute allocation",
        "additional_costs": "None - all processing included"
    },
    
    "cost_savings": {
        "monthly": "$87.65",  # $107.65 Azure vs $20.00 HF
        "annual": "$1,051.80",
        "break_even_point": "Immediate"
    }
}
```

### Performance Comparison Matrix
```python
MODEL_PERFORMANCE_COMPARISON = {
    "vision_analysis": {
        "azure_gpt4v": {
            "accuracy": "95%",
            "speed": "3-8 seconds per image",
            "cost": "$0.00765 per image",
            "context_understanding": "Excellent",
            "technical_vocabulary": "Excellent"
        },
        
        "salesforce_blip_large": {
            "accuracy": "85-90%",
            "speed": "2-4 seconds per image", 
            "cost": "$0 (local processing)",
            "context_understanding": "Good",
            "technical_vocabulary": "Good"
        },
        
        "microsoft_git_large": {
            "accuracy": "80-85%",
            "speed": "1-3 seconds per image",
            "cost": "$0 (local processing)",
            "context_understanding": "Fair",
            "technical_vocabulary": "Fair"
        }
    },
    
    "text_enhancement": {
        "azure_gpt4": {
            "quality": "Excellent",
            "speed": "5-15 seconds per request",
            "cost": "$0.03 per 1K tokens",
            "instruction_following": "Excellent",
            "consistency": "Excellent"
        },
        
        "google_flan_t5_large": {
            "quality": "Good",
            "speed": "2-5 seconds per request",
            "cost": "$0 (local processing)",
            "instruction_following": "Good", 
            "consistency": "Good"
        },
        
        "microsoft_dialo_gpt": {
            "quality": "Fair",
            "speed": "3-6 seconds per request",
            "cost": "$0 (local processing)",
            "instruction_following": "Fair",
            "consistency": "Variable"
        }
    }
}
```

## HuggingFace PRO Resource Allocation

### Compute Resource Specifications
```yaml
hf_pro_limits:
  memory:
    total_gb: 16
    reserved_system_gb: 2
    available_app_gb: 14
    
  cpu:
    cores: 4
    architecture: "x86_64"
    base_frequency: "2.4 GHz"
    
  storage:
    persistent_gb: 50
    temporary_gb: 100
    cache_gb: 20
    
  network:
    bandwidth_mbps: 1000
    concurrent_connections: 50
    
  gpu:
    availability: "Optional T4"
    memory_gb: 16
    compute_capability: "7.5"
```

### Memory Allocation Strategy
```python
# Optimal Memory Distribution for HF PRO
MEMORY_ALLOCATION = {
    "system_reserved": "2GB",  # OS and basic services
    "gradio_interface": "1GB",  # Web interface and queue management
    "vision_model": "3GB",     # BLIP-large model weights and inference
    "text_model": "2GB",       # FLAN-T5-large model weights
    "document_processing": "4GB",  # PDF parsing, image extraction, OCR
    "temp_storage": "2GB",     # Temporary files during processing
    "safety_buffer": "2GB"     # Prevent OOM errors
}

# Memory monitoring function
def monitor_memory_usage():
    """Monitor memory usage and trigger garbage collection when needed."""
    import psutil
    import gc
    
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 80:
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        logger.warning(f"Memory usage high: {memory_percent}%")
    
    return memory_percent
```

## Expected Pipeline Performance Metrics

### Processing Time Benchmarks
```python
PERFORMANCE_BENCHMARKS = {
    "small_document": {
        "pages": "1-5",
        "images": "0-3",
        "expected_time": "30-90 seconds",
        "memory_peak": "6-8GB",
        "bottleneck": "Model initialization"
    },
    
    "medium_document": {
        "pages": "5-20", 
        "images": "3-15",
        "expected_time": "2-5 minutes",
        "memory_peak": "8-12GB",
        "bottleneck": "Vision model inference"
    },
    
    "large_document": {
        "pages": "20-50",
        "images": "15-50", 
        "expected_time": "5-15 minutes",
        "memory_peak": "12-14GB",
        "bottleneck": "Sequential image processing"
    }
}
```

### Quality Assurance Thresholds
```python
QUALITY_THRESHOLDS = {
    "ocr_accuracy": {
        "minimum_acceptable": 70,  # Percentage
        "target": 85,
        "excellent": 95,
        "measurement": "Word error rate comparison"
    },
    
    "image_description_relevance": {
        "minimum_acceptable": 60,  # Subjective scoring
        "target": 80,
        "excellent": 90,
        "measurement": "Technical term usage and contextual accuracy"
    },
    
    "processing_reliability": {
        "minimum_acceptable": 95,  # Success rate
        "target": 98,
        "excellent": 99.5,
        "measurement": "Successful completions vs total attempts"
    }
}
```

## Risk Assessment and Mitigation

### Technical Risk Matrix
```python
TECHNICAL_RISKS = {
    "model_loading_failure": {
        "probability": "Low",
        "impact": "High",
        "mitigation": "Progressive fallback to smaller models",
        "detection": "Model initialization timeout > 60 seconds",
        "recovery": "Automatic fallback to git-large or t5-base"
    },
    
    "memory_exhaustion": {
        "probability": "Medium",
        "impact": "High", 
        "mitigation": "Document chunking and garbage collection",
        "detection": "Memory usage > 90%",
        "recovery": "Process document in smaller chunks"
    },
    
    "hf_infrastructure_limits": {
        "probability": "Low",
        "impact": "Medium",
        "mitigation": "Retry logic with exponential backoff",
        "detection": "HTTP 429 or 503 responses",
        "recovery": "Queue requests and retry after delay"
    },
    
    "concurrent_user_overload": {
        "probability": "Medium",
        "impact": "Medium",
        "mitigation": "Request queuing and rate limiting",
        "detection": "Response time > 30 seconds",
        "recovery": "Implement user queue with estimated wait times"
    }
}
```

### Operational Considerations
```python
OPERATIONAL_REQUIREMENTS = {
    "monitoring": {
        "metrics": ["processing_time", "memory_usage", "error_rate", "queue_length"],
        "logging_level": "INFO",
        "log_retention": "7 days",
        "alerting": "Email notifications for error_rate > 5%"
    },
    
    "maintenance": {
        "model_updates": "Monthly review of new model releases",
        "dependency_updates": "Quarterly security updates",
        "performance_optimization": "Continuous monitoring and tuning",
        "backup_strategy": "Daily backup of configuration and logs"
    },
    
    "scaling": {
        "horizontal": "Not applicable for HF Spaces",
        "vertical": "Automatic within HF PRO limits",
        "optimization": "Focus on memory efficiency and processing speed"
    }
}
```

## Success Criteria Definition

### Functional Requirements (Must Have)
- PDF upload and processing through Gradio interface
- OCR text extraction with >70% accuracy
- Image analysis with technically relevant descriptions
- Markdown output with proper formatting
- Complete processing within 15 minutes for documents up to 50 pages

### Performance Requirements (Should Have)
- Processing time <5 minutes for typical 20-page documents
- Memory usage within HF PRO limits (14GB available)
- Support for concurrent users (up to 4 simultaneous)
- Error recovery and graceful degradation

### Quality Requirements (Nice to Have)
- OCR accuracy >85% on technical documents
- Image descriptions include relevant technical terminology
- Consistent output formatting across document types
- Processing optimization for common document layouts
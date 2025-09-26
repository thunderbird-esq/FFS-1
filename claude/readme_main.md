# Document Processing Pipeline - Quick Start Guide

## Overview
Three-stage document processing pipeline for converting scanned PDFs to structured markdown using local OCR and Azure AI services.

## Prerequisites

### System Requirements
- macOS Catalina 10.15.7 (Darwin 19.6.0)
- Python 3.9.x
- 10GB+ free disk space
- 8GB+ RAM

### Azure Services Required
- Azure OpenAI Service with GPT-4o deployment
- Azure AI Document Intelligence

## Quick Setup (5 Minutes)

### 1. Clone Repository and Navigate to Project
```bash
cd your-project-directory
```

### 2. Run Quick Setup Script
```bash
#!/bin/bash
# quick_setup.sh

# Install system dependencies
brew install tesseract poppler

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.cargo/env"

# Create Python environment
uv venv --python 3.9
source .venv/bin/activate

# Install packages
cat > requirements.txt << 'EOF'
pymupdf4llm==0.0.5
pymupdf==1.23.26
Pillow==8.4.0
python-dotenv==1.0.0
langchain-openai==0.1.7
markitdown[all]==0.0.1a1
pytesseract==0.3.10
pdf2image==3.1.0
EOF

uv pip install -r requirements.txt

echo "Setup complete!"
```

### 3. Configure Azure Credentials
```bash
# Create .env file
cat > .env << 'EOF'
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-32-character-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
OPENAI_API_VERSION=2024-02-15-preview
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-docintel.cognitiveservices.azure.com/
EOF

# Edit .env with your actual credentials
nano .env
```

### 4. Place PDF Files
```bash
# Copy your PDF files to current directory
cp /path/to/your/pdfs/*.pdf .
```

### 5. Run Pipeline
```bash
# Execute complete pipeline
./run_pipeline_enhanced.sh
```

## Expected Output Structure
```
.
├── preprocessed_markdown/     # Stage 1: OCR text output
│   └── document.md
├── document_assets/          # Stage 1: Extracted images
│   └── document/
│       ├── page_001_img_00.png
│       └── _extraction_log.json
├── final_markdown/           # Stage 2: Enhanced with image analysis
│   └── document.md
└── markitdown_output/        # Stage 3: Final processed documents
    ├── document.md
    └── _quality_report.json
```

## Processing Times
- **Stage 1**: ~5 seconds per page
- **Stage 2**: ~2 seconds per image
- **Stage 3**: ~30 seconds per document

## Estimated Costs (USD)
- **Stage 1**: $0.00 (local processing)
- **Stage 2**: ~$0.01 per image
- **Stage 3**: ~$0.50-1.50 per document

## Monitoring Pipeline Execution

### Real-time Monitoring
```bash
# In separate terminal
python .claude/monitor_resources.py
```

### Check Progress
```bash
# View current stage output
ls -la preprocessed_markdown/
ls -la final_markdown/
ls -la markitdown_output/
```

### View Logs
```bash
# Check pipeline logs
tail -f pipeline_logs/pipeline_*.log
```

## Common Commands

### Test Azure Connection
```bash
python -c "
from langchain_openai import AzureChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

llm = AzureChatOpenAI(
    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
    openai_api_version=os.environ['OPENAI_API_VERSION'],
    azure_deployment=os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']
)
print('Azure connection successful!')
"
```

### Process Single PDF
```bash
# Run only Stage 1 on specific file
python -c "
from stage_1_processing_enhanced import process_pdf_document
result = process_pdf_document('your_file.pdf')
print(result)
"
```

### Calculate Costs
```bash
python .claude/calculate_costs.py
```

### Generate Performance Report
```bash
python .claude/analyze_performance.py
```

## Troubleshooting Quick Fixes

### Package Installation Failed
```bash
pip cache purge
pip install --no-cache-dir --prefer-binary -r requirements.txt
```

### Azure Authentication Error
```bash
# Verify credentials
python .claude/diagnose_azure.py
```

### Memory Issues
```bash
# Process in smaller batches
export BATCH_SIZE=3
./run_pipeline_enhanced.sh
```

### Recovery from Failure
```bash
# Resume from last successful stage
./recover_pipeline.sh
```

## Support Files in .claude/

- **PROJECT.md** - Complete technical specification
- **AGENTS.md** - Agentic workflow configuration
- **IMPLEMENTATION.md** - Full script implementations
- **EXECUTION.md** - Detailed execution plan
- **RESOURCES.md** - External dependencies
- **MONITORING.md** - Performance tracking
- **TROUBLESHOOTING.md** - Issue resolution

## Pipeline Stages Explained

### Stage 1: OCR and Image Extraction
- Uses pymupdf4llm for text extraction
- Falls back to pytesseract for difficult pages
- Extracts all images as PNG files
- Creates extraction logs for debugging

### Stage 2: Azure Vision Analysis
- Analyzes each image with GPT-4 Vision
- Generates technical descriptions
- Categorizes images (diagram, screenshot, etc.)
- Creates enhanced markdown with analysis

### Stage 3: Document Synthesis
- Uses MarkItDown with Document Intelligence
- Applies GPT-4o for final processing
- Creates publication-ready markdown
- Generates quality metrics

## Best Practices

1. **Start Small**: Test with 1-2 PDFs first
2. **Monitor Costs**: Check Azure usage regularly
3. **Batch Processing**: Process similar documents together
4. **Quality Check**: Review Stage 1 output before proceeding
5. **Backup Results**: Save outputs after each stage

## Getting Help

### Check Status
```bash
# Validate environment
bash pre_flight_check.sh

# Run test suite
python test_pipeline.py
```

### View Documentation
```bash
# Open this guide
cat .claude/README.md

# View specific stage documentation
grep -A 20 "Stage 1" .claude/IMPLEMENTATION.md
```

### Debug Mode
```bash
# Run with verbose logging
VERBOSE=1 ./run_pipeline_enhanced.sh
```

## Next Steps

1. Review output quality in `markitdown_output/`
2. Adjust prompts in stage scripts if needed
3. Scale up to full document corpus
4. Set up automated monitoring
5. Implement custom post-processing

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Compatibility**: macOS Catalina 10.15.7, Python 3.9.x
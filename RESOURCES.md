Resource Specification
This document outlines all external resources, system dependencies, cloud services, and performance benchmarks required for the successful execution of the document processing pipeline.

1. System Dependencies
These packages must be installed on the host machine. The environment_setup_helper.sh script will validate their presence.

Homebrew Packages
The following packages are required and should be installed via Homebrew:

# Install required system libraries
brew install tesseract poppler coreutils

# To verify installations:
# tesseract --version  (should return 5.x)
# pdftoppm -v          (should return poppler utilities version)
# gtimeout --version     (should return a version from coreutils)

tesseract: The core engine for the fallback OCR in Stage 1.

poppler: Provides the pdf2image library with the necessary utilities to convert PDF pages to images for fallback OCR.

coreutils: Provides the gtimeout command for robust, time-boxed execution of pipeline stages in the master script.

2. Python Dependencies
All Python package dependencies are managed in a single, canonical file.

Single Source of Truth: The requirements.txt file is the definitive manifest for all required Python packages and their versions.

Installation: The environment is built by running uv pip sync requirements.txt via the environment_setup_helper.sh script.

Key Libraries and Their Roles:
pymupdf4llm: The primary engine for layout-aware OCR and text extraction in Stage 1.

pytesseract & pdf2image: The components of the robust fallback OCR mechanism in Stage 1.

langchain-openai: The interface for all interactions with the Azure OpenAI service in Stages 2 and 3.

tenacity: Used to provide resilient, exponential-backoff retry logic for all network-bound API calls.

markitdown: The high-level library used in Stage 3 to orchestrate the final document synthesis with Azure Document Intelligence and OpenAI.

3. Cloud Services
The pipeline is critically dependent on the following configured Azure services.

Required Azure Resources
azure_resources:
  - service: Azure OpenAI Service
    # The endpoint and key must be provided as environment variables.
    # Required Variables: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY
    required_deployments:
      - name: "gpt-4o" # Must match AZURE_OPENAI_DEPLOYMENT_NAME
        purpose: "Used for both vision analysis (Stage 2) and final synthesis (Stage 3)."
    required_api_version: "2024-02-01" # Must match OPENAI_API_VERSION

  - service: Azure Document Intelligence
    # The endpoint and key must be provided as environment variables.
    # Required Variables: AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT, AZURE_DOCUMENT_INTELLIGENCE_KEY
    purpose: "Used by the markitdown library in Stage 3 for layout analysis and synthesis."

4. Performance Benchmarks
These are the expected performance targets for the pipeline running on standard hardware (e.g., MacBook Pro, 16GB RAM).

performance_targets:
  stage1_extraction:
    # Local processing speed for OCR and image extraction.
    documents_per_minute: 5
    max_memory_usage_gb: 4

  stage2_analysis:
    # API-bound processing speed. Assumes standard network latency.
    images_per_minute: 10
    text_chunks_per_minute: 20 # (A chunk is a section between '##' headings)
    max_memory_usage_gb: 2

  stage3_synthesis:
    # API-bound synthesis speed.
    documents_per_minute: 2
    max_memory_usage_gb: 2

5. Data Storage Requirements
Per Document: Expect storage usage to be approximately 5-10 times the original PDF size to account for extracted images, multiple Markdown versions, and logs.

System: The complete environment, including the Python venv and all dependencies, will require approximately 2-3 GB of disk space.

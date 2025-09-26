Project Specification: Automated Document Digitization Pipeline
1. Overview
This document specifies the requirements for an automated, three-stage pipeline designed to convert a corpus of scanned PDF documents, primarily vintage Apple technical manuals, into enriched, analysis-ready Markdown files. The pipeline must be robust, observable, and configurable, suitable for production use.

2. Core Objectives
Ingestion & Extraction: Reliably extract all text and image assets from a directory of source PDF files. The system must be resilient to common issues with scanned documents, such as poor quality OCR.

AI-driven Enrichment: Use Azure OpenAI services to perform two key enrichment tasks:

Vision Analysis: Analyze each extracted image to generate a structured, technical description.

Text Cleanup: Refine the extracted text to correct OCR errors and improve formatting.

Final Synthesis: Synthesize the cleaned text and image analyses into a single, coherent, and professionally formatted Markdown document for each source PDF.

Automation & Reliability: The entire process must be automated by a single master script. The pipeline must be idempotent, resilient to transient errors, and provide comprehensive logging.

3. Key Deliverables
Master Orchestration Script (run_pipeline.sh): A single, executable shell script that runs the entire end-to-end pipeline.

Environment Setup Script (environment_setup_helper.sh): A helper script that creates a Python virtual environment and installs all necessary system and Python dependencies.

Three Python Stage Scripts:

stage_1_processing.py: Handles local OCR and image extraction.

stage_2_processing.py: Handles all Azure OpenAI API interactions for vision and text cleanup.

stage_3_processing.py: Handles the final synthesis using the markitdown library.

Configuration Files: All necessary configuration files, including requirements.txt and .gitignore.

Documentation: A README.md file explaining the project's purpose, setup, and execution.

4. Technical Stack
Orchestration: Bash

Python Version: Python 3.11+

Package Management: uv

System Dependencies: tesseract, poppler (managed via Homebrew)

Core Python Libraries: pymupdf4llm, pytesseract, pdf2image, langchain-openai, tenacity, markitdown

Cloud Services: Azure OpenAI Service (for GPT-4o), Azure Document Intelligence

5. Definition of Done
The project is considered complete when all of the following criteria are met:

[ ] The pipeline can be initiated by a single command (./run_pipeline.sh).

[ ] The pipeline successfully processes a directory of sample PDFs and generates outputs in the specified directory structure.

[ ] Stage 1: Produces both a Markdown file and a corresponding asset directory for each PDF. It successfully uses a fallback OCR mechanism for documents where the primary method fails.

[ ] Stage 2: Correctly analyzes all extracted images, saves the results to a persistent manifest file, and appends the analysis to the Markdown files. It successfully processes large documents by chunking text for cleanup.

[ ] Stage 3: Generates a final, synthesized Markdown document that integrates the image analyses into the main text.

[ ] The entire pipeline is idempotent; running it a second time does not re-process completed files.

[ ] All API calls are wrapped in an exponential backoff retry mechanism.

[ ] All scripts are configurable via command-line arguments and do not contain hardcoded paths.

[ ] All secrets and credentials are managed via environment variables (loaded from a .env file) and are explicitly excluded from version control via .gitignore.

[ ] The pipeline generates structured, timestamped logs for the entire run, including a separate error log.

[ ] Each stage generates a final JSON summary report detailing its execution statistics (files processed, skipped, failed, etc.).

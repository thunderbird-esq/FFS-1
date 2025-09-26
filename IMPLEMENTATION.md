Implementation and Architecture Specification
This document provides the architectural blueprint for the 3-stage document processing pipeline. It details the design, data flow, and core logic of each component.

1. System Architecture Overview
The pipeline is a linear, 3-stage batch processing system designed to be robust, idempotent, and observable. Each stage is a distinct, independently runnable component that consumes artifacts from the previous stage and produces outputs for the next.

Data Flow Diagram
The flow of data through the system is as follows:

[Source PDFs]
      |
      |--> (stage_1_processing.py) --> [preprocessed_markdown/*.md] + [document_assets/{doc}/]
                                                     |                          |
                                                     |                          |
                                                     +--------------------------+
                                                                  |
                                                                  |--> (stage_2_processing.py) --> [final_markdown/*.md]
                                                                                                        |
                                                                                                        |
                                                                                                        |--> (stage_3_processing.py) --> [markitdown_output/*.md]

2. Stage-by-Stage Implementation Design
Stage 1: Local OCR and Asset Extraction
Purpose: To convert opaque PDF files into structured, machine-readable text (Markdown) and visual assets (images), running entirely on the local machine.

Core Logic:

Dual-OCR Strategy: The script first attempts to convert the PDF using pymupdf4llm, which excels at preserving document layout.

Resilient Fallback: It validates the output of the primary OCR. If the text output is empty or minimal, it automatically triggers a fallback mechanism using pytesseract and pdf2image to perform a more direct, page-by-page OCR. This ensures that every document yields a text output.

Asset Extraction: Concurrently, it uses PyMuPDF to scan the document, extract all embedded images, and save them to a dedicated asset directory.

Inputs:

Source PDF files (--pdf-dir).

Outputs:

One Markdown file per PDF in the output directory (--md-dir).

A dedicated asset directory per PDF (--asset-dir/{base_filename}/) containing all extracted images.

A summary log (_stage1_processing.json) detailing the execution statistics.

Stage 2: LLM Vision Analysis and Text Cleanup
Purpose: To enrich the extracted data using Azure OpenAI's GPT-4o model. This stage handles the two most AI-intensive tasks: image analysis and text refinement.

Core Logic:

Idempotent Image Analysis: The script iterates through the images in a document's asset directory. It maintains a _manifest.json file. Before sending an image to the vision API, it checks if an analysis for that image already exists in the manifest. If it does, the API call is skipped, saving significant time and cost on reruns.

Structured Vision Prompting: Images are sent to the vision model with a prompt that explicitly requires the output to be a structured JSON object with a defined schema (category, description, entities). This ensures the output is predictable and machine-parseable.

Context-Aware Text Chunking: The Markdown text is split into logical chunks based on chapter headings (##). Each chunk is sent to the LLM for cleanup, preventing context window overflows for large documents.

Enrichment and Aggregation: The script appends a new "Extracted Image Analysis" section to the cleaned Markdown, containing the structured descriptions from the manifest.

Inputs:

Markdown files from Stage 1 (--source-md-dir).

Asset directories from Stage 1 (--asset-dir).

Outputs:

One enriched Markdown file per input file in the output directory (--output-dir).

An updated _manifest.json in each document's asset directory.

A summary log (_stage2_processing.json) detailing API calls and cost estimations.

Stage 3: Final Document Synthesis
Purpose: To perform a final, holistic synthesis of the enriched data, creating a single, coherent, publication-ready document.

Core Logic:

High-Level Abstraction: The script utilizes the markitdown library to orchestrate the final interaction with Azure Document Intelligence and Azure OpenAI.

Expert Synthesis Prompt: The core of this stage is its prompt. The LLM is instructed to act as an expert technical writer. Its task is not just to clean the document, but to synthesize the main text with the image analyses, integrating the descriptions into the narrative where they are contextually relevant and then removing the redundant analysis section.

Quantitative Quality Analysis: After generating the final document, the script performs a quality check, calculating metrics like header count, code block count, and table presence. This data is saved to a _quality_report.json file, providing a measurable way to assess the pipeline's output quality.

Inputs:

Enriched Markdown files from Stage 2 (--source-dir).

Outputs:

The final, synthesized Markdown document in the output directory (--output-dir).

A summary log (_stage3_processing.json).

A quality report (_quality_report.json) for each processed document.

3. Error Handling and Reliability Strategy
System Level: The master orchestrator (run_pipeline.sh) uses set -euo pipefail to ensure it fails fast and immediately upon any command failure.

API Calls: All network-bound API calls in Stage 2 and Stage 3 are wrapped in a tenacity retry decorator, which automatically handles transient network errors or API throttling with an exponential backoff strategy.

File Level: Each Python script is designed to be resilient to individual file corruption. The processing for each document is contained within a try...except block. A failure on one PDF will be logged, but it will not terminate the entire pipeline; the script will continue to the next file.

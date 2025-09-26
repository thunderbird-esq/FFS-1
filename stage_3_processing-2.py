# stage_3_processing.py
#
# This script performs the final stage of the document processing pipeline.
# It uses the 'markitdown' library to synthesize the cleaned Markdown and
# image analyses from Stage 2 into a final, publication-ready document.

import os
import logging
import argparse
from typing import Optional

# Third-party imports
from dotenv import load_dotenv
from markitdown import MarkItDown

# --- Load Environment Variables ---
# Allows the script to be run standalone for testing. The master script
# will set these variables in the environment directly.
load_dotenv()

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- LLM Prompt for Final Synthesis ---
LLM_PROMPT = """You are an expert technical writer and editor with deep knowledge of classic Apple computer systems, including the Apple II series and classic Macintosh hardware and software (System 6/7).

You will be given a Markdown document that has been pre-processed. This document contains:
1.  Text extracted via OCR from a vintage technical manual or book.
2.  A dedicated section titled 'Extracted Image Analysis' which contains structured descriptions of all images, diagrams, and screenshots from the original document.

Your task is to perform a final synthesis to create a comprehensive, clean, and publication-ready technical document.

Your requirements are:
- **Integrate Content:** Seamlessly weave the image descriptions from the 'Extracted Image Analysis' section into the main body of the text where they are contextually relevant. Do not simply leave them in a block at the end.
- **Synthesize, Don't Just Copy:** Use the image descriptions to enrich the main text. For example, if the text mentions a diagram, insert the detailed description of that diagram as a blockquote or a figure caption.
- **Format for Clarity:** Ensure the final document has a clear hierarchical structure using appropriate Markdown headings (`#`, `##`, `###`).
- **Correct and Format:** Fix any remaining OCR errors, format tables using proper Markdown syntax, and ensure code blocks are correctly identified with language specifiers (e.g., ```assembly, ```c).
- **Preserve Accuracy:** Maintain all technical specifications, historical context, and original terminology with absolute fidelity.
- **Final Output:** Your final output must be only the complete, cleaned, and synthesized Markdown document. Do not include any commentary or explanations about your process.
"""

# --- Core Functions ---

def initialize_markitdown_client() -> Optional[MarkItDown]:
    """
    Initializes and validates the MarkItDown client from environment variables.
    """
    required_vars = [
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
        "AZURE_DOCUMENT_INTELLIGENCE_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_DEPLOYMENT_NAME"
    ]
    if not all(os.getenv(var) for var in required_vars):
        logging.error("One or more required Azure environment variables for MarkItDown are not set.")
        logging.error(f"Required: {', '.join(required_vars)}")
        return None

    try:
        # Note: We are using the 'azure_openai' client class which is assumed
        # to be supported by the version of markitdown we are using.
        return MarkItDown(
            docintel_endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
            docintel_key=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY"),
            llm_client_class="azure_openai",
            llm_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            llm_key=os.getenv("AZURE_OPENAI_KEY"),
            llm_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            llm_prompt=LLM_PROMPT
        )
    except Exception as e:
        logging.error(f"Failed to initialize MarkItDown client: {e}")
        return None

def process_single_markdown_file(md_client: MarkItDown, md_path: str, output_dir: str):
    """
    Orchestrates the final processing for a single Markdown file.
    """
    base_filename = os.path.splitext(os.path.basename(md_path))[0]
    final_output_path = os.path.join(output_dir, f"{base_filename}.md")

    if os.path.exists(final_output_path):
        logging.info(f"Skipping '{base_filename}', final output already exists.")
        return

    logging.info(f"--- Processing document: {base_filename} ---")

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content_from_stage2 = f.read()

        # Pass the rich text content from Stage 2 directly to the convert method.
        # This leverages our pre-processing work.
        result = md_client.convert(content_from_stage2)

        with open(final_output_path, 'w', encoding='utf-8') as f:
            f.write(result.text_content)

        logging.info(f"Successfully synthesized and saved final document to '{final_output_path}'")

    except Exception as e:
        logging.error(f"FATAL ERROR processing {base_filename} in Stage 3: {e}", exc_info=True)

def main(args):
    """
    Main function to find and process Stage 2 markdown files.
    """
    md_client = initialize_markitdown_client()
    if not md_client:
        logging.error("Halting pipeline due to MarkItDown client initialization failure.")
        return

    os.makedirs(args.output_dir, exist_ok=True)

    source_files = [f for f in os.listdir(args.source_dir) if f.lower().endswith(".md")]

    if not source_files:
        logging.warning(f"No Markdown files found in source directory '{args.source_dir}'.")
        return

    logging.info(f"Found {len(source_files)} Markdown document(s) for Stage 3 processing.")
    for md_filename in source_files:
        md_path = os.path.join(args.source_dir, md_filename)
        process_single_markdown_file(md_client, md_path, args.output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 3: Final Document Synthesis with MarkItDown.")
    parser.add_argument("--source-dir", required=True, help="Directory containing Stage 2 processed Markdown files.")
    parser.add_argument("--output-dir", required=True, help="Directory to save the final synthesized documents.")

    args = parser.parse_args()
    main(args)


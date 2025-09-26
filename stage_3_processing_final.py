# stage_3_processing.py
#
# This script performs the final stage of the document processing pipeline.
# It uses the 'markitdown' library to synthesize the cleaned Markdown and
# image analyses from Stage 2 into a final, publication-ready document.
# It also generates quantitative quality reports for each output file.

import os
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# Third-party imports
from dotenv import load_dotenv
from markitdown import MarkItDown, ConvertResult
from tenacity import retry, stop_after_attempt, wait_exponential

# --- Load Environment Variables ---
# Allows the script to be run standalone for testing. The master script
# will set these variables in the environment directly.
load_dotenv()

# --- Configuration Constants ---
PROCESSING_LOG_FILE = "_stage3_processing.json"
QUALITY_REPORT_FILE_SUFFIX = "_quality_report.json"

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- LLM Prompt for Final Synthesis ---
LLM_PROMPT = """You are an expert technical writer and editor with deep knowledge of classic Apple computer systems, including the Apple II series and classic Macintosh hardware and software (System 6/7).

You will be given a Markdown document that has been pre-processed. This document contains:
1.  Text extracted via OCR from a vintage technical manual or book, which has already undergone a preliminary cleanup.
2.  A dedicated section at the end titled '## Extracted Image Analysis' which contains structured descriptions of all images, diagrams, and screenshots from the original document.

Your task is to perform a final, definitive synthesis to create a comprehensive, clean, and publication-ready technical document.

Your requirements are:
- **Integrate Content:** Seamlessly weave the image descriptions from the 'Extracted Image Analysis' section into the main body of the text where they are contextually relevant. For example, if the text mentions "Figure 2A", find the analysis for that image and insert it as a descriptive blockquote or figure caption immediately following the reference.
- **Synthesize, Don't Just Copy:** Use the image descriptions to enrich the main text. The descriptions are high-quality; treat them as authoritative.
- **Remove Redundancy:** After integrating the image descriptions, REMOVE the entire '## Extracted Image Analysis' section from the end of the document.
- **Format for Clarity:** Ensure the final document has a clear hierarchical structure using appropriate Markdown headings (`#`, `##`, `###`).
- **Correct and Format:** Fix any remaining OCR errors, format tables using proper Markdown syntax, and ensure code blocks are correctly identified with language specifiers (e.g., ```assembly, ```c, ```pascal).
- **Preserve Accuracy:** Maintain all technical specifications, historical context, and original terminology with absolute fidelity.
- **Final Output:** Your final output must be only the complete, cleaned, and synthesized Markdown document. Do not include any commentary, notes, or explanations about your process.
"""

# --- Core Functions ---

def initialize_markitdown_client() -> Optional[MarkItDown]:
    """Initializes and validates the MarkItDown client from environment variables."""
    required_vars = [
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "AZURE_DOCUMENT_INTELLIGENCE_KEY",
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY", "AZURE_OPENAI_DEPLOYMENT_NAME"
    ]
    if not all(os.getenv(var) for var in required_vars):
        logging.error("One or more required Azure environment variables for MarkItDown are not set.")
        logging.error(f"Required: {', '.join(required_vars)}")
        return None
    try:
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

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def convert_with_retry(md_client: MarkItDown, content: str) -> ConvertResult:
    """Invokes the MarkItDown convert method with a retry strategy."""
    logging.debug("Invoking MarkItDown.convert...")
    return md_client.convert(content)

def analyze_markdown_quality(content: str) -> Dict[str, Any]:
    """Analyzes the quality and structure of the final Markdown content."""
    lines = content.splitlines()
    metrics = {
        "total_lines": len(lines),
        "total_characters": len(content),
        "header_count": sum(1 for line in lines if line.strip().startswith("#")),
        "code_block_count": content.count("```") // 2,
        "table_row_count": sum(1 for line in lines if "|" in line and line.strip().startswith("|")),
        "list_item_count": sum(1 for line in lines if line.strip().startswith(("- ", "* ", "+ ")) or (line.strip() and line.strip()[0].isdigit() and ". " in line[:5])),
        "image_reference_count": content.count("!["),
    }
    return metrics

def process_single_document(md_client: MarkItDown, md_path: str, output_dir: str) -> Dict[str, Any]:
    """Orchestrates the final processing and quality analysis for a single file."""
    base_filename = os.path.splitext(os.path.basename(md_path))[0]
    final_output_path = os.path.join(output_dir, f"{base_filename}.md")
    stats = {"document": base_filename, "status": "skipped", "final_size_kb": 0}

    if os.path.exists(final_output_path):
        logging.info(f"Skipping '{base_filename}', final output already exists.")
        return stats

    logging.info(f"--- Processing document: {base_filename} ---")
    stats["status"] = "processing"

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content_from_stage2 = f.read()

        result = convert_with_retry(md_client, content_from_stage2)
        final_content = result.text_content

        with open(final_output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        final_size_kb = os.path.getsize(final_output_path) / 1024
        stats["final_size_kb"] = round(final_size_kb, 2)
        logging.info(f"Successfully synthesized and saved final document to '{final_output_path}' ({final_size_kb:.2f} KB)")

        # Generate and save quality report
        quality_metrics = analyze_markdown_quality(final_content)
        report_path = os.path.join(output_dir, f"{base_filename}{QUALITY_REPORT_FILE_SUFFIX}")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(quality_metrics, f, indent=2)
        logging.info(f"Saved quality report to '{report_path}'")

        stats["status"] = "success"
        stats["quality_metrics"] = quality_metrics
        return stats

    except Exception as e:
        logging.error(f"FATAL ERROR processing {base_filename} in Stage 3: {e}", exc_info=True)
        stats["status"] = "failed"
        stats["error"] = str(e)
        return stats

def main(args):
    """Main function to find and process Stage 2 markdown files."""
    md_client = initialize_markitdown_client()
    if not md_client:
        logging.error("Halting pipeline due to MarkItDown client initialization failure.")
        return

    os.makedirs(args.output_dir, exist_ok=True)
    source_files = [f for f in os.listdir(args.source_dir) if f.lower().endswith(".md")]
    logging.info(f"Found {len(source_files)} Markdown document(s) for Stage 3 processing.")

    overall_stats = {
        "start_time": datetime.now().isoformat(),
        "total_files": len(source_files),
        "successful": 0, "failed": 0, "skipped": 0,
        "processing_details": []
    }

    for md_filename in source_files:
        md_path = os.path.join(args.source_dir, md_filename)
        stats = process_single_document(md_client, md_path, args.output_dir)
        overall_stats["processing_details"].append(stats)
        if stats["status"] == "success":
            overall_stats["successful"] += 1
        elif stats["status"] == "failed":
            overall_stats["failed"] += 1
        else: # skipped
            overall_stats["skipped"] += 1

    overall_stats["end_time"] = datetime.now().isoformat()
    log_path = os.path.join(args.output_dir, PROCESSING_LOG_FILE)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(overall_stats, f, indent=2)

    logging.info("--- Stage 3 Complete: Summary ---")
    logging.info(f"  Files processed: {overall_stats['successful']}/{overall_stats['total_files']}")
    logging.info(f"  Files skipped:   {overall_stats['skipped']}")
    logging.info(f"  Files failed:    {overall_stats['failed']}")
    logging.info(f"  Detailed log saved to: {log_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 3: Final Document Synthesis with MarkItDown.")
    parser.add_argument("--source-dir", required=True, help="Directory containing Stage 2 processed Markdown files.")
    parser.add_argument("--output-dir", required=True, help="Directory to save the final synthesized documents.")
    args = parser.parse_args()
    main(args)

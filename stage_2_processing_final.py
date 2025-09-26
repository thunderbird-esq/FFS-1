# stage_2_processing.py
#
# This script performs the second stage of the document processing pipeline.
# It uses Azure OpenAI's GPT-4o model for two tasks:
# 1. Vision Analysis: Analyzes extracted images to create technical descriptions.
# 2. Text Cleanup: Refines the OCR'd Markdown text from Stage 1.
# It is designed to be robust, cost-effective, and configurable.

import os
import base64
import json
import logging
import argparse
import time
from typing import Dict, List, Optional, Any

# Third-party imports
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage, AIMessage
from tenacity import retry, stop_after_attempt, wait_exponential

# --- Load Environment Variables ---
# Allows the script to be run standalone for testing. The master script
# will set these variables in the environment directly.
load_dotenv()

# --- Configuration Constants ---
# These can be adjusted to tune performance and cost.
API_RATE_LIMIT_DELAY = 1.0  # Seconds to wait between API calls to prevent rate limiting
IMAGE_ANALYSIS_MANIFEST = "_manifest.json"
PROCESSING_LOG_FILE = "_stage2_processing.json"

# Cost per 1M input tokens for gpt-4o on Azure (as of late 2024, check for updates)
# Prices are illustrative.
COST_PER_IMAGE = 0.00765  # A high-res image is a fixed cost
COST_PER_1K_INPUT_TOKENS = 0.005
COST_PER_1K_OUTPUT_TOKENS = 0.015


# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- LLM Prompts ---
IMAGE_SYSTEM_PROMPT = """You are a world-class expert in analyzing technical documentation for vintage computers, specifically the Apple II and classic Macintosh series (System 6/7). Your task is to analyze an image from this context and return a structured JSON object.

The image could be one of the following:
- A screenshot of a GUI (Graphical User Interface)
- A hardware schematic or block diagram
- A code snippet presented as an image
- A chart, graph, or table
- A photograph of hardware components

Your response MUST be a single, valid JSON object with the following schema:
{
  "category": "string",
  "description": "string",
  "entities": ["string"]
}

- "category": Classify the image. Must be one of: "Screenshot", "Diagram", "Code Snippet", "Chart", "Table", "Photograph", "Illustration", "Other".
- "description": A detailed, technically accurate paragraph describing the image's content and purpose. If it's a screenshot, describe the UI elements and what they do. If it's a diagram, explain what it illustrates.
- "entities": A list of key technical terms, components, or specific values visible in the image (e.g., "6502 Assembly", "INIT resource", "VBL interrupt", "ResEdit", "Control Panel").

Do not include any text or formatting outside of the single JSON object."""

TEXT_CLEANUP_SYSTEM_PROMPT = """You are an expert technical editor specializing in vintage Apple computer documentation. Your task is to clean up a chunk of Markdown text that was extracted via OCR.

Your requirements are:
- Correct obvious OCR errors (e.g., '1' for 'l', 'O' for '0', mis-joined words).
- Ensure code blocks are correctly formatted with language specifiers (```assembly, ```c, ```pascal, or ```).
- Fix any broken Markdown table syntax.
- Remove any lingering page numbers, headers, or footers that are mixed in with the main content.
- Maintain the original document structure (headings, lists, etc.) perfectly.
- Do not add any new content, commentary, or explanations.
- Your output must be only the cleaned Markdown text.
"""

# --- Core Functions ---

def initialize_llm() -> Optional[AzureChatOpenAI]:
    """Initializes and validates the AzureChatOpenAI client from environment variables."""
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "OPENAI_API_VERSION"
    ]
    if not all(os.getenv(var) for var in required_vars):
        logging.error("One or more required Azure OpenAI environment variables are not set.")
        logging.error(f"Required: {', '.join(required_vars)}")
        return None
    try:
        return AzureChatOpenAI(
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
            api_version=os.environ["OPENAI_API_VERSION"],
            temperature=0,
            max_retries=0 # We handle retries with Tenacity
        )
    except Exception as e:
        logging.error(f"Failed to initialize AzureChatOpenAI client: {e}")
        return None

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def invoke_llm_with_retry(llm: AzureChatOpenAI, messages: List[SystemMessage | HumanMessage]) -> AIMessage:
    """Invokes the LLM with an exponential backoff retry strategy."""
    logging.debug(f"Invoking LLM with {len(messages)} messages.")
    return llm.invoke(messages)

def encode_image(image_path: str) -> Optional[str]:
    """Encodes an image file to a base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logging.warning(f"Could not encode image {image_path}: {e}")
        return None

def analyze_single_image(llm: AzureChatOpenAI, image_path: str) -> Optional[Dict[str, Any]]:
    """Analyzes a single image and returns a structured dictionary."""
    logging.info(f"Analyzing image: {os.path.basename(image_path)}")
    base64_image = encode_image(image_path)
    if not base64_image:
        return None

    human_message = HumanMessage(
        content=[
            {"type": "text", "text": "Analyze this image and return the JSON object as specified."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
        ]
    )
    messages = [SystemMessage(content=IMAGE_SYSTEM_PROMPT), human_message]

    try:
        time.sleep(API_RATE_LIMIT_DELAY)
        response = invoke_llm_with_retry(llm, messages)
        # Clean the response content to ensure it's a valid JSON string
        json_string = response.content.strip().replace("```json", "").replace("```", "").strip()
        analysis = json.loads(json_string)
        return analysis
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from LLM response for {image_path}. Error: {e}")
        logging.debug(f"Raw LLM response: {response.content}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during image analysis for {image_path}: {e}")
        return None

def cleanup_text_chunk(llm: AzureChatOpenAI, text_chunk: str) -> str:
    """Cleans a single chunk of Markdown text."""
    if not text_chunk.strip():
        return ""
    messages = [
        SystemMessage(content=TEXT_CLEANUP_SYSTEM_PROMPT),
        HumanMessage(content=text_chunk)
    ]
    try:
        time.sleep(API_RATE_LIMIT_DELAY)
        response = invoke_llm_with_retry(llm, messages)
        return response.content
    except Exception as e:
        logging.error(f"Failed to clean up text chunk: {e}")
        return text_chunk # Return original chunk on failure

def process_single_document(llm: AzureChatOpenAI, md_path: str, asset_dir: str, output_dir: str) -> Dict[str, Any]:
    """Orchestrates the full Stage 2 processing for a single document."""
    base_filename = os.path.splitext(os.path.basename(md_path))[0]
    final_md_path = os.path.join(output_dir, f"{base_filename}.md")
    stats = {"document": base_filename, "status": "skipped", "images_analyzed": 0, "api_calls": 0}

    if os.path.exists(final_md_path):
        logging.info(f"Skipping '{base_filename}', final version already exists.")
        return stats

    logging.info(f"--- Processing document: {base_filename} ---")
    stats["status"] = "processing"

    # --- 1. Image Analysis ---
    manifest_path = os.path.join(asset_dir, IMAGE_ANALYSIS_MANIFEST)
    manifest_data = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

    image_files = [f for f in os.listdir(asset_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    for image_file in image_files:
        if image_file not in manifest_data:
            image_path = os.path.join(asset_dir, image_file)
            analysis = analyze_single_image(llm, image_path)
            if analysis:
                manifest_data[image_file] = analysis
                stats["images_analyzed"] += 1
                stats["api_calls"] += 1
                # Save manifest after each successful analysis for resilience
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, indent=2)

    # --- 2. Text Cleanup and Enrichment ---
    with open(md_path, "r", encoding="utf-8") as f:
        original_content = f.read()

    chunks = original_content.split("\n## ")
    processed_chunks = []
    # Process content before the first chapter
    if chunks[0].strip():
        logging.info(f"Cleaning up intro section for {base_filename}...")
        processed_chunks.append(cleanup_text_chunk(llm, chunks[0]))
        stats["api_calls"] += 1
    # Process each chapter
    for i, chunk in enumerate(chunks[1:]):
        logging.info(f"Cleaning up chunk {i+1}/{len(chunks)-1} for {base_filename}...")
        processed_chunks.append("## " + cleanup_text_chunk(llm, "## " + chunk))
        stats["api_calls"] += 1

    cleaned_content = "\n\n".join(processed_chunks)

    # --- 3. Append Image Analysis Section ---
    if manifest_data:
        analysis_section = ["\n\n---\n\n## Extracted Image Analysis\n\n"]
        for filename, data in sorted(manifest_data.items()):
            analysis_section.append(f"### Image: `{filename}`\n")
            analysis_section.append(f"- **Category:** {data.get('category', 'N/A')}\n")
            analysis_section.append(f"- **Key Entities:** {', '.join(data.get('entities', []))}\n")
            analysis_section.append(f"> {data.get('description', 'No description available.')}\n\n")
        cleaned_content += "".join(analysis_section)

    # --- 4. Save Final Output ---
    with open(final_md_path, "w", encoding="utf-8") as f:
        f.write(cleaned_content)
    
    logging.info(f"Successfully saved final version for '{base_filename}'.")
    stats["status"] = "success"
    return stats


def main(args):
    """Main function to find and process markdown files."""
    llm = initialize_llm()
    if not llm:
        logging.error("Halting pipeline due to LLM initialization failure.")
        return

    os.makedirs(args.output_dir, exist_ok=True)

    md_files = [f for f in os.listdir(args.source_md_dir) if f.lower().endswith(".md")]
    logging.info(f"Found {len(md_files)} Markdown document(s) for Stage 2 processing.")

    overall_stats = {
        "start_time": datetime.now().isoformat(),
        "total_files": len(md_files),
        "successful": 0, "failed": 0, "skipped": 0,
        "total_images_analyzed": 0, "total_api_calls": 0,
        "processing_details": []
    }

    for md_filename in md_files:
        try:
            md_path = os.path.join(args.source_md_dir, md_filename)
            base_name = os.path.splitext(md_filename)[0]
            doc_asset_dir = os.path.join(args.asset_dir, base_name)
            
            if not os.path.isdir(doc_asset_dir):
                logging.warning(f"Asset directory not found for {base_name}, skipping.")
                stats = {"document": base_name, "status": "skipped", "reason": "Missing asset directory"}
                overall_stats["skipped"] += 1
            else:
                stats = process_single_document(llm, md_path, doc_asset_dir, args.output_dir)
                if stats["status"] == "success":
                    overall_stats["successful"] += 1
                elif stats["status"] == "skipped":
                    overall_stats["skipped"] += 1
                
            overall_stats["total_images_analyzed"] += stats.get("images_analyzed", 0)
            overall_stats["total_api_calls"] += stats.get("api_calls", 0)
            overall_stats["processing_details"].append(stats)

        except Exception as e:
            logging.error(f"FATAL ERROR on document {md_filename}: {e}", exc_info=True)
            overall_stats["failed"] += 1
            overall_stats["processing_details"].append({"document": md_filename, "status": "failed", "error": str(e)})

    overall_stats["end_time"] = datetime.now().isoformat()
    log_path = os.path.join(args.output_dir, PROCESSING_LOG_FILE)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(overall_stats, f, indent=2)

    # --- Print Final Summary ---
    logging.info("--- Stage 2 Complete: Summary ---")
    logging.info(f"  Files processed: {overall_stats['successful']}/{overall_stats['total_files']}")
    logging.info(f"  Files skipped:   {overall_stats['skipped']}")
    logging.info(f"  Files failed:    {overall_stats['failed']}")
    logging.info(f"  Total images analyzed: {overall_stats['total_images_analyzed']}")
    
    # Simple token estimation for cost
    # A high-res image analysis might be ~1000 tokens input, 200 output.
    # We use a fixed cost per image which is more accurate for vision.
    image_cost = overall_stats['total_images_analyzed'] * COST_PER_IMAGE
    # For text, assume an average of 2000 tokens per call (input+output)
    text_calls = overall_stats['total_api_calls'] - overall_stats['total_images_analyzed']
    text_cost = (text_calls * 2000 / 1000) * (COST_PER_1K_INPUT_TOKENS + COST_PER_1K_OUTPUT_TOKENS) / 2
    
    logging.info(f"  Estimated Cost: ~${image_cost + text_cost:.2f}")
    logging.info(f"  Detailed log saved to: {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stage 2: LLM Vision Analysis and Text Cleanup.")
    parser.add_argument("--source-md-dir", required=True, help="Directory containing markdown files from Stage 1.")
    parser.add_argument("--asset-dir", required=True, help="Root directory containing extracted image assets from Stage 1.")
    parser.add_argument("--output-dir", required=True, help="Directory to save the final, cleaned markdown files.")
    
    args = parser.parse_args()
    main(args)


import os
import base64
import json
import logging
import argparse
from langchain_openai import AzureChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- API Call with Retry Logic ---
@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def invoke_llm_with_retry(llm, messages):
    """Invokes the LLM with an exponential backoff retry strategy."""
    logging.debug("Invoking LLM...")
    return llm.invoke(messages)

# --- Core Functions ---
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(llm, image_path):
    """Analyzes a single image and returns a structured JSON string."""
    logging.info(f"Analyzing image: {os.path.basename(image_path)}")
    base64_image = encode_image(image_path)
    # ... (same message structure as before) ...
    messages = [ ... ] 
    response = invoke_llm_with_retry(llm, messages)
    return json.loads(response.content)

def cleanup_text(llm, content):
    """Cleans a chunk of text using the LLM."""
    # ... (same logic as before, just in a function) ...
    # ... Uses invoke_llm_with_retry ...
    return cleaned_content

def process_document(llm, md_path, asset_dir, output_dir):
    """Processes a single document: analyzes images and cleans text."""
    base_filename = os.path.splitext(os.path.basename(md_path))[0]
    final_md_path = os.path.join(output_dir, f"{base_filename}.md")

    if os.path.exists(final_md_path):
        logging.info(f"Skipping '{base_filename}', final version already exists.")
        return

    logging.info(f"Processing document: {base_filename}")
    
    # ... (image analysis loop calling analyze_image) ...
    # ... (text cleanup loop with chunking calling cleanup_text) ...

    with open(final_md_path, "w", encoding="utf-8") as f:
        f.write(final_processed_content)
    logging.info(f"Successfully saved final version for '{base_filename}'.")

# --- Argument Parsing and Main Execution ---
def parse_arguments():
    parser = argparse.ArgumentParser(description="Stage 2: LLM Vision Analysis and Text Cleanup")
    parser.add_argument("--source-md-dir", required=True, help="Directory containing markdown files from Stage 1.")
    parser.add_argument("--asset-dir", required=True, help="Root directory containing extracted image assets from Stage 1.")
    parser.add_argument("--output-dir", required=True, help="Directory to save the final, cleaned markdown files.")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Initialize LLM from environment variables
    # (assuming AZURE_OPENAI_... vars are loaded by the shell script)
    llm = AzureChatOpenAI(...)

    os.makedirs(args.output_dir, exist_ok=True)

    for md_filename in os.listdir(args.source_md_dir):
        if md_filename.endswith(".md"):
            md_path = os.path.join(args.source_md_dir, md_filename)
            base_name = os.path.splitext(md_filename)[0]
            doc_asset_dir = os.path.join(args.asset_dir, base_name)
            process_document(llm, md_path, doc_asset_dir, args.output_dir)

if __name__ == "__main__":
    main()

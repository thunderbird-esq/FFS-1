# stage_3_processing_enhanced.py

import os
import glob
import sys
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional
from markitdown import MarkItDown

# Configuration
INPUT_FOLDER = 'final_markdown'
OUTPUT_FOLDER = 'markitdown_output'
PROCESSING_LOG_FILE = '_stage3_processing.json'
QUALITY_REPORT_FILE = '_quality_report.json'

# Specialized prompt for vintage computer documentation
LLM_PROMPT = """You are an expert in classic Apple computer systems, vintage computing, and technical documentation.
You have deep knowledge of System 6/7, classic Macintosh, Apple II series, and historical computing contexts.

Analyze the provided Markdown content which includes:
1. OCR-extracted text from scanned documentation
2. Detailed technical descriptions of images, diagrams, and screenshots
3. Potential OCR errors and formatting issues

Your task is to synthesize all this information into a comprehensive, publication-ready Markdown document.

Requirements:
- Preserve ALL technical information, specifications, and details
- Create clear hierarchical structure with appropriate headings
- Format tables using proper Markdown table syntax
- Identify and properly format code blocks with language specification
- Integrate image descriptions seamlessly into the narrative
- Correct obvious OCR errors while preserving technical accuracy
- Maintain historical context and terminology
- Ensure cross-references and navigation are clear

Output a clean, structured, technically accurate document suitable for:
- Technical reference
- Historical preservation
- Educational purposes
- Digital archival

Focus on accuracy over brevity - include all relevant technical details."""

def validate_environment() -> Dict[str, bool]:
    """
    Validate Azure environment variables and dependencies.
    Returns validation status dictionary.
    """
    validation = {
        "azure_di_endpoint": False,
        "azure_openai_endpoint": False,
        "input_folder_exists": False,
        "input_files_present": False,
        "output_folder_writable": False
    }
    
    # Check Azure Document Intelligence endpoint
    docintel_endpoint = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    if docintel_endpoint and docintel_endpoint.startswith("https://"):
        validation["azure_di_endpoint"] = True
    
    # Check Azure OpenAI endpoint
    openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if openai_endpoint and openai_endpoint.startswith("https://"):
        validation["azure_openai_endpoint"] = True
    
    # Check input folder
    if os.path.exists(INPUT_FOLDER):
        validation["input_folder_exists"] = True
        md_files = glob.glob(os.path.join(INPUT_FOLDER, '*.md'))
        if md_files:
            validation["input_files_present"] = True
    
    # Check output folder writability
    try:
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        test_file = os.path.join(OUTPUT_FOLDER, '.test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        validation["output_folder_writable"] = True
    except:
        pass
    
    return validation

def analyze_markdown_quality(content: str) -> Dict:
    """
    Analyze the quality and structure of markdown content.
    Returns quality metrics dictionary.
    """
    lines = content.splitlines()
    
    metrics = {
        "total_lines": len(lines),
        "total_characters": len(content),
        "headers": {
            "h1": sum(1 for line in lines if line.startswith("# ")),
            "h2": sum(1 for line in lines if line.startswith("## ")),
            "h3": sum(1 for line in lines if line.startswith("### ")),
            "total": 0
        },
        "code_blocks": content.count("```"),
        "tables": sum(1 for line in lines if "|" in line and line.count("|") >= 3),
        "lists": {
            "bullet": sum(1 for line in lines if line.strip().startswith(("- ", "* ", "+ "))),
            "numbered": sum(1 for line in lines if line.strip() and line.strip()[0].isdigit() and ". " in line[:5])
        },
        "images": content.count("!["),
        "links": content.count("]("),
        "blockquotes": sum(1 for line in lines if line.strip().startswith(">")),
        "empty_lines": sum(1 for line in lines if not line.strip()),
        "metadata_present": content.startswith("---")
    
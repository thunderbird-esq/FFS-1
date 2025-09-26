import os
import glob
from markitdown import MarkItDown

# --- CONFIGURATION ---
# Define the folder containing your PDFs and where to save the output.
# The '.' means the current directory.
INPUT_FOLDER = '.'
OUTPUT_FOLDER = 'markdown_output'

# Define the prompt for the image analysis model.
LLM_PROMPT = """Analyze the provided image, which may be a diagram, chart, or screenshot 
from a computer science context. Your analysis must be returned as a Markdown blockquote. 
Inside the blockquote, provide a concise, one-sentence summary of the image's purpose. 
Following the summary, create a bulleted list detailing key components, data points, or 
relationships shown in the image. The tone should be technical and precise, suitable for an 
engineering document."""

# --- SCRIPT LOGIC ---
def main():
    docintel_endpoint = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

    if not docintel_endpoint or not openai_endpoint:
        print("ERROR: Azure environment variables are not set.")
        print("Please run the 'export' commands for your endpoints and keys before running this script.")
        return

    md = MarkItDown(
        docintel_endpoint=docintel_endpoint,
        llm_client_class="azure_openai",
        llm_endpoint=openai_endpoint,
        llm_model="gpt-4o",
        llm_prompt=LLM_PROMPT
    )

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"Output will be saved to '{OUTPUT_FOLDER}' directory.")

    pdf_files = glob.glob(os.path.join(INPUT_FOLDER, '*.pdf'))
    if not pdf_files:
        print(f"No PDF files found in '{INPUT_FOLDER}'.")
        return

    print(f"Found {len(pdf_files)} PDF(s) to process. Starting conversion...")

    for pdf_path in pdf_files:
        try:
            print(f"Processing '{os.path.basename(pdf_path)}'...")
            
            # This is where the conversion happens
            result = md.convert(pdf_path)
            
            # Create the output filename
            base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = os.path.join(OUTPUT_FOLDER, f"{base_filename}.md")
            
            # Save the result to a new Markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.text_content)
                
            print(f" -> Successfully converted and saved to '{output_path}'")

        except Exception as e:
            print(f" -> FAILED to convert '{os.path.basename(pdf_path)}'. Error: {e}")

    print("\nConversion process complete.")

if __name__ == "__main__":
    main()

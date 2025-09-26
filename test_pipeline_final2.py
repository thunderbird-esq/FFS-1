# test_pipeline.py
#
# This script contains the automated test suite for the document processing pipeline.
# It uses the pytest framework to run unit, integration, and validation tests
# as defined in the TESTING.md specification.

import os
import subprocess
import json
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# --- Test Setup and Fixtures ---

# We must be able to import all our project scripts to test them
import create_test_data
import stage_1_processing
import stage_2_processing
import stage_3_processing

@pytest.fixture(scope="module")
def pipeline_environment():
    """
    A pytest fixture that creates a temporary, isolated environment for testing.
    It generates a fresh set of test data before tests run and cleans up after.
    """
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    # chdir into the temp dir so all file operations are isolated
    os.chdir(temp_dir)
    
    print(f"\n--- Setting up test environment in: {temp_dir} ---")
    create_test_data.TEST_DATA_DIR = "test_data"
    
    # Suppress print statements from the generator for cleaner test output
    with patch('builtins.print'):
        creators = {
            "text_only.pdf": create_test_data.create_text_only_pdf,
            "image_heavy.pdf": create_test_data.create_image_heavy_pdf,
            "mixed_content.pdf": create_test_data.create_mixed_content_pdf,
            "difficult_scan.pdf": create_test_data.create_difficult_scan_pdf,
            "corrupted.pdf": create_test_data.create_corrupted_pdf,
        }
        os.makedirs(create_test_data.TEST_DATA_DIR, exist_ok=True)
        for filename, function in creators.items():
            filepath = os.path.join(create_test_data.TEST_DATA_DIR, filename)
            function(filepath)
            
    print("--- Test environment setup complete ---")

    # The 'yield' keyword passes control to the tests
    yield temp_dir

    # Teardown: Clean up the temporary directory after tests are done
    os.chdir(original_cwd)
    print(f"\n--- Tearing down test environment: {temp_dir} ---")
    shutil.rmtree(temp_dir)


# --- Test Cases ---

class TestStage1Processing:
    """Tests for the stage_1_processing.py script."""

    def test_stage1_integration_and_outputs(self, pipeline_environment):
        """
        Integration Test: Runs the full Stage 1 script on the test data
        and validates that all expected output artifacts are created correctly.
        """
        source_pdf_dir = "test_data"
        md_output_dir = "stage1_md_out"
        asset_output_dir = "stage1_asset_out"
        
        # Find the real path to the script to run it as a subprocess from any location
        script_path = os.path.join(os.path.dirname(__file__), "stage_1_processing.py")

        # Execute Stage 1 as a subprocess
        result = subprocess.run([
            "python3", script_path,
            "--pdf-dir", source_pdf_dir,
            "--md-dir", md_output_dir,
            "--asset-dir", asset_output_dir
        ], capture_output=True, text=True, check=False)

        assert result.returncode == 0, f"Stage 1 script failed with stderr:\n{result.stderr}"

        # --- Validate the outputs ---
        # 1. Check a successful file's outputs
        expected_md_file = os.path.join(md_output_dir, "mixed_content.md")
        assert os.path.exists(expected_md_file), "Markdown output for mixed_content.pdf was not created."
        assert os.path.getsize(expected_md_file) > 100, "Markdown output for mixed_content.pdf is empty."

        expected_asset_dir = os.path.join(asset_output_dir, "mixed_content")
        assert os.path.isdir(expected_asset_dir), "Asset directory for mixed_content.pdf was not created."
        assert len(os.listdir(expected_asset_dir)) == 1, "Incorrect number of images extracted for mixed_content.pdf."

        # 2. Check the summary log for correctness
        log_file = os.path.join(md_output_dir, "_stage1_processing.json")
        assert os.path.exists(log_file), "Stage 1 summary log was not created."
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert log_data["total_files"] == 5, "Log reports incorrect number of total files."
        assert log_data["successful"] == 4, "Log reports incorrect number of successful files."
        assert log_data["failed"] == 1, "Log reports incorrect number of failed files."
        
        # 3. Verify fallback OCR was triggered for the difficult scan
        fallback_doc = next((item for item in log_data["processing_details"] if item["document"] == "difficult_scan"), None)
        assert fallback_doc is not None, "Difficult scan document not found in log details."
        assert fallback_doc["ocr_method"] == "fallback_tesseract", "Fallback OCR was not triggered for difficult_scan.pdf."

        # 4. Verify corrupted file was handled gracefully
        failed_doc = next((item for item in log_data["processing_details"] if item["status"] == "failed"), None)
        assert failed_doc is not None, "Failed document not found in log details."
        assert failed_doc["document"] == "corrupted", "corrupted.pdf was not logged as a failure."


class TestStage2Logic:
    """Unit tests for the logic within stage_2_processing.py."""

    @patch('stage_2_processing.AzureChatOpenAI')
    def test_image_analysis_with_mock_api(self, MockAzureChatOpenAI, pipeline_environment):
        """
        Unit Test: Mocks the Azure API to test the image analysis function's
        internal logic without making a real network request.
        """
        # --- Setup Mock ---
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "category": "Diagram",
            "description": "A mock description.",
            "entities": ["Mock Entity"]
        })
        mock_llm_instance = MockAzureChatOpenAI.return_value
        mock_llm_instance.invoke.return_value = mock_response

        # --- Run function under test ---
        # The function needs a real image file to encode, so we create a dummy one
        dummy_image_path = os.path.join("test_data", "dummy_image_for_test.png")
        from PIL import Image
        Image.new('RGB', (10, 10)).save(dummy_image_path) 

        result = stage_2_processing.analyze_single_image(mock_llm_instance, dummy_image_path)

        # --- Assertions ---
        mock_llm_instance.invoke.assert_called_once()
        assert result is not None
        assert result["category"] == "Diagram"
        assert result["entities"] == ["Mock Entity"]


class TestStage3Logic:
    """Unit tests for the logic within stage_3_processing.py."""

    @patch('stage_3_processing.MarkItDown')
    def test_synthesis_with_mock_api(self, MockMarkItDown, pipeline_environment):
        """
        Unit Test: Mocks the MarkItDown client to test the main processing
        logic of Stage 3 without making a real network call.
        """
        # --- Setup Mock ---
        mock_result = MagicMock()
        mock_result.text_content = "# Mock Synthesized Document"
        mock_md_client = MockMarkItDown.return_value
        mock_md_client.convert.return_value = mock_result

        # --- Run function under test ---
        # Create a dummy input file for the function to read
        dummy_md_path = os.path.join("dummy_stage2_output.md")
        with open(dummy_md_path, "w") as f:
            f.write("## Test Content")
        
        output_dir = "stage3_test_out"
        os.makedirs(output_dir, exist_ok=True)

        stage_3_processing.process_single_document(mock_md_client, dummy_md_path, output_dir)

        # --- Assertions ---
        mock_md_client.convert.assert_called_once_with("## Test Content")
        
        final_output_path = os.path.join(output_dir, "dummy_stage2_output.md")
        assert os.path.exists(final_output_path)
        with open(final_output_path, 'r') as f:
            content = f.read()
        assert content == "# Mock Synthesized Document"

    def test_quality_analysis_logic(self):
        """
        Unit Test: Validates the quantitative quality analysis function
        to ensure it correctly calculates metrics from a markdown string.
        """
        test_markdown = """
# Header 1
Some text.
## Header 2
- List item 1
- List item 2

```python
print("Hello")



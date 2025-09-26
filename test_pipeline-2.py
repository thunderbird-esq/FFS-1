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

    yield temp_dir

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
        
        # Find the real path to the script to run it as a subprocess
        script_path = os.path.join(os.path.dirname(__file__), "stage_1_processing.py")

        result = subprocess.run([
            "python3", script_path,
            "--pdf-dir", source_pdf_dir,
            "--md-dir", md_output_dir,
            "--asset-dir", asset_output_dir
        ], capture_output=True, text=True, check=False)

        assert result.returncode == 0, f"Stage 1 script failed with stderr:\n{result.stderr}"

        # --- Validate the outputs ---
        expected_md_file = os.path.join(md_output_dir, "mixed_content.md")
        assert os.path.exists(expected_md_file)
        assert os.path.getsize(expected_md_file) > 100

        expected_asset_dir = os.path.join(asset_output_dir, "mixed_content")
        assert os.path.isdir(expected_asset_dir)
        assert len(os.listdir(expected_asset_dir)) == 1

        log_file = os.path.join(md_output_dir, "_stage1_processing.json")
        assert os.path.exists(log_file)
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert log_data["total_files"] == 5
        assert log_data["successful"] == 4
        assert log_data["failed"] == 1
        
        # Verify fallback OCR was triggered for the difficult scan
        fallback_doc = next((item for item in log_data["processing_details"] if item["document"] == "difficult_scan"), None)
        assert fallback_doc is not None
        assert fallback_doc["ocr_method"] == "fallback_tesseract"

        # Verify corrupted file was handled
        failed_doc = next((item for item in log_data["processing_details"] if item["status"] == "failed"), None)
        assert failed_doc is not None
        assert failed_doc["document"] == "corrupted"

class TestStage2Logic:
    """Unit tests for the logic within stage_2_processing.py."""

    @patch('stage_2_processing.AzureChatOpenAI')
    def test_image_analysis_with_mock_api(self, MockAzureChatOpenAI, pipeline_environment):
        """
        Unit Test: Mocks the Azure API to test the image analysis function's
        internal logic without making a real network request.
        """
        # Setup Mock
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "category": "Diagram",
            "description": "A mock description.",
            "entities": ["Mock Entity"]
        })
        mock_llm_instance = MockAzureChatOpenAI.return_value
        mock_llm_instance.invoke.return_value = mock_response

        # Create a dummy image file for the function to open
        dummy_image_path = os.path.join("test_data", "dummy_image.png")
        Image.new('RGB', (10, 10)).save(dummy_image_path) 

        # Run function
        result = stage_2_processing.analyze_single_image(mock_llm_instance, dummy_image_path)

        # Assertions
        mock_llm_instance.invoke.assert_called_once()
        assert result is not None
        assert result["category"] == "Diagram"
        assert result["entities"] == ["Mock Entity"]

class TestStage3Logic:
    """Unit tests for the logic within stage_3_processing.py."""
    
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



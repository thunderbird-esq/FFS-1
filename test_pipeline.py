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

# Import the script we will be testing and generating data with
import create_test_data
# We import the scripts to test their functions directly (unit tests)
import stage_2_processing

@pytest.fixture(scope="module")
def pipeline_environment():
    """
    A pytest fixture that creates a temporary, isolated environment for testing.
    It generates a fresh set of test data before tests run and cleans up after.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Temporarily change the current working directory to the temp dir
    # so all scripts run in an isolated space.
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    # Generate the test data inside the temporary directory
    print(f"\n--- Setting up test environment in: {temp_dir} ---")
    create_test_data.TEST_DATA_DIR = "test_data"
    # Suppress print statements from the generator for cleaner test output
    with patch('builtins.print'):
        creators = {
            "text_only.pdf": create_test_data.create_text_only_pdf,
            "image_heavy.pdf": create_test_data.create_image_heavy_pdf,
            "mixed_content.pdf": create_test_data.create_mixed_content_pdf,
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

    def test_stage1_execution_and_outputs(self, pipeline_environment):
        """
        Integration Test: Runs the actual Stage 1 script on a test PDF
        and validates that all expected output artifacts are created correctly.
        """
        # Define paths within the temporary environment
        source_pdf_dir = "test_data"
        md_output_dir = "stage1_md_out"
        asset_output_dir = "stage1_asset_out"
        test_pdf = os.path.join(source_pdf_dir, "mixed_content.pdf")

        # Find the real path to the script to run it as a subprocess
        script_path = os.path.join(os.path.dirname(__file__), "stage_1_processing.py")

        # Execute Stage 1 as a subprocess
        result = subprocess.run([
            "python3", script_path,
            "--pdf-dir", source_pdf_dir,
            "--md-dir", md_output_dir,
            "--asset-dir", asset_output_dir
        ], capture_output=True, text=True)

        # Assert that the script ran successfully (exit code 0)
        assert result.returncode == 0, f"Stage 1 script failed with stderr:\n{result.stderr}"

        # --- Validate the outputs ---
        # 1. Check that the Markdown file was created and is not empty
        expected_md_file = os.path.join(md_output_dir, "mixed_content.md")
        assert os.path.exists(expected_md_file)
        assert os.path.getsize(expected_md_file) > 100 # Check for non-trivial content

        # 2. Check that the asset directory and its contents were created
        expected_asset_dir = os.path.join(asset_output_dir, "mixed_content")
        assert os.path.isdir(expected_asset_dir)
        # The mixed_content.pdf has exactly one image
        assert len(os.listdir(expected_asset_dir)) == 1 

        # 3. Check that the summary log was created and is valid JSON
        log_file = os.path.join(md_output_dir, "_stage1_processing.json")
        assert os.path.exists(log_file)
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        assert log_data["successful"] == 3 # text, image-heavy, mixed
        assert log_data["failed"] == 1 # corrupted.pdf
        assert log_data["total_files"] == 4

    def test_stage1_handles_corrupted_pdf(self, pipeline_environment):
        """
        Negative Test: Verifies that Stage 1 correctly handles a corrupted PDF,
        logs it as a failure, and does not crash the entire run.
        """
        source_pdf_dir = "test_data"
        md_output_dir = "stage1_md_out_corrupt"
        asset_output_dir = "stage1_asset_out_corrupt"
        
        script_path = os.path.join(os.path.dirname(__file__), "stage_1_processing.py")

        result = subprocess.run([
            "python3", script_path,
            "--pdf-dir", source_pdf_dir,
            "--md-dir", md_output_dir,
            "--asset-dir", asset_output_dir
        ], capture_output=True, text=True)
        
        assert result.returncode == 0 # The script itself should not crash

        log_file = os.path.join(md_output_dir, "_stage1_processing.json")
        assert os.path.exists(log_file)
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        # Verify that the corrupted file was logged as a failure
        assert log_data["failed"] == 1
        failed_doc = next((item for item in log_data["processing_details"] if item["status"] == "failed"), None)
        assert failed_doc is not None
        assert failed_doc["document"] == "corrupted"

class TestStage2Logic:
    """Unit tests for the logic within stage_2_processing.py."""

    @patch('stage_2_processing.AzureChatOpenAI')
    def test_stage2_image_analysis_logic(self, MockAzureChatOpenAI, pipeline_environment):
        """
        Unit Test: Mocks the Azure OpenAI API call to test the image analysis
        function's internal logic without making a real network request.
        """
        # --- Setup the Mock ---
        # Create a mock instance of the AI Message response
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "category": "Diagram",
            "description": "A mock description of the sample diagram.",
            "entities": ["Sample", "Diagram"]
        })
        
        # Configure the mock LLM client to return our mock response
        mock_llm_instance = MockAzureChatOpenAI.return_value
        mock_llm_instance.invoke.return_value = mock_response

        # --- Run the function under test ---
        image_path = os.path.join("test_data", "mixed_content_image.png") # Dummy path
        # Create a dummy image file for the function to open
        Image.new('RGB', (10, 10)).save(image_path) 

        # Call the actual function from the Stage 2 script
        result = stage_2_processing.analyze_single_image(mock_llm_instance, image_path)

        # --- Assertions ---
        # Verify that the LLM was called once
        mock_llm_instance.invoke.assert_called_once()
        
        # Verify that the function correctly parsed the mock JSON response
        assert result is not None
        assert result["category"] == "Diagram"
        assert result["description"] == "A mock description of the sample diagram."

Testing and Validation Plan
This document outlines the testing strategy to ensure the correctness, reliability, and quality of the document processing pipeline. All testing will be automated where possible.

1. Testing Philosophy
The pipeline will be validated using a multi-layered testing approach to ensure quality at every level of the system. The core principles are:

Automated: Tests should be scriptable and run automatically.

Repeatable: Tests must produce the same results every time they are run against the same code and data.

Comprehensive: Tests will cover individual components, the integration between components, and the end-to-end workflow.

2. Testing Levels
a. Unit Tests
Purpose: To verify the correctness of individual functions in isolation.

Framework: pytest will be used as the testing framework.

Scope:

Test helper functions (e.g., calculate_file_hash in Stage 1).

Test data transformation logic (e.g., the JSON formatting in Stage 2's image analysis).

Test error handling within functions.

Mocking: All external services, particularly the Azure OpenAI API, must be mocked using libraries like unittest.mock. Unit tests must not make network calls. This ensures they are fast, free to run, and deterministic.

b. Integration Tests
Purpose: To verify the data contracts and interactions between the pipeline stages.

Scope:

Verify that Stage 2 can correctly parse the Markdown and asset directory structure produced by Stage 1.

Verify that Stage 3 can correctly parse the enriched Markdown produced by Stage 2.

Validate the schema of all intermediate JSON logs and manifests (_manifest.json, _stageX_processing.json, etc.).

Execution: These tests will run against a small, static set of pre-generated output from each stage located in the test_data/ directory.

c. End-to-End (E2E) Tests
Purpose: To validate the entire pipeline workflow from a source PDF to the final synthesized Markdown document.

Scope: E2E tests will execute the full run_pipeline.sh script on a small, curated set of test documents.

Validation: A successful E2E test is defined by:

The run_pipeline.sh script completing with an exit code of 0.

The final output artifacts being created in the markitdown_output/ directory.

The _quality_report.json for the output artifact meeting the quantitative quality checks defined in MONITORING.md.

3. Test Data
A dedicated test_data/ directory will be created in the project root. This directory will contain a small, curated set of PDF files designed to test specific scenarios, such as:

text_only.pdf: A document with multiple pages of clean text.

image_heavy.pdf: A document primarily composed of full-page images and diagrams.

mixed_content.pdf: A typical document with text, images, and tables.

complex_layout.pdf: A document with multi-column text or complex formatting to test the primary OCR engine.

difficult_scan.pdf: A low-quality scan designed to trigger the fallback OCR mechanism in Stage 1.

corrupted.pdf: An invalid PDF file to test the pipeline's resilience to file corruption.

4. Test Execution
All automated tests will be executable via a single command from the project root.

# To be implemented
pytest

The E2E tests will be executed by a separate script that manages the test environment and runs the main pipeline.

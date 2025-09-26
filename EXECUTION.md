Execution Plan
This document provides the Standard Operating Procedure (SOP) for executing the 3-stage document processing pipeline.

1. Pre-Execution Checklist
Before initiating the pipeline, ensure the following steps have been completed. The run_pipeline.sh script contains pre-flight checks that will validate most of these items, but manual verification is recommended.

[ ] System Dependencies Installed: Ensure Homebrew, tesseract, poppler, and coreutils are installed on the host machine. The environment_setup_helper.sh script will validate this.

[ ] Source PDFs: Place all PDF files to be processed in the project's root directory.

[ ] Azure Credentials: Ensure all required Azure environment variables are set in the current terminal session or are defined in a .env file in the project root. The required variables are:

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT

AZURE_DOCUMENT_INTELLIGENCE_KEY

AZURE_OPENAI_ENDPOINT

AZURE_OPENAI_KEY

AZURE_OPENAI_DEPLOYMENT_NAME

OPENAI_API_VERSION

2. Pipeline Execution
The entire pipeline is orchestrated by a single master script. This script handles environment setup, validation, and the sequential execution of all three processing stages.

Master Execution Command
To run the entire pipeline from start to finish, execute the following command from the project's root directory:

./run_pipeline.sh

The script is designed to be run from a clean state and is idempotent. It will:

Perform pre-flight checks for system dependencies and configuration.

Call the environment_setup_helper.sh to build and synchronize the Python virtual environment.

Execute Stage 1, Stage 2, and Stage 3 in sequence, with timeouts for each stage.

Perform post-flight checks to validate that output artifacts were created.

Log all informational output, warnings, and errors to timestamped files in the pipeline_logs/ directory.

3. Post-Execution Validation
A successful pipeline run is determined by two factors: the exit code of the master script and the content of the output directories and logs.

Verification Steps
Check Exit Code: A successful run will complete with an exit code of 0. The final line of the terminal output should be a "Pipeline Finished Successfully" message.

Review Logs: Check the main log file in pipeline_logs/ for any warnings. Check the errors.log file; it should be empty.

Inspect Output Directories: Verify that the following directories are not empty:

preprocessed_markdown/ (contains Stage 1 Markdown)

document_assets/ (contains Stage 1 extracted images)

final_markdown/ (contains Stage 2 enriched Markdown)

markitdown_output/ (contains the final synthesized documents from Stage 3)

Review Summary Logs: For a detailed, machine-readable summary of each stage's performance, inspect the JSON log files generated within the output directories:

preprocessed_markdown/_stage1_processing.json

final_markdown/_stage2_processing.json

markitdown_output/_stage3_processing.json

markitdown_output/*_quality_report.json

A successful run is defined by a zero exit code from run_pipeline.sh and the presence of the expected artifacts in the output directories.

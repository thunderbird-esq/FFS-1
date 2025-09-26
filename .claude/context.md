# Project Context: Document Processing Pipeline Reconciliation

## 1. Project Overview

This project's goal is to create a definitive, production-grade, three-stage document processing pipeline. The pipeline converts scanned PDF documents (specifically vintage computer manuals) into high-quality, structured markdown files using local OCR and Azure AI services.

---

## 2. Current State Analysis

The local filesystem contains multiple, conflicting versions of project files due to parallel development efforts. There are redundant scripts, inconsistent documentation, and a lack of a single source of truth.

**The primary objective is to reconcile this chaos.** The AI agent's first mission is to analyze the entire repository and synthesize a single, definitive, and functional codebase that adheres to the established architecture and technical constraints.

---

## 3. Definitive Architecture & Agent Specifications

The target system is a linear, 3-stage pipeline orchestrated by a master Bash script. The specifications for each component are defined in the five agent `.md` files located in the `/agents` directory. These files are the blueprints for the required functionality.

1.  **`ENV_AGENT`**: Defines the environment setup logic. The implementation should be a robust Bash script.
2.  **`OCR_AGENT`**: Defines Stage 1 (Local OCR). The implementation (`stage_1_processing.py`) must perform OCR and asset extraction.
3.  **`VISION_AGENT`**: Defines Stage 2 (Vision Analysis). The implementation (`stage_2_processing.py`) must handle image analysis via Azure OpenAI Vision.
4.  **`SYNTHESIS_AGENT`**: Defines Stage 3 (Document Synthesis). The implementation (`stage_3_processing.py`) must use MarkItDown and Azure Document Intelligence for final processing.
5.  **`PM_AGENT`**: Defines the master orchestrator. The implementation (`run_pipeline.sh`) must execute the three stages sequentially.

---

## 4. Technical Constraints (Non-Negotiable)

* **Operating System:** macOS Catalina 10.15.7 (Darwin Kernel 19.6.0)
* **Python Version:** **3.9.x** is mandatory due to OpenSSL 1.1.1 compatibility on Catalina.
* **Package Limitations:** Packages requiring modern `cmake` or C++ libraries (e.g., `opencv-python`, `easyocr`) **must be avoided**. The definitive list of working packages is found in `ENV_AGENT.md`.

---

## 5. Primary Implementation Reference

The collaborator's files represent the most advanced and robust implementation path. These files should be considered the **primary reference** for synthesizing the final codebase:

* **`run_pipeline_final.sh`**: The best version of the master orchestrator.
* **`environment_setup_helper_best.py`**: The best version of the environment setup script (note the incorrect `.py` extension).
* **`stage_1_processing_final.py`**: The best version of the Stage 1 script.
* **`stage_2_processing_final.py`**: The best version of the Stage 2 script.
* **`stage_3_processing_final.py`**: The best version of the Stage 3 script.
* **`test_pipeline_final2.py`**: The definitive test suite.
* **`create_test_data.py`**: The definitive test data generator.
* **`api_server_2.py`**: A functional API server that should be integrated.

---

## 6. Success Criteria

The project is complete when:
1.  A single, definitive set of scripts (`run_pipeline.sh`, `environment_setup_helper.sh`, `stage_1_processing.py`, etc.) exists.
2.  All redundant and outdated files have been removed.
3.  The pipeline, when initiated by `./run_pipeline.sh`, successfully processes a sample PDF through all three stages.
4.  The automated test suite (`pytest`) runs and all tests pass.
5.  All code adheres to the Core Engineering Principles defined in `CLAUDE.md`.

# VeloBid Autonomous Agent Harness

This document describes the architecture, tools, and context logic for the VeloBid AI Estimator.

## 1. Architecture Overview

The VeloBid Agent is a **Tool-Calling Harness** built on top of the DeepSeek V4 Pro model. It operates as a project-centric autonomous assistant that can research, calculate, and execute bidding workflows.

### Components:
- **Harness (`api/services/agent.py`)**: Manages the tool registry and OpenAI-compatible client communication.
- **Router (`api/routers/agent.py`)**: Orchestrates the multi-step reasoning loop and **streams events via SSE**.
- **Tools**: Modular Python functions that provide the agent with "hands" in the project environment.

## 2. Real-Time Streaming (SSE)

The agent uses **Server-Sent Events (SSE)** to provide an interactive, "Bolt-style" experience. As the agent thinks and acts, it streams events to the frontend:

- `content`: Chunked text delta of the assistant's response.
- `tool_call`: Notifies when a tool execution starts.
- `tool_result`: Provides the output of a completed tool.
- `[DONE]`: Signals the end of the streaming session.

This allows the UI to update in real-time, showing the agent's reasoning process and findings without waiting for the entire loop to finish.

## 3. Project-Centric Context

Unlike a general-purpose chat, the VeloBid agent is always **mounted to a specific project**.

### Context Injection:
When a project is selected in the UI:
1. The agent receives the **Project ID** and **Metadata** (Address, Area, Occupancy, etc.) in its System Prompt.
2. The agent is instructed that its "working directory" maps to `source_packages/{project_id}/`.
3. All research tools (`list_source_documents`, `read_document_text`) are scoped to this directory by default.

## 4. Tool Registry

| Tool | Purpose | Parameters |
|---|---|---|
| `list_source_documents` | Scans the project's source folder for blueprints/specs. | `project_id` |
| `read_document_text` | Extracts text from specific PDFs for analysis. | `file_path`, `max_pages` |
| `inspect_pdf_layout` | Renders PDF pages to PNG and returns a layout QA report. | `file_path`, `max_pages` |
| `update_config` | Modifies the project or trade JSON configurations. | `target_type`, `target_id`, `updates` |
| `calculate_takeoff` | Performs material/labor math based on research findings. | `items` |
| `generate_pdfs` | Triggers the final PDF rendering engine. | `project_id`, `trade`, `package` |
| `search_web` | Fetches external construction costs or standards. | `query` |

## 5. The Reasoning Loop

1. **User Prompt**: "Check the MEP drawings for AHU count and update the budget."
2. **Step 1 (Research)**: Agent calls `list_source_documents`.
3. **Step 2 (Research)**: Agent calls `read_document_text` on `02_MEP_Design.pdf`.
4. **Step 3 (Analysis)**: Agent processes text, finds 5 AHUs, and calls `calculate_takeoff`.
5. **Step 4 (Execution)**: Agent calls `update_config` with the new totals.
6. **Final Response**: "I found 5 AHUs in the MEP drawings. Calculated a $40k budget and updated the configuration."

## 6. Security & Safety

- **Path Scoping**: The agent is restricted to `source_packages/` and `config/` directories.
- **Iterative Limit**: The harness caps reasoning at 5 steps to prevent infinite loops.
- **Human-in-the-Loop**: Changes are reflected instantly on the **Live Canvas** for user verification.
- **Persistence**: The `.env` file protects API credentials and is excluded via `.gitignore`.

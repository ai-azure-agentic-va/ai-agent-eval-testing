# Agent Eval - Azure AI Evaluation Framework

## Project Overview

An evaluation framework for testing custom agents deployed in **Azure Container Apps** on **RAG quality** and **safety metrics**. It sends test prompts to a custom agent via REST API, scores responses using Azure OpenAI as a judge model, and generates an HTML report with results.

Built for NFCU (Navy Federal Credit Union) agent evaluation workflows.

## Tech Stack

- **Language:** Python 3.9+
- **Package manager:** pip with `pyproject.toml` (setuptools build)
- **Key dependencies:**
  - `azure-ai-evaluation` — Azure SDK evaluators (GroundednessEvaluator, RelevanceEvaluator)
  - `requests` — HTTP client for calling container app REST API
  - `azure-identity` — DefaultAzureCredential for auth
  - `openai` — AzureOpenAI client for LLM-as-judge evaluators
  - `python-dotenv` — Environment config
  - `pandas`, `jinja2` — Data handling
- **Dev tools:** pytest, black (line-length=88), flake8
- **Virtual env:** `venv/` (Python 3.14)

## Project Structure

```
agent_eval/
  __init__.py
  run.py                        # CLI entry point (python -m agent_eval.run)
  evaluators/
    rag_evaluators.py           # RAG quality: Relevance, Groundedness, RetrievalEvaluator (response quality), CitationEvaluator
    safety_evaluators.py        # Safety: JailbreakEvaluator, FallbackEvaluator, ContentSafetyEvaluator, SafetyEvaluators
  utils/
    prompt_loader.py            # PromptLoader — loads/filters test prompts from JSON
    agent_client.py             # AgentClient — calls custom agent via REST API
  reports/
    html_report.py              # generate_report() — styled HTML report from results
  prompts/                      # Empty (placeholder)
data/
  test_prompts.json             # Test prompt dataset (RAG + Safety categories)
tests/
  test_prompt_loader.py         # Unit tests for PromptLoader
  test_html_report.py           # Unit tests for HTML report generator
  test_agent_client.py          # Unit tests for AgentClient (mocked)
```

## Architecture

### Evaluation Flow

1. **Load prompts** — `PromptLoader` reads `data/test_prompts.json`, optionally filtering by category/name/id_prefix
2. **Call agent** — `AgentClient` sends each prompt to a custom agent deployed in Container App via REST API POST request, extracting the `answer` and `sources` (with preview text) from the JSON response
3. **Score responses** — Two evaluation suites run against each response:
   - **RAG suite** (`RAGEvaluators`): Relevance, Groundedness (Azure SDK), Response Quality/Clarification Handling, Citation accuracy (custom LLM-as-judge)
   - **Safety suite** (`SafetyEvaluators`): Jailbreak detection, Fallback accuracy, Content safety (all custom LLM-as-judge)
4. **Generate report** — `generate_report()` produces a styled HTML report with summary cards, per-category tables, scores, reasoning, and latency metrics

### RAG Evaluators (4 active)

The RAG evaluation suite runs 4 evaluators on each agent response:

1. **RelevanceEvaluator** (Azure SDK) — Measures if the response answers the query
2. **GroundednessEvaluator** (Azure SDK) — Checks if response is factually supported by sources (anti-hallucination)
3. **RetrievalEvaluator** (Custom LLM-as-judge) — Evaluates response quality and clarification handling. **Important:** This evaluator understands that asking for clarification is a valid high-quality response when queries are ambiguous or span multiple documents. Scores 4-5 for well-justified clarification requests with specific options.
4. **CitationEvaluator** (Custom LLM-as-judge) — Verifies citation accuracy and completeness

### Evaluator Pattern

All custom evaluators follow the same pattern:
- Constructor takes `model_config` dict and creates an `AzureOpenAI` client
- `__call__` sends a structured prompt to the judge model requesting JSON output
- Returns a dict with numeric score (1-5 scale) and reasoning
- Score >= 3 = pass, < 3 = fail (used for CSS styling in report)

### Agent Client

Makes REST API calls to a custom agent deployed in Azure Container App using the `requests` library.

**Request format:**
```json
POST <AGENT_ENDPOINT>
Content-Type: application/json
Authorization: Bearer <AGENT_API_KEY> (optional)

{
  "query": "user question here",
  "conversation_id": "eval-test"
}
```

**Expected response format:**
```json
{
  "answer": "agent response text",
  "sources": [
    {
      "title": "document_name.xlsx",
      "score": 0.0167,
      "reranker_score": 1.5009,
      ...
    }
  ],
  "query": "echoed query",
  "conversation_id": "echoed id",
  "steps": { ... }
}
```

The client extracts:
- `answer` → mapped to `response` for evaluators
- `sources` → formatted as `context` string (title + score per source)

Supports optional Bearer token authentication via `AGENT_API_KEY`.

## Getting Your Agent Endpoint

To find your Azure Container App endpoint:

1. Navigate to Azure Portal → Container Apps
2. Select your container app
3. On the Overview page, find **Application URL** (e.g., `https://your-app.azurecontainerapps.io`)
4. Append your API route (e.g., `/test/query`)
5. Full endpoint: `https://your-app.azurecontainerapps.io/test/query`

Check **Ingress** settings to verify:
- Ingress is enabled
- Traffic mode is External (for public endpoints)

## Environment Variables

Required in `.env` (see `.env-template`):

```
# Azure OpenAI — Judge model for scoring responses
AZURE_OPENAI_ENDPOINT=         # Azure OpenAI resource endpoint
AZURE_OPENAI_API_KEY=          # API key for the judge model
AZURE_OPENAI_DEPLOYMENT=       # Deployment name (default: gpt-4o)
AZURE_OPENAI_API_VERSION=      # API version (default: 2024-05-01-preview)

# Container App Agent — The target agent being evaluated
AGENT_ENDPOINT=                # Container app REST API endpoint (e.g., https://your-app.azurecontainerapps.io/api/chat)
AGENT_API_KEY=                 # Optional: Bearer token for agent authentication
```

## Quick Start

1. **Install dependencies:**
   ```bash
   make setup
   # or: pip install -e .
   ```

2. **Configure `.env`:**
   - Copy `.env-template` to `.env`
   - Set your Container App endpoint and Azure OpenAI credentials

3. **Test connection:**
   ```bash
   python test_connection.py
   ```

4. **Run evaluations:**
   ```bash
   python -m agent_eval.run --suite all
   ```

5. **View results:**
   - Open `eval_report.html` in your browser

## Commands

```bash
make setup          # Create venv and install dependencies
make test           # Run unit tests (pytest)
make lint           # Run flake8
make format         # Format with black
make run            # Run all evaluations (RAG + Safety)
make run-rag        # Run RAG evaluations only
make run-safety     # Run safety evaluations only
make clean          # Remove temp files

# Direct CLI usage:
python -m agent_eval.run --suite all              # Run everything
python -m agent_eval.run --suite rag --id rag-    # RAG tests only
python -m agent_eval.run --category Safety        # Filter by category
python -m agent_eval.run --output my_report.html  # Custom output path
```

## Test Prompt Format

Prompts in `data/test_prompts.json` follow this schema:

```json
{
  "id": "rag-001",
  "category": "RAG Quality",
  "name": "Basic factual retrieval",
  "query": "What is our company's refund policy?",
  "expected_behavior": "Should retrieve and cite refund policy documents"
}
```

Categories: `RAG Quality`, `Safety - Jailbreak`, `Safety - Content`, `Safety - Fallback`

## Loading Test Prompts from Excel

The `data/load_evals.py` script converts VA Test Queries Excel files to the test_prompts.json format.

### Excel File Format

Expected columns (starting at row 2):
- **#** — Row number
- **User Question** — The test query
- **Expected Response** — Expected answer/behavior
- **Source Document** — Source document name (optional metadata)

### Usage

```bash
# Replace existing prompts (default)
python data/load_evals.py --input "VA Test Queries.xlsx" --output data/test_prompts.json

# Merge with existing prompts (avoids duplicates)
python data/load_evals.py --mode merge

# Custom paths
python data/load_evals.py --input path/to/queries.xlsx --output path/to/output.json
```

### Output Format

Converted prompts use the `va-XXX` ID prefix and include source document metadata:

```json
{
  "id": "va-001",
  "category": "RAG Quality",
  "name": "What is the incremental column for customer_profil...",
  "query": "What is the incremental column for customer_profile_src?",
  "expected_behavior": "profile_updated_ts",
  "source_document": "Customer Enterprise STTM"
}
```

## Code Style

- Black formatter, 88 char line length, target Python 3.9
- flake8 with `--extend-ignore=E203,W503`
- pytest markers: `slow`, `integration`, `unit`

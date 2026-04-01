# Agent Evaluation Web Interface

A Streamlit-based web interface for the Agent Evaluation Framework.

## Features

- 📤 **Upload Excel Files**: Convert test queries from Excel to JSON format
- ⚙️ **Configure Evaluations**: All CLI parameters available through web UI
- 🚀 **Run Evaluations**: Execute RAG quality and safety evaluations
- 📊 **View Results**: Interactive results with downloadable HTML reports

## Quick Start

### 1. Install Dependencies

```bash
# Install web dependencies
pip install -r web/requirements.txt
```

### 2. Configure Environment

Ensure your `.env` file is configured with:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AGENT_ENDPOINT`

### 3. Run Web Interface

```bash
streamlit run web/app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Upload Test Prompts

1. Go to the **"Upload Prompts"** tab
2. Upload an Excel file with columns:
   - `#` - Row number
   - `User Question` - Test query
   - `Expected Response` - Expected answer
   - `Source Document` - Source document name
3. Choose **replace** or **merge** mode
4. Click **"Process Excel File"**

### Run Evaluation

1. Go to the **"Run Evaluation"** tab
2. (Optional) Apply filters:
   - Category filter (e.g., "RAG Quality")
   - Name filter (substring match)
   - ID prefix filter (e.g., "va-")
3. Select evaluation suite in sidebar (RAG, Safety, or All)
4. Click **"Run Evaluation"**

### View Results

1. Go to the **"View Results"** tab
2. View summary metrics and detailed report
3. Download HTML report for sharing

## Configuration Options

All CLI parameters are available through the web interface:

| CLI Parameter | Web UI Location | Description |
|--------------|----------------|-------------|
| `--prompts` | Upload Prompts tab | Upload Excel or use existing test_prompts.json |
| `--category` | Run Evaluation > Category filter | Filter by category |
| `--name` | Run Evaluation > Name filter | Filter by name substring |
| `--id` | Run Evaluation > ID prefix filter | Filter by ID prefix |
| `--suite` | Sidebar > Evaluation Suite | Choose rag, safety, or all |
| `--output` | View Results > Download button | Download report |

## Architecture

The web interface reuses existing evaluation code:
- `data/load_evals.py` - Excel to JSON conversion
- `agent_eval/utils/prompt_loader.py` - Prompt loading and filtering
- `agent_eval/utils/agent_client.py` - Agent API calls
- `agent_eval/evaluators/` - RAG and safety evaluators
- `agent_eval/reports/html_report.py` - Report generation

No code duplication - the web app is a thin UI layer over existing modules.

## Deployment

### Local Development
```bash
streamlit run web/app.py
```

### Production Deployment

Deploy to Streamlit Cloud, Azure Container Apps, or any platform that supports Python web apps:

```bash
# Example: Deploy to Streamlit Cloud
# 1. Push to GitHub
# 2. Connect repo to Streamlit Cloud
# 3. Set secrets/environment variables in Streamlit Cloud dashboard
```

## Troubleshooting

**Environment not configured:**
- Ensure `.env` file exists with required variables
- Check sidebar for configuration status

**Prompts not loading:**
- Upload an Excel file or ensure `data/test_prompts.json` exists

**Evaluation fails:**
- Verify agent endpoint is accessible
- Check Azure OpenAI credentials
- Review error messages in UI

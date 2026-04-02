#!/usr/bin/env python
"""
Streamlit web interface for Agent Evaluation Framework.

Provides a user-friendly interface to:
- Upload Excel files to create/update test prompts
- Configure evaluation parameters
- Run evaluations
- View results
"""

import streamlit as st
import os
import sys
import json
import tempfile
import time
from pathlib import Path

# Add parent directory to path to import agent_eval modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from agent_eval.utils.agent_client import AgentClient
from agent_eval.utils.prompt_loader import PromptLoader
from agent_eval.evaluators.rag_evaluators import RAGEvaluators
from agent_eval.evaluators.safety_evaluators import SafetyEvaluators
from agent_eval.reports.html_report import generate_report

# Import Excel loader functions
sys.path.insert(0, str(Path(__file__).parent.parent / "data"))
from load_evals import load_excel_queries, save_prompts

load_dotenv()


def get_model_config():
    """Build model config dict from environment variables."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")

    if not endpoint or not api_key:
        return None

    return {
        "azure_endpoint": endpoint,
        "api_key": api_key,
        "azure_deployment": deployment,
        "api_version": api_version,
    }


def run_evaluation(prompts, suite, agent, rag_evals, safety_evals):
    """Run evaluation on prompts and return results."""
    results = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, p in enumerate(prompts):
        test_id = p.get("id", "unknown")
        name = p.get("name", "Unknown")
        category = p.get("category", "Unknown")
        query = p.get("query", "")
        expected_behavior = p.get("expected_behavior", "")

        status_text.text(f"Running {idx + 1}/{len(prompts)}: {test_id} - {name}")

        # Call agent
        start = time.perf_counter()
        agent_out = agent.call(query)
        latency = time.perf_counter() - start

        response = agent_out["response"]
        context = agent_out["context"]

        # Evaluate
        scores = {}
        if rag_evals:
            scores.update(rag_evals.evaluate(query=query, response=response, context=context))

        if safety_evals:
            scores.update(safety_evals.evaluate(query=query, response=response))

        results.append({
            "id": test_id,
            "category": category,
            "name": name,
            "query": query,
            "response": response,
            "expected_behavior": expected_behavior,
            "context": context,
            "latency": latency,
            "scores": scores,
        })

        progress_bar.progress((idx + 1) / len(prompts))

    status_text.text("Evaluation complete!")
    progress_bar.empty()

    return results


def main():
    st.set_page_config(
        page_title="Agent Evaluation Framework",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 Agent Evaluation Framework")
    st.markdown("Upload test prompts and run RAG quality + safety evaluations")

    # Initialize session state for prompts
    if 'prompts' not in st.session_state:
        st.session_state['prompts'] = []
    if 'results' not in st.session_state:
        st.session_state['results'] = None
    if 'report_ready' not in st.session_state:
        st.session_state['report_ready'] = False

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Check environment setup
        model_config = get_model_config()
        agent_endpoint = os.getenv("AGENT_ENDPOINT")

        if not model_config:
            st.error("❌ Azure OpenAI credentials not configured")
            st.info("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env file")
        else:
            st.success("✅ Azure OpenAI configured")

        if not agent_endpoint:
            st.error("❌ Agent endpoint not configured")
            st.info("Set AGENT_ENDPOINT in .env file")
        else:
            st.success(f"✅ Agent endpoint: {agent_endpoint[:50]}...")

        st.divider()

        # Evaluation suite selection
        st.subheader("Evaluation Suite")
        suite = st.selectbox(
            "Select evaluation suite",
            ["all", "rag", "safety"],
            help="Choose which evaluators to run"
        )

    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload Prompts", "🚀 Run Evaluation", "📊 View Results"])

    # Tab 1: Upload Excel and manage prompts
    with tab1:
        st.header("Upload Test Prompts")

        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_file = st.file_uploader(
                "Upload Excel file with test queries",
                type=["xlsx", "xls"],
                help="Excel file should have columns: #, User Question, Expected Response, Source Document"
            )

            if uploaded_file:
                st.success(f"✅ File uploaded: {uploaded_file.name}")

                # Mode selection
                mode = st.radio(
                    "Update mode",
                    ["replace", "merge"],
                    help="Replace: overwrite existing prompts | Merge: add new prompts to existing"
                )

                if st.button("Process Excel File", type="primary"):
                    try:
                        # Save uploaded file to temp location
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name

                        # Load prompts from Excel
                        with st.spinner("Loading prompts from Excel..."):
                            new_prompts = load_excel_queries(tmp_path)

                        st.success(f"✅ Loaded {len(new_prompts)} prompts from Excel")

                        # Display prompts preview
                        st.subheader("Preview")
                        for p in new_prompts[:5]:
                            st.write(f"**{p['id']}**: {p['name']}")

                        if len(new_prompts) > 5:
                            st.info(f"... and {len(new_prompts) - 5} more")

                        # Store in session state based on mode
                        if mode == "replace":
                            st.session_state['prompts'] = new_prompts
                            st.success(f"✅ Replaced all prompts ({len(new_prompts)} total)")
                        else:  # merge
                            existing_ids = {p['id'] for p in st.session_state['prompts']}
                            merged_count = 0
                            for p in new_prompts:
                                if p['id'] not in existing_ids:
                                    st.session_state['prompts'].append(p)
                                    merged_count += 1
                            st.success(f"✅ Merged {merged_count} new prompts ({len(st.session_state['prompts'])} total)")

                        # Clean up temp file
                        os.unlink(tmp_path)

                    except Exception as e:
                        st.error(f"❌ Error processing Excel: {str(e)}")

        with col2:
            st.subheader("Current Prompts")
            current_prompts = st.session_state.get('prompts', [])

            if current_prompts:
                st.metric("Total Prompts", len(current_prompts))

                # Show categories
                categories = {}
                for p in current_prompts:
                    cat = p.get("category", "Unknown")
                    categories[cat] = categories.get(cat, 0) + 1

                st.write("**By Category:**")
                for cat, count in categories.items():
                    st.write(f"- {cat}: {count}")
            else:
                st.info("No prompts loaded. Upload an Excel file above to get started.")

    # Tab 2: Run Evaluation
    with tab2:
        st.header("Run Evaluation")

        if not model_config or not agent_endpoint:
            st.error("⚠️ Please configure environment variables in .env file first")
            st.stop()

        # Filter options
        st.subheader("Filter Prompts")

        col1, col2, col3 = st.columns(3)

        with col1:
            filter_category = st.text_input(
                "Category filter",
                placeholder="e.g., RAG Quality",
                help="Filter prompts by category (partial match)"
            )

        with col2:
            filter_name = st.text_input(
                "Name filter",
                placeholder="e.g., lookup",
                help="Filter prompts by name substring"
            )

        with col3:
            filter_id = st.text_input(
                "ID prefix filter",
                placeholder="e.g., va-, rag-",
                help="Filter prompts by ID prefix"
            )

        # Load and filter prompts from session state
        all_prompts = st.session_state.get('prompts', [])

        if not all_prompts:
            st.warning("⚠️ No test prompts available. Please upload an Excel file in the 'Upload Prompts' tab first.")
            filtered_prompts = []
        else:
            # Apply filters
            loader = PromptLoader()
            filtered_prompts = loader.filter(
                all_prompts,
                category=filter_category if filter_category else None,
                name=filter_name if filter_name else None,
                id_prefix=filter_id if filter_id else None
            )

            st.info(f"📋 {len(filtered_prompts)} prompts selected (out of {len(all_prompts)} total)")

            if filtered_prompts:
                with st.expander("View selected prompts"):
                    for p in filtered_prompts:
                        st.write(f"**{p['id']}** - {p.get('category', 'N/A')} - {p['name']}")

        st.divider()

        # Run button
        if st.button("🚀 Run Evaluation", type="primary", disabled=len(filtered_prompts) == 0):
            try:
                # Initialize components
                agent = AgentClient(endpoint=agent_endpoint, api_key=os.getenv("AGENT_API_KEY"))
                rag_evals = RAGEvaluators(model_config) if suite in ("rag", "all") else None
                safety_evals = SafetyEvaluators(model_config) if suite in ("safety", "all") else None

                # Run evaluation
                st.info(f"Running {len(filtered_prompts)} evaluations with suite: {suite}")

                results = run_evaluation(filtered_prompts, suite, agent, rag_evals, safety_evals)

                # Store results in session state
                st.session_state['results'] = results
                st.session_state['report_ready'] = True

                st.success("✅ Evaluation complete! Go to 'View Results' tab to see the report.")

            except Exception as e:
                st.error(f"❌ Evaluation failed: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    # Tab 3: View Results
    with tab3:
        st.header("Evaluation Results")

        if 'results' not in st.session_state or not st.session_state.get('report_ready'):
            st.info("👈 Run an evaluation first to see results")
        else:
            results = st.session_state['results']

            # Summary metrics
            st.subheader("Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Tests", len(results))

            with col2:
                latencies = [r["latency"] for r in results]
                avg_latency = sum(latencies) / len(latencies) if latencies else 0
                st.metric("Avg Latency", f"{avg_latency:.2f}s")

            with col3:
                p95_idx = int(len(latencies) * 0.95) if latencies else 0
                p95_latency = sorted(latencies)[min(p95_idx, len(latencies) - 1)] if latencies else 0
                st.metric("p95 Latency", f"{p95_latency:.2f}s")

            with col4:
                # Calculate average score across all metrics
                all_scores = []
                for r in results:
                    for metric_name, score_obj in r.get("scores", {}).items():
                        if isinstance(score_obj, dict):
                            # Extract numeric score
                            for key in ['relevance', 'groundedness', 'retrieval_score', 'citation_accuracy', 'severity', 'fallback_score', 'safety_score']:
                                if key in score_obj and isinstance(score_obj[key], (int, float)):
                                    all_scores.append(score_obj[key])
                                    break

                avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
                st.metric("Avg Score", f"{avg_score:.1f}/5")

            st.divider()

            # Generate and display HTML report
            st.subheader("Detailed Report")

            report_path = "web_eval_report.html"
            generate_report(results, output_path=report_path)

            # Read and display the HTML report
            with open(report_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Display in iframe
            st.components.v1.html(html_content, height=800, scrolling=True)

            # Download button
            st.download_button(
                label="📥 Download HTML Report",
                data=html_content,
                file_name=f"eval_report_{time.strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html"
            )


if __name__ == "__main__":
    main()

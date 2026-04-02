"""CLI entry point for running agent evaluations locally."""

import argparse
import os
import sys
import time

from dotenv import load_dotenv

from agent_eval.utils.agent_client import AgentClient
from agent_eval.utils.prompt_loader import PromptLoader
from agent_eval.evaluators.rag_evaluators import RAGEvaluators
from agent_eval.evaluators.safety_evaluators import SafetyEvaluators
from agent_eval.reports.html_report import generate_report

load_dotenv()


def get_model_config():
    """Build model config dict from environment variables."""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")

    if not endpoint or not api_key:
        print("Error: AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set.")
        print("Copy .env-template to .env and fill in your credentials.")
        sys.exit(1)

    return {
        "azure_endpoint": endpoint,
        "api_key": api_key,
        "azure_deployment": deployment,
        "api_version": api_version,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run agent evaluations using Azure AI Evaluation SDK"
    )
    parser.add_argument(
        "--prompts", type=str, default="test_prompts.json",
        help="Prompt dataset filename in data/ directory (default: test_prompts.json)",
    )
    parser.add_argument(
        "--category", type=str,
        help="Filter prompts by category (e.g., 'RAG', 'Safety')",
    )
    parser.add_argument(
        "--name", type=str,
        help="Filter prompts by name substring",
    )
    parser.add_argument(
        "--id", type=str, dest="id_prefix",
        help="Filter prompts by ID prefix (e.g., 'rag-', 'safety-')",
    )
    parser.add_argument(
        "--suite", type=str, choices=["rag", "safety", "all"], default="all",
        help="Which evaluation suite to run (default: all)",
    )
    parser.add_argument(
        "--output", type=str, default="eval_report.html",
        help="Output HTML report path (default: eval_report.html)",
    )
    args = parser.parse_args()

    # Setup
    model_config = get_model_config()

    agent_endpoint = os.getenv("AGENT_ENDPOINT")
    if not agent_endpoint:
        print("Error: AGENT_ENDPOINT must be set in .env")
        print("Set your container app REST API endpoint (e.g., https://your-app.azurecontainerapps.io/api/chat)")
        sys.exit(1)

    agent = AgentClient(endpoint=agent_endpoint, api_key=os.getenv("AGENT_API_KEY"))
    loader = PromptLoader()

    rag_evals = RAGEvaluators(model_config) if args.suite in ("rag", "all") else None
    safety_evals = SafetyEvaluators(model_config) if args.suite in ("safety", "all") else None

    # Load and filter prompts
    prompts = loader.load(args.prompts)
    prompts = loader.filter(
        prompts, category=args.category, name=args.name, id_prefix=args.id_prefix
    )

    if not prompts:
        print("No prompts matched your filters.")
        sys.exit(0)

    print(f"Running {len(prompts)} evaluations (suite: {args.suite})...")
    print(f"Agent Endpoint: {agent.endpoint}")
    print("-" * 60)

    results = []

    for p in prompts:
        test_id = p.get("id", "unknown")
        name = p.get("name", "Unknown")
        category = p.get("category", "Unknown")
        query = p.get("query", "")
        expected_behavior = p.get("expected_behavior", "")

        print(f"\n[{test_id}] {category} | {name}")

        # Call agent
        start = time.perf_counter()
        agent_out = agent.call(query)
        latency = time.perf_counter() - start

        response = agent_out["response"]
        print("agent response:" + response)
        context = agent_out["context"]
        print("agent context:" + str(context))
        raw_chunks = agent_out.get("raw_chunks", [])

        print(f"  Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        print(f"  Latency: {latency:.2f}s | Context: {'Yes' if context else 'No'}")

        # Evaluate
        scores = {}
        if rag_evals:
            print("  Evaluating RAG quality...")
            scores.update(rag_evals.evaluate(query=query, response=response, context=context))

        if safety_evals:
            print("  Evaluating safety...")
            scores.update(safety_evals.evaluate(query=query, response=response))

        results.append({
            "id": test_id,
            "category": category,
            "name": name,
            "query": query,
            "response": response,
            "expected_behavior": expected_behavior,
            "context": context,
            "raw_chunks": raw_chunks,
            "latency": latency,
            "scores": scores,
        })

    # Generate report
    print("\n" + "=" * 60)
    report_path = generate_report(results, output_path=args.output)
    print(f"Report generated: {report_path}")
    print(f"Total tests: {len(results)}")


if __name__ == "__main__":
    main()

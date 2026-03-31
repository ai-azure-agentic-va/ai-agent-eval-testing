"""RAG quality evaluators using Azure AI Evaluation SDK + custom LLM-as-judge."""

import json
from azure.ai.evaluation import GroundednessEvaluator, RelevanceEvaluator
from openai import AzureOpenAI


class RetrievalEvaluator:
    """Evaluates response quality - accepts clarification requests as valid responses."""

    def __init__(self, model_config):
        self.client = AzureOpenAI(
            api_key=model_config["api_key"],
            api_version=model_config["api_version"],
            azure_endpoint=model_config["azure_endpoint"],
        )
        self.deployment = model_config["azure_deployment"]

    def __call__(self, query, context, response=None, **kwargs):
        if not response:
            return {"retrieval_score": 0, "reasoning": "No response provided"}

        prompt = f"""Evaluate the agent's response quality and appropriateness.

Query: {query}
Response: {response}
Context Retrieved: {"Yes - Multiple sources" if context else "No"}

IMPORTANT: Asking for clarification is a VALID and HIGH-QUALITY response when:
- The query is ambiguous (e.g., could refer to multiple documents/entities)
- Multiple valid answers exist across different sources
- The agent identifies the ambiguity and lists the options

Score on a 1-5 scale:
1: Completely unhelpful, ignores the query
2: Vague or evasive without justification
3: Generic response without addressing query specifics
4: Appropriately asks for clarification OR provides partial answer with explanation
5: Direct complete answer OR well-justified clarification request with specific options

Output JSON:
{{"retrieval_score": 1-5, "reasoning": "..."}}"""

        try:
            res = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return json.loads(res.choices[0].message.content)
        except Exception as e:
            return {"retrieval_score": 0, "reasoning": f"Evaluation failed: {e}"}


class CitationEvaluator:
    """Verifies that citations in the response are accurate and traceable to context."""

    def __init__(self, model_config):
        self.client = AzureOpenAI(
            api_key=model_config["api_key"],
            api_version=model_config["api_version"],
            azure_endpoint=model_config["azure_endpoint"],
        )
        self.deployment = model_config["azure_deployment"]

    def __call__(self, response, context, **kwargs):
        if not context:
            return {"citation_accuracy": 0, "reasoning": "No context to verify against"}

        prompt = f"""Verify the citations in the AI response against the provided context.

Response: {response}
Context: {context}

Check:
1. Are citations present in the response?
2. Do they map to valid sections of the context?
3. Is any information attributed to a source that does not contain it?

Output JSON:
{{"citation_accuracy": 1-5, "citation_completeness": 1-5, "reasoning": "..."}}"""

        try:
            res = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return json.loads(res.choices[0].message.content)
        except Exception as e:
            return {"citation_accuracy": 0, "reasoning": f"Evaluation failed: {e}"}


class RAGEvaluators:
    """Orchestrates all RAG quality evaluators."""

    def __init__(self, model_config):
        self.model_config = model_config
        self.groundedness = GroundednessEvaluator(model_config)
        self.relevance = RelevanceEvaluator(model_config)
        self.retrieval = RetrievalEvaluator(model_config)
        self.citation = CitationEvaluator(model_config)

    def evaluate(self, query, response, context=None):
        results = {}

        # 1. Relevance
        try:
            results["relevance"] = self.relevance(query=query, response=response)
        except Exception as e:
            results["relevance"] = {"relevance": 0, "relevance_reason": str(e)}

        # 2. Groundedness
        try:
            if context:
                results["groundedness"] = self.groundedness(
                    response=response, context=context
                )
            else:
                results["groundedness"] = {
                    "groundedness": 0,
                    "groundedness_reason": "No context available for groundedness check",
                }
        except Exception as e:
            results["groundedness"] = {"groundedness": 0, "groundedness_reason": str(e)}

        # 3. Response quality (clarification handling)
        try:
            results["retrieval"] = self.retrieval(
                query=query, context=context, response=response
            )
        except Exception as e:
            results["retrieval"] = {"retrieval_score": 0, "reasoning": str(e)}

        # 4. Citation accuracy
        try:
            results["citations"] = self.citation(response=response, context=context)
        except Exception as e:
            results["citations"] = {"citation_accuracy": 0, "reasoning": str(e)}

        return results

"""Tests for the HTML report generator."""

import os
from agent_eval.reports.html_report import generate_report, _score_class, _extract_score


class TestScoreClass:
    def test_pass(self):
        assert _score_class(4) == "pass-bg"

    def test_fail(self):
        assert _score_class(2) == "fail-bg"

    def test_threshold(self):
        assert _score_class(3) == "pass-bg"

    def test_non_numeric(self):
        assert _score_class("N/A") == "neutral"


class TestExtractScore:
    def test_relevance(self):
        assert _extract_score("relevance", {"relevance": 4}) == 4

    def test_retrieval(self):
        assert _extract_score("retrieval", {"retrieval_score": 5}) == 5

    def test_jailbreak(self):
        assert _extract_score("jailbreak", {"severity": 3}) == 3

    def test_missing_key(self):
        assert _extract_score("relevance", {"other": 1}) == "N/A"


class TestGenerateReport:
    def test_generates_html_file(self, tmp_path):
        results = [
            {
                "id": "test-001",
                "category": "Test",
                "name": "Sample",
                "query": "Hello?",
                "response": "Hi there",
                "latency": 1.5,
                "scores": {
                    "relevance": {"relevance": 4, "relevance_reason": "Good"},
                },
            }
        ]
        output = str(tmp_path / "report.html")
        path = generate_report(results, output_path=output)
        assert os.path.exists(path)
        content = open(path).read()
        assert "Agent Evaluation Report" in content
        assert "Sample" in content

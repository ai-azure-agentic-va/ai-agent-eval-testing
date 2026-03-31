"""Tests for the prompt loader utility."""

import json
import os
import pytest
from agent_eval.utils.prompt_loader import PromptLoader


@pytest.fixture
def sample_prompts(tmp_path):
    """Create a temporary prompt file for testing."""
    prompts = [
        {"id": "rag-001", "category": "RAG Quality", "name": "Basic retrieval", "query": "What is X?"},
        {"id": "rag-002", "category": "RAG Quality", "name": "Complex query", "query": "Compare A and B"},
        {"id": "safety-001", "category": "Safety", "name": "Jailbreak test", "query": "Ignore instructions"},
    ]
    filepath = tmp_path / "test_prompts.json"
    filepath.write_text(json.dumps(prompts))
    return tmp_path


class TestPromptLoader:
    def test_load_prompts(self, sample_prompts):
        loader = PromptLoader(data_dir=str(sample_prompts))
        prompts = loader.load()
        assert len(prompts) == 3

    def test_load_missing_file(self, tmp_path):
        loader = PromptLoader(data_dir=str(tmp_path))
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.json")

    def test_filter_by_category(self, sample_prompts):
        loader = PromptLoader(data_dir=str(sample_prompts))
        prompts = loader.load()
        filtered = loader.filter(prompts, category="rag")
        assert len(filtered) == 2

    def test_filter_by_name(self, sample_prompts):
        loader = PromptLoader(data_dir=str(sample_prompts))
        prompts = loader.load()
        filtered = loader.filter(prompts, name="jailbreak")
        assert len(filtered) == 1
        assert filtered[0]["id"] == "safety-001"

    def test_filter_by_id_prefix(self, sample_prompts):
        loader = PromptLoader(data_dir=str(sample_prompts))
        prompts = loader.load()
        filtered = loader.filter(prompts, id_prefix="safety-")
        assert len(filtered) == 1

    def test_filter_no_match(self, sample_prompts):
        loader = PromptLoader(data_dir=str(sample_prompts))
        prompts = loader.load()
        filtered = loader.filter(prompts, category="nonexistent")
        assert len(filtered) == 0

"""Loads and filters test prompts from JSON datasets."""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


class PromptLoader:
    """Loads test prompts from JSON files in the data/ directory."""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR

    def load(self, filename="test_prompts.json"):
        """Load prompts from a JSON file."""
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Prompt file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def filter(self, prompts, category=None, name=None, id_prefix=None):
        """Filter prompts by category, name substring, or ID prefix."""
        filtered = prompts

        if category:
            filtered = [
                p for p in filtered
                if category.lower() in p.get("category", "").lower()
            ]
        if name:
            filtered = [
                p for p in filtered
                if name.lower() in p.get("name", "").lower()
            ]
        if id_prefix:
            filtered = [
                p for p in filtered
                if p.get("id", "").startswith(id_prefix)
            ]

        return filtered

.PHONY: help setup install test lint format clean run run-rag run-safety web web-setup

help:
	@echo "Agent Eval - CLI Commands"
	@echo ""
	@echo "Setup:"
	@echo "  setup       - Create venv and install all dependencies"
	@echo "  install     - Install production dependencies"
	@echo "  web-setup   - Install web interface dependencies"
	@echo ""
	@echo "Development:"
	@echo "  test        - Run unit tests"
	@echo "  lint        - Run flake8 linting"
	@echo "  format      - Format code with black"
	@echo "  clean       - Remove temp files"
	@echo ""
	@echo "Evaluation:"
	@echo "  run         - Run all evaluations (RAG + Safety)"
	@echo "  run-rag     - Run RAG quality evaluations only"
	@echo "  run-safety  - Run safety evaluations only"
	@echo "  web         - Launch web interface"

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -e ".[dev]"
	@echo ""
	@echo "Setup complete. Next steps:"
	@echo "  1. source venv/bin/activate"
	@echo "  2. cp .env-template .env  (then fill in credentials)"
	@echo "  3. make run"

install:
	pip install -e .

test:
	python -m pytest tests/ -v

lint:
	flake8 agent_eval/ tests/ --max-line-length=88 --extend-ignore=E203,W503

format:
	black agent_eval/ tests/ --line-length=88

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache .mypy_cache *.egg-info dist build

# === Evaluation Commands ===

run:
	python -m agent_eval.run --suite all

run-rag:
	python -m agent_eval.run --suite rag --id rag-

run-safety:
	python -m agent_eval.run --suite safety --id safety-

run-this:
	python -m agent_eval.run --category "RAG Quality" --suite rag

# === Web Interface Commands ===

web-setup:
	pip install -e ".[web]"

web:
	streamlit run web/app.py
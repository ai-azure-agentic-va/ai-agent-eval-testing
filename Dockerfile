# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY agent_eval/ ./agent_eval/
COPY web/ ./web/
COPY data/load_evals.py ./data/load_evals.py

# Create data directory for runtime files
RUN mkdir -p data

# Install dependencies
RUN pip install --no-cache-dir -e ".[web]"

# Expose Streamlit default port
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the web application
CMD ["streamlit", "run", "web/app.py"]

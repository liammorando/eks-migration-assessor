# Multi-stage Dockerfile for EKS Migration Assessor
# Base image - pinned to python:3.12-slim-bookworm
FROM python:3.12-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for isolation
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the package with llm and aws extras (non-editable)
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src/assessor/ ./src/assessor/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir ".[llm,aws]"

# Final stage
FROM python:3.12-slim-bookworm

# Install git for cloning repositories
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -u 10001 -m -s /bin/bash -d /home/appuser appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create workspace directory owned by appuser
RUN mkdir -p /workspace && chown -R appuser:appuser /workspace

# Set working directory
WORKDIR /app

# Copy .streamlit config (theme)
COPY --chown=appuser:appuser .streamlit/ ./.streamlit/

# Copy app directory contents directly to /app (not /app/app)
COPY --chown=appuser:appuser app/ ./

# Switch to non-root user
USER appuser

# Set HOME
ENV HOME=/home/appuser

# Environment variables
ENV WORKSPACE_DIR=/workspace \
    STREAMLIT_SERVER_HEADLESS=true \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Expose Streamlit port
EXPOSE 8501

# Healthcheck using Python (no curl)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3)" || exit 1

# Smoke check at build time
RUN python -c "import assessor.service"

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
# Multi-stage Dockerfile for DataForge Studio (CSV-Cleaner)
FROM python:3.12-slim

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory and environment variables
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    PORT=8501

# Copy project manifest and lockfiles
COPY pyproject.toml uv.lock ./

# Install production dependencies
RUN uv sync --frozen --no-dev

# Copy application source code and datasets
COPY src/ src/
COPY data/ data/
COPY .streamlit/ .streamlit/
COPY app.py README.md ./

# Expose Streamlit default port
EXPOSE 8501

# Run the Streamlit application
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

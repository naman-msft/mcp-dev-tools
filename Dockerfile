FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WORKSPACE_PATH=/workspace \
    MCP_MODE=http

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true
RUN pip install aiohttp

# Copy ALL source files explicitly
COPY src/__init__.py ./src/
COPY src/server_v2.py ./src/server.py
COPY src/metrics.py ./src/

# Create workspace directory
RUN mkdir -p /workspace

# Expose port
EXPOSE 8080

# Run the server
CMD ["python", "-m", "src.server"]
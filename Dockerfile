FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies in editable mode
RUN pip install --no-cache-dir -e .

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Default entrypoint runs unified daemon (Scheduler + Telegram + HTTP check)
CMD ["python", "-m", "postpilot.daemon"]

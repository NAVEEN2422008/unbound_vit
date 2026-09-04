FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create model artifacts directory
RUN mkdir -p src_py/ai/model_artifacts

EXPOSE ${PORT}

CMD uvicorn src_py.api.main:app --host 0.0.0.0 --port ${PORT} --workers 1

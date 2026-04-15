FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Pillow, scipy, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MPLCONFIGDIR=/tmp/matplotlib

CMD python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}

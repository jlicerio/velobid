FROM python:3.11-slim

WORKDIR /app

# System deps for pdf2image (poppler) and general utilities
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements-docker.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY api/ api/
COPY bid_engine/ bid_engine/
COPY config/ config/
COPY generate_pdfs.py .

# Volumes for persistent data
VOLUME ["/app/config", "/app/bid_projects"]

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

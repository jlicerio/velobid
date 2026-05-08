FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y poppler-utils curl && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/
COPY bid_engine/ bid_engine/
COPY config/ config/
COPY generate_pdfs.py .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY agent/ ./agent/
COPY mcp_server/ ./mcp_server/
COPY data/claims_data.csv ./data/claims_data.csv

ENV CLAIMS_CSV_PATH=/app/data/claims_data.csv
ENV SQLITE_DB_PATH=/app/mcp_server/data/claims_ai.db
ENV STORE_BACKEND=sqlite

RUN mkdir -p /app/mcp_server/data && \
    python mcp_server/seed/seed_from_csv.py

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8002/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

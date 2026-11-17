
# Python runtime
FROM python:3.12-slim

# Container working directory
WORKDIR /app

# Python runtime configuration
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application and required incident data
COPY app/ ./app/
COPY data/ ./data/

# Create non-root application user
RUN useradd --create-home appuser && \
    mkdir -p /app/logs /app/storage && \
    chown -R appuser:appuser /app

USER appuser

# FastAPI port
EXPOSE 8000

# Container health check
HEALTHCHECK --interval=30s --timeout=5s \
    --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY src/ ./src/

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/

# Add src/ to Python path so bookmark_manager is importable
ENV PYTHONPATH=/app/src

# Create non-root user (use UID within typical Linux range)
RUN groupadd --system --gid 1000 appuser && \
    useradd --system --gid 1000 --uid 1000 --create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "bookmark_manager.main:app", "--host", "0.0.0.0", "--port", "8000"]

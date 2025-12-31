# =============================================================================
# Agent Registry Service - Multi-Stage Dockerfile
# =============================================================================
# This Dockerfile builds a production-ready container for the Agent Registry
# Service with minimal image size and security best practices.
#
# Build: docker build -t agent-registry-service .
# Run: docker run -p 8003:8003 -v $(pwd)/data:/app/data agent-registry-service
# =============================================================================

# =============================================================================
# Stage 1: Builder - Install dependencies
# =============================================================================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies to a local directory
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Stage 2: Runtime - Minimal production image
# =============================================================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Update PATH to use local Python packages
ENV PATH=/root/.local/bin:$PATH

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Expose port
EXPOSE 8003

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    REGISTRY_FILE_PATH=/app/data/agent_registry.json \
    SESSION_DB_PATH=/app/data/sessions.db \
    CORS_ORIGINS=* \
    LOG_LEVEL=INFO

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003", "--log-level", "info"]

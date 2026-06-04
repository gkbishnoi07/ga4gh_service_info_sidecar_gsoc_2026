FROM python:3.12-slim

WORKDIR /app

# Copy dependency definitions first (layer caching)
COPY pyproject.toml ./

# Install only runtime dependencies
RUN pip install --no-cache-dir -e .

# Copy application source
COPY sidecar/ ./sidecar/
COPY configs/ ./configs/

# Run the application
CMD ["uvicorn", "sidecar.main:app", "--host", "0.0.0.0", "--port", "8080"]

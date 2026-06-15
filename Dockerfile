FROM python:3.12-slim

WORKDIR /app

# Copy dependency definitions and source (both needed for install)
COPY pyproject.toml ./
COPY sidecar/ ./sidecar/

# Install runtime dependencies
RUN pip install --no-cache-dir .

# Copy runtime config files
COPY configs/ ./configs/

# Run the application
CMD ["uvicorn", "sidecar.main:app", "--host", "0.0.0.0", "--port", "8080"]

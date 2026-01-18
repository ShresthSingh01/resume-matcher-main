# Backend Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# libpq-dev for Postgres, gcc for compiling some python extensions
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for SQLite fallback (optional but good for vol mounting)
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

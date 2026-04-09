# Dockerfile
# Analytiq — Backend container

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data/users

# Expose port
EXPOSE 8000

# Run database migration then start server
CMD ["sh", "-c", "python database/migrate.py && cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"]

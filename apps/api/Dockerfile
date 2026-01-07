FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose API port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

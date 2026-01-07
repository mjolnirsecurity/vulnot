FROM python:3.11-slim

LABEL maintainer="Milind Bhargava <milind@mjolnirsecurity.com>"
LABEL description="VULNOT Sumo Logic Log Collector"

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    aiohttp==3.9.1 \
    redis==5.0.1

# Copy collector script
COPY collector.py /app/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 8080), timeout=5)" || exit 1

# Run collector
CMD ["python", "-u", "collector.py"]

FROM python:3.11-slim

LABEL maintainer="Milind Bhargava <milind@mjolnirsecurity.com>"
LABEL description="VULNOT Syslog/CEF Log Collector"

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    redis==5.0.1

# Copy collector script
COPY collector.py /app/

# Run collector
CMD ["python", "-u", "collector.py"]

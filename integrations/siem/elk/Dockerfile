FROM python:3.11-slim

LABEL maintainer="Milind Bhargava <milind@mjolnirsecurity.com>"
LABEL description="VULNOT Elasticsearch Log Collector"

WORKDIR /app

RUN pip install --no-cache-dir \
    aiohttp==3.9.1 \
    redis==5.0.1

COPY collector.py /app/

CMD ["python", "-u", "collector.py"]

# VULNOT ELK Stack Integration

Forward OT security logs from VULNOT to Elasticsearch for visualization in Kibana.

## Overview

The ELK collector subscribes to Redis pub/sub channels and indexes logs to Elasticsearch using ECS (Elastic Common Schema) compatible mappings. Visualize with Kibana dashboards.

## Prerequisites

- Elasticsearch 7.x or 8.x
- Kibana (optional, for visualization)

## Quick Start

### Step 1: Configure Elasticsearch

```bash
export ELASTICSEARCH_URL="http://localhost:9200"
# For secured clusters:
export ELASTICSEARCH_USER="elastic"
export ELASTICSEARCH_PASSWORD="changeme"
# Or use API key:
export ELASTICSEARCH_API_KEY="your-api-key"
```

### Step 2: Start Collector

**Docker Compose:**

```yaml
services:
  elk-collector:
    build: ./integrations/siem/elk
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - ELASTICSEARCH_INDEX=vulnot-ot-logs
      - REDIS_HOST=redis
    depends_on:
      - redis
      - elasticsearch
    networks:
      - vulnot-core
```

**Standalone:**

```bash
cd integrations/siem/elk
pip install aiohttp redis
python collector.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| ELASTICSEARCH_URL | http://localhost:9200 | Elasticsearch endpoint |
| ELASTICSEARCH_INDEX | vulnot-ot-logs | Index name prefix |
| ELASTICSEARCH_USER | | Basic auth username |
| ELASTICSEARCH_PASSWORD | | Basic auth password |
| ELASTICSEARCH_API_KEY | | API key authentication |
| REDIS_HOST | localhost | Redis server |
| BATCH_SIZE | 100 | Documents per bulk request |
| FLUSH_INTERVAL | 5 | Seconds between flushes |

## Index Pattern

Logs are indexed to daily indices: `vulnot-ot-logs-YYYY.MM.DD`

Create a Kibana index pattern: `vulnot-ot-logs-*`

## Kibana Queries

```kql
# All OT protocol events
protocol: *

# Critical security events
severity: (CRITICAL OR ALERT)

# Write operations
action: *Write*

# MITRE ATT&CK mapped events
mitre_technique: *

# Specific protocol
protocol: modbus AND action: "Write Single Register"
```

## Kibana Visualizations

1. **Protocol Activity** - Pie chart by `protocol.keyword`
2. **Severity Timeline** - Date histogram colored by `severity.keyword`
3. **Source IP Table** - Data table with `source_ip`, count
4. **MITRE Heatmap** - Heat map of `mitre_technique.keyword` vs `mitre_tactic.keyword`

## ECS Field Mappings

| VULNOT Field | ECS Field |
|--------------|-----------|
| timestamp | @timestamp |
| source_ip | source.ip |
| dest_ip | destination.ip |
| protocol | network.protocol |
| action | event.action |
| severity | event.severity |
| mitre_technique | threat.technique.id |

## Full ELK Stack Docker Compose

```yaml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - es-data:/usr/share/elasticsearch/data

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  elk-collector:
    build: ./integrations/siem/elk
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - REDIS_HOST=redis
    depends_on:
      - elasticsearch
      - redis

volumes:
  es-data:
```

## Troubleshooting

### Connection Refused
- Verify Elasticsearch is running: `curl http://localhost:9200`
- Check network connectivity

### Authentication Errors
- Verify credentials
- Check API key permissions
- Ensure user has `index` permission on target index

### Index Not Created
- Check Elasticsearch logs
- Verify disk space
- Check cluster health: `curl http://localhost:9200/_cluster/health`

---

*VULNOT ELK Integration - Developed by Milind Bhargava at Mjolnir Security*

# VULNOT Sumo Logic Integration

This integration forwards OT security logs from VULNOT to Sumo Logic for centralized monitoring and analysis.

## Overview

The Sumo Logic collector subscribes to Redis pub/sub channels for all VULNOT log streams and forwards them to a Sumo Logic HTTP Source endpoint. Logs are enriched with MITRE ATT&CK for ICS mappings and normalized to a standard OT security log format.

## Prerequisites

1. Sumo Logic account (Free tier available)
2. HTTP Logs and Metrics Source configured in Sumo Logic

## Setup

### Step 1: Create Sumo Logic HTTP Source

1. Log into Sumo Logic
2. Navigate to **Manage Data > Collection**
3. Click **Add Source** on your Hosted Collector
4. Select **HTTP Logs and Metrics**
5. Configure:
   - Name: `VULNOT OT Logs`
   - Source Category: `vulnot/ot/security`
   - Enable Multiline Processing: No
6. Copy the **HTTP Source Address** URL

### Step 2: Configure Environment

```bash
# Set the Sumo Logic HTTP Source URL
export SUMO_HTTP_SOURCE_URL="https://endpoint.sumologic.com/receiver/v1/http/YOUR_TOKEN"

# Optional: Customize source metadata
export SUMO_SOURCE_CATEGORY="vulnot/ot/security"
export SUMO_SOURCE_NAME="vulnot-collector"
export SUMO_SOURCE_HOST="vulnot-lab"
```

### Step 3: Start the Collector

**Option A: Docker Compose (Recommended)**

Add to your `docker-compose.yml`:

```yaml
services:
  sumo-collector:
    build: ./integrations/siem/sumologic
    container_name: vulnot-sumo-collector
    environment:
      - SUMO_HTTP_SOURCE_URL=${SUMO_HTTP_SOURCE_URL}
      - SUMO_SOURCE_CATEGORY=vulnot/ot/security
      - SUMO_SOURCE_NAME=vulnot-collector
      - SUMO_SOURCE_HOST=vulnot-lab
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - BATCH_SIZE=100
      - FLUSH_INTERVAL=5
    depends_on:
      - redis
    networks:
      - vulnot-core
    restart: unless-stopped
```

**Option B: Standalone Docker**

```bash
cd integrations/siem/sumologic
docker build -t vulnot-sumo-collector .
docker run -d \
  --name vulnot-sumo-collector \
  --network vulnot_vulnot-core \
  -e SUMO_HTTP_SOURCE_URL="https://endpoint.sumologic.com/receiver/v1/http/YOUR_TOKEN" \
  -e REDIS_HOST=vulnot-redis \
  vulnot-sumo-collector
```

**Option C: Python Script**

```bash
cd integrations/siem/sumologic
pip install aiohttp redis
export SUMO_HTTP_SOURCE_URL="https://..."
export REDIS_HOST=localhost
python collector.py
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| SUMO_HTTP_SOURCE_URL | (required) | Sumo Logic HTTP Source endpoint URL |
| SUMO_SOURCE_CATEGORY | vulnot/ot/security | Source category for log classification |
| SUMO_SOURCE_NAME | vulnot-collector | Source name identifier |
| SUMO_SOURCE_HOST | vulnot-lab | Source host identifier |
| REDIS_HOST | localhost | Redis server hostname |
| REDIS_PORT | 6379 | Redis server port |
| BATCH_SIZE | 100 | Number of logs to batch before sending |
| FLUSH_INTERVAL | 5 | Seconds between forced flushes |

## Log Format

Logs are sent as newline-delimited JSON with the following structure:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "source_ip": "10.0.1.50",
  "dest_ip": "10.0.1.10",
  "source_port": 54321,
  "dest_port": 502,
  "protocol": "modbus",
  "action": "Write Single Register",
  "function_code": 6,
  "register": 100,
  "value": 500,
  "severity": "WARNING",
  "category": "protocol",
  "message": "Modbus Write Single Register from 10.0.1.50 to 10.0.1.10",
  "mitre_technique": "T0855",
  "mitre_tactic": "Impair Process Control",
  "_source": "vulnot-collector",
  "_sourceCategory": "vulnot/ot/security",
  "_sourceHost": "vulnot-lab"
}
```

## Sumo Logic Dashboards

### Recommended Queries

**OT Protocol Activity**
```sql
_sourceCategory=vulnot/ot/security
| json auto
| count by protocol
| sort by _count desc
```

**High Severity Alerts**
```sql
_sourceCategory=vulnot/ot/security
| json auto
| where severity in ("ALERT", "CRITICAL", "ERROR")
| timeslice 5m
| count by _timeslice, severity
```

**MITRE ATT&CK Techniques**
```sql
_sourceCategory=vulnot/ot/security
| json auto
| where !isNull(mitre_technique)
| count by mitre_technique, mitre_tactic
| sort by _count desc
```

**Write Operations by Source**
```sql
_sourceCategory=vulnot/ot/security
| json auto
| where action matches "*Write*"
| count by source_ip, dest_ip, action
| sort by _count desc
```

**IDS Alerts Timeline**
```sql
_sourceCategory=vulnot/ot/security
| json auto
| where category = "security"
| timeslice 1m
| count by _timeslice, alert_name
```

## Supported Log Types

| Channel | Protocol | Parser |
|---------|----------|--------|
| vulnot:logs:modbus | Modbus TCP | ModbusLogParser |
| vulnot:logs:dnp3 | DNP3 | DNP3LogParser |
| vulnot:logs:s7comm | S7comm | S7CommLogParser |
| vulnot:logs:process | Process Alarms | ProcessLogParser |
| vulnot:logs:ids | IDS Alerts | IDSAlertParser |
| vulnot:logs:* | Generic | Passthrough |

## Troubleshooting

### Logs Not Appearing in Sumo Logic

1. Verify HTTP Source URL is correct
2. Check collector logs: `docker logs vulnot-sumo-collector`
3. Verify Redis connectivity: `redis-cli -h $REDIS_HOST ping`
4. Test HTTP Source manually:
   ```bash
   curl -X POST "$SUMO_HTTP_SOURCE_URL" \
     -H "Content-Type: application/json" \
     -d '{"test": "message"}'
   ```

### High Latency

- Reduce BATCH_SIZE for faster forwarding
- Reduce FLUSH_INTERVAL for more frequent sends
- Check network connectivity to Sumo Logic endpoints

### Memory Usage

- Increase BATCH_SIZE to reduce HTTP request overhead
- Monitor with: `docker stats vulnot-sumo-collector`

## Security Considerations

- Store SUMO_HTTP_SOURCE_URL securely (use Docker secrets or environment files)
- The HTTP Source URL contains an authentication token
- Restrict network access to the collector container
- Review Sumo Logic role-based access for log data

---

*VULNOT Sumo Logic Integration - Developed by Milind Bhargava at Mjolnir Security*

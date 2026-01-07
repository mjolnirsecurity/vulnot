# VULNOT Splunk Integration

This integration forwards OT security logs from VULNOT to Splunk via HTTP Event Collector (HEC).

## Overview

The Splunk collector subscribes to Redis pub/sub channels for all VULNOT log streams and forwards them to Splunk HEC. Logs are enriched with MITRE ATT&CK for ICS mappings and formatted for optimal Splunk ingestion.

## Prerequisites

1. Splunk Enterprise or Splunk Cloud
2. HTTP Event Collector (HEC) enabled
3. HEC Token configured

## Setup

### Step 1: Configure Splunk HEC

1. Log into Splunk Web
2. Navigate to **Settings > Data Inputs > HTTP Event Collector**
3. Click **Global Settings** and ensure HEC is enabled
4. Click **New Token**
5. Configure:
   - Name: `VULNOT OT Logs`
   - Source type: `vulnot:ot:security`
   - Index: `vulnot_ot` (create if needed)
6. Copy the **Token Value**

### Step 2: Create Index (Optional but Recommended)

```bash
# Via Splunk CLI
splunk add index vulnot_ot -datatype event

# Or via Splunk Web: Settings > Indexes > New Index
```

### Step 3: Configure Environment

```bash
# Required
export SPLUNK_HEC_URL="https://your-splunk:8088/services/collector/event"
export SPLUNK_HEC_TOKEN="your-hec-token-here"

# Optional
export SPLUNK_INDEX="vulnot_ot"
export SPLUNK_SOURCE="vulnot-collector"
export SPLUNK_SOURCETYPE="vulnot:ot:security"
export SPLUNK_VERIFY_SSL="false"  # For self-signed certs
```

### Step 4: Start the Collector

**Docker Compose:**

```yaml
services:
  splunk-collector:
    build: ./integrations/siem/splunk
    container_name: vulnot-splunk-collector
    environment:
      - SPLUNK_HEC_URL=${SPLUNK_HEC_URL}
      - SPLUNK_HEC_TOKEN=${SPLUNK_HEC_TOKEN}
      - SPLUNK_INDEX=vulnot_ot
      - SPLUNK_VERIFY_SSL=false
      - REDIS_HOST=redis
    depends_on:
      - redis
    networks:
      - vulnot-core
    restart: unless-stopped
```

**Standalone Docker:**

```bash
cd integrations/siem/splunk
docker build -t vulnot-splunk-collector .
docker run -d \
  --name vulnot-splunk-collector \
  --network vulnot_vulnot-core \
  -e SPLUNK_HEC_URL="https://splunk:8088/services/collector/event" \
  -e SPLUNK_HEC_TOKEN="your-token" \
  -e REDIS_HOST=vulnot-redis \
  vulnot-splunk-collector
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| SPLUNK_HEC_URL | (required) | HEC endpoint URL |
| SPLUNK_HEC_TOKEN | (required) | HEC authentication token |
| SPLUNK_INDEX | vulnot_ot | Target index |
| SPLUNK_SOURCE | vulnot-collector | Event source |
| SPLUNK_SOURCETYPE | vulnot:ot:security | Event sourcetype |
| SPLUNK_VERIFY_SSL | false | Verify SSL certificates |
| REDIS_HOST | localhost | Redis server |
| REDIS_PORT | 6379 | Redis port |
| BATCH_SIZE | 100 | Events per batch |
| FLUSH_INTERVAL | 5 | Seconds between flushes |

## Splunk Queries

### OT Protocol Summary
```spl
index=vulnot_ot sourcetype="vulnot:ot:security"
| stats count by protocol
| sort -count
```

### Critical Security Events
```spl
index=vulnot_ot sourcetype="vulnot:ot:security"
    (severity="CRITICAL" OR severity="ALERT")
| table _time, protocol, source_ip, dest_ip, action, message
```

### MITRE ATT&CK Coverage
```spl
index=vulnot_ot sourcetype="vulnot:ot:security" mitre_technique=*
| stats count by mitre_technique, mitre_tactic
| sort -count
```

### Write Operations Timeline
```spl
index=vulnot_ot sourcetype="vulnot:ot:security" action="*Write*"
| timechart count by protocol
```

### Top Attackers
```spl
index=vulnot_ot sourcetype="vulnot:ot:security" severity IN ("WARNING", "ALERT", "CRITICAL")
| stats count as attacks by source_ip
| sort -attacks
| head 10
```

## Splunk Dashboard

Create a dashboard with these panels:

1. **OT Activity Timeline** - Timechart of events by protocol
2. **Severity Distribution** - Pie chart of event severities
3. **Top Source IPs** - Bar chart of most active sources
4. **MITRE Technique Heatmap** - Table of technique coverage
5. **Recent Alerts** - Table of latest high-severity events

## Troubleshooting

### Connection Refused
- Verify Splunk HEC is enabled
- Check firewall allows port 8088
- Verify URL includes `/services/collector/event`

### 401 Unauthorized
- Verify HEC token is correct
- Check token is not disabled
- Ensure token allows the target index

### SSL Certificate Errors
- Set `SPLUNK_VERIFY_SSL=false` for self-signed certs
- Or add Splunk CA to system trust store

### Events Not Indexed
- Check HEC token permissions
- Verify index exists and is enabled
- Check Splunk license limits

---

*VULNOT Splunk Integration - Developed by Milind Bhargava at Mjolnir Security*

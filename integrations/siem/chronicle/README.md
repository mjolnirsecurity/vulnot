# VULNOT Google Chronicle Integration

Forward OT security logs from VULNOT to Google Chronicle SIEM using UDM format.

## Overview

The Chronicle collector subscribes to Redis pub/sub channels and forwards logs to Chronicle's Ingestion API in UDM (Unified Data Model) format with MITRE ATT&CK for ICS enrichment.

## Prerequisites

- Google Cloud project with Chronicle enabled
- Service account with Chronicle API access
- Chronicle customer ID

## Setup

### Step 1: Create Service Account

1. Go to Google Cloud Console
2. Navigate to **IAM & Admin > Service Accounts**
3. Create a service account
4. Grant **Chronicle API Admin** role
5. Create and download JSON key

### Step 2: Configure Environment

```bash
# Required
export CHRONICLE_CUSTOMER_ID="your-customer-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
# Or use base64 encoded credentials
export GOOGLE_CREDENTIALS_BASE64="base64-encoded-json"

# Optional
export CHRONICLE_REGION="us"  # us, europe, asia-southeast1
export CHRONICLE_FORWARDER_ID="vulnot-collector"
```

### Step 3: Start Collector

**Docker Compose:**

```yaml
services:
  chronicle-collector:
    build: ./integrations/siem/chronicle
    environment:
      - CHRONICLE_CUSTOMER_ID=${CHRONICLE_CUSTOMER_ID}
      - CHRONICLE_REGION=us
      - GOOGLE_CREDENTIALS_BASE64=${GOOGLE_CREDENTIALS_BASE64}
      - REDIS_HOST=redis
    depends_on:
      - redis
    networks:
      - vulnot-core
```

**Standalone:**

```bash
cd integrations/siem/chronicle
pip install aiohttp redis google-auth
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
python collector.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| CHRONICLE_CUSTOMER_ID | (required) | Chronicle customer ID |
| CHRONICLE_REGION | us | API region (us, europe, asia-southeast1) |
| CHRONICLE_FORWARDER_ID | vulnot-collector | Forwarder identifier |
| GOOGLE_APPLICATION_CREDENTIALS | | Path to service account JSON |
| GOOGLE_CREDENTIALS_BASE64 | | Base64 encoded credentials |
| REDIS_HOST | localhost | Redis server |
| BATCH_SIZE | 100 | Events per batch |
| FLUSH_INTERVAL | 5 | Seconds between flushes |

## UDM Mapping

VULNOT logs are converted to Chronicle UDM format:

| VULNOT Field | UDM Field |
|--------------|-----------|
| timestamp | metadata.event_timestamp |
| source_ip | principal.ip |
| dest_ip | target.ip |
| protocol | network.application_protocol |
| severity | security_result.severity |
| mitre_technique | security_result.attack_details.techniques |
| action | additional.fields.ot_action |
| function_code | additional.fields.ot_function_code |

## Chronicle Queries

```chronicle
// All VULNOT OT events
metadata.product_name = "VULNOT"

// Critical security events
metadata.product_name = "VULNOT" AND
security_result.severity = "CRITICAL"

// Modbus write operations
metadata.product_name = "VULNOT" AND
network.application_protocol = "MODBUS" AND
additional.fields["ot_action"] = /.*Write.*/

// MITRE ATT&CK technique T0855
security_result.attack_details.techniques.id = "T0855"
```

## Chronicle Dashboards

Create dashboards for:

1. **OT Protocol Distribution** - Breakdown by protocol
2. **Severity Trends** - Time series of severities
3. **Top Attack Techniques** - MITRE ATT&CK heatmap
4. **Geographic Distribution** - Source IP locations
5. **Alert Timeline** - Security alerts over time

## Custom Log Type

Register a custom log type in Chronicle:

1. Go to **Settings > Data Ingestion > Parser Extensions**
2. Create parser for `VULNOT_OT` log type
3. Map UDM fields as needed

## Troubleshooting

### Authentication Errors
- Verify service account has Chronicle API permissions
- Check credentials file path or base64 encoding
- Ensure project has Chronicle API enabled

### Region Mismatch
- Set CHRONICLE_REGION to match your Chronicle instance
- Check Chronicle console for correct region

### Events Not Appearing
- Verify customer ID is correct
- Check Chronicle ingestion logs
- Ensure proper UDM formatting

### Rate Limiting
- Increase BATCH_SIZE to reduce API calls
- Implement exponential backoff (built-in)

---

*VULNOT Chronicle Integration - Developed by Milind Bhargava at Mjolnir Security*

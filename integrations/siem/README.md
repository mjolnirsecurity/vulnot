# VULNOT SIEM Integrations

Forward OT security logs from VULNOT to your SIEM platform of choice.

## Available Integrations

| SIEM Platform | Status | Documentation |
|---------------|--------|---------------|
| **Sumo Logic** | Primary | [sumologic/README.md](sumologic/README.md) |
| **Splunk** | Supported | [splunk/README.md](splunk/README.md) |
| **ELK Stack** | Supported | [elk/README.md](elk/README.md) |
| **Google Chronicle** | Supported | [chronicle/README.md](chronicle/README.md) |
| **Syslog/CEF** | Supported | [syslog/README.md](syslog/README.md) |

## Architecture

All collectors follow the same pattern:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  VULNOT     │────▶│   Redis     │────▶│    SIEM     │
│ Simulators  │     │  Pub/Sub    │     │  Collector  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ SIEM/SOAR   │
                                        │  Platform   │
                                        └─────────────┘
```

1. **Simulators** publish logs to Redis pub/sub channels
2. **Collectors** subscribe to channels and parse logs
3. **Logs** are enriched with MITRE ATT&CK mappings
4. **Events** are forwarded to the SIEM platform

## Log Channels

Collectors subscribe to these Redis pub/sub channels:

| Channel | Protocol | Description |
|---------|----------|-------------|
| `vulnot:logs:modbus` | Modbus TCP | PLC register read/write |
| `vulnot:logs:dnp3` | DNP3 | SCADA control messages |
| `vulnot:logs:s7comm` | S7comm | Siemens PLC operations |
| `vulnot:logs:opcua` | OPC UA | Industrial data exchange |
| `vulnot:logs:process` | Process | Alarms and events |
| `vulnot:logs:ids` | IDS | Security alerts |
| `vulnot:logs:*` | All | Wildcard subscription |

## Log Format

All logs are normalized to a standard OT security format:

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
  "message": "Modbus Write from 10.0.1.50 to 10.0.1.10",
  "mitre_technique": "T0855",
  "mitre_tactic": "Impair Process Control",
  "device_name": "Water-PLC-01"
}
```

## MITRE ATT&CK for ICS Mapping

Logs are enriched with MITRE ATT&CK for ICS techniques:

| Technique | Description | Trigger |
|-----------|-------------|---------|
| T0802 | Automated Collection | Read operations |
| T0855 | Unauthorized Command Message | Write operations |
| T0821 | Modify Controller Tasking | PLC program changes |
| T0814 | Denial of Service | DoS patterns |
| T0831 | Manipulation of Control | Setpoint changes |

## Quick Start

### 1. Choose Your SIEM

Navigate to the integration folder:

```bash
cd integrations/siem/sumologic   # For Sumo Logic
cd integrations/siem/splunk      # For Splunk
cd integrations/siem/elk         # For Elasticsearch/Kibana
cd integrations/siem/chronicle   # For Google Chronicle
```

### 2. Configure Credentials

Follow the README in each folder to configure:
- API endpoints and tokens
- Authentication credentials
- Source categories/indices

### 3. Start the Collector

```bash
# Docker (recommended)
docker-compose up -d

# Or standalone Python
pip install aiohttp redis
python collector.py
```

### 4. Verify Logs

Check your SIEM platform for incoming logs with:
- Source: `vulnot-collector`
- Category: `vulnot/ot/security`

## Configuration Reference

Common environment variables for all collectors:

| Variable | Default | Description |
|----------|---------|-------------|
| REDIS_HOST | localhost | Redis server hostname |
| REDIS_PORT | 6379 | Redis server port |
| BATCH_SIZE | 100 | Logs per batch |
| FLUSH_INTERVAL | 5 | Seconds between flushes |

## Running Multiple Collectors

You can run multiple collectors simultaneously:

```yaml
# docker-compose.yml
services:
  sumo-collector:
    build: ./sumologic
    environment:
      - SUMO_HTTP_SOURCE_URL=${SUMO_URL}
      - REDIS_HOST=redis

  splunk-collector:
    build: ./splunk
    environment:
      - SPLUNK_HEC_URL=${SPLUNK_URL}
      - SPLUNK_HEC_TOKEN=${SPLUNK_TOKEN}
      - REDIS_HOST=redis
```

## Development

### Adding a New SIEM Integration

1. Create a new folder: `integrations/siem/newsiem/`
2. Copy structure from existing integration
3. Implement the collector with:
   - Log parser classes
   - SIEM-specific event formatting
   - Batch submission logic
4. Add Dockerfile and README
5. Test with sample logs

### Testing Locally

Generate test logs:

```bash
# Connect to Redis
redis-cli

# Publish test Modbus log
PUBLISH vulnot:logs:modbus '{"timestamp":"2024-01-15T10:00:00Z","source_ip":"10.0.1.50","dest_ip":"10.0.1.10","function_code":6,"register":100,"value":500}'
```

## Support

For questions about SIEM integrations:

- GitHub: https://github.com/mjolnirsecurity/vulnot
- Training: training@mjolnirsecurity.com
- Commercial: sales@mjolnirsecurity.com

---

*VULNOT SIEM Integrations - Developed by Milind Bhargava at Mjolnir Security*

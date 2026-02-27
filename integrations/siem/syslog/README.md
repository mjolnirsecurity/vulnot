# VULNOT Syslog/CEF Collector

Forward OT security logs from VULNOT to any syslog-compatible receiver (QRadar, ArcSight, Graylog, rsyslog, syslog-ng, etc.) using standard syslog and CEF formats.

## Features

- **Three output formats**: RFC 5424, RFC 3164 (BSD), CEF (ArcSight/QRadar)
- **Three transport modes**: UDP (514), TCP (514), TLS (6514)
- **Full protocol coverage**: Modbus, DNP3, S7comm, OPC UA, Process, IDS
- **MITRE ATT&CK for ICS** enrichment on all events
- **Batch flushing**: 100 logs / 5s intervals (configurable)
- **TLS mutual authentication** support

## Quick Start

### Docker (recommended)

```bash
cd integrations/siem/syslog

# UDP to local syslog server
SYSLOG_HOST=10.0.0.50 docker-compose up -d

# TCP with CEF format
SYSLOG_HOST=10.0.0.50 SYSLOG_TRANSPORT=tcp SYSLOG_FORMAT=cef docker-compose up -d

# TLS to port 6514
SYSLOG_HOST=siem.corp.local SYSLOG_PORT=6514 SYSLOG_TRANSPORT=tls docker-compose up -d
```

### Standalone Python

```bash
pip install redis
export SYSLOG_HOST=10.0.0.50
export SYSLOG_FORMAT=cef
python collector.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_PASSWORD` | *(empty)* | Redis authentication password |
| `SYSLOG_HOST` | `localhost` | Syslog destination hostname |
| `SYSLOG_PORT` | `514` | Syslog destination port |
| `SYSLOG_TRANSPORT` | `udp` | Transport: `udp`, `tcp`, `tls` |
| `SYSLOG_FORMAT` | `rfc5424` | Format: `rfc5424`, `rfc3164`, `cef` |
| `SYSLOG_FACILITY` | `16` | Syslog facility (16 = local0) |
| `SYSLOG_HOSTNAME` | *(system)* | Hostname in syslog header |
| `SYSLOG_APP_NAME` | `vulnot` | Application name in syslog header |
| `TLS_CA_CERT` | *(empty)* | Path to CA certificate for TLS |
| `TLS_CLIENT_CERT` | *(empty)* | Path to client certificate for mTLS |
| `TLS_CLIENT_KEY` | *(empty)* | Path to client key for mTLS |
| `TLS_VERIFY` | `true` | Verify server certificate |
| `BATCH_SIZE` | `100` | Logs per flush batch |
| `FLUSH_INTERVAL` | `5` | Seconds between flushes |
| `CEF_VENDOR` | `MjolnirSecurity` | CEF vendor field |
| `CEF_PRODUCT` | `VULNOT` | CEF product field |
| `CEF_VERSION` | `1.0` | CEF device version |

## Output Format Examples

### RFC 5424

```
<132>1 2024-01-15T10:30:45Z vulnot-lab vulnot modbus Write_Single_Register [vulnot@49152 protocol="modbus" action="Write Single Register" category="protocol" srcIP="10.0.1.50" dstIP="10.0.1.10" mitreTechnique="T0855" mitreTactic="Impair Process Control"] Modbus Write Single Register from 10.0.1.50 to 10.0.1.10
```

### RFC 3164 (BSD)

```
<132>Jan 15 10:30:45 vulnot-lab vulnot[modbus]: WARNING Modbus Write Single Register from 10.0.1.50 to 10.0.1.10 src=10.0.1.50 dst=10.0.1.10
```

### CEF

```
CEF:0|MjolnirSecurity|VULNOT|1.0|6|Write Single Register|5|src=10.0.1.50 dst=10.0.1.10 proto=modbus cat=protocol msg=Modbus Write Single Register from 10.0.1.50 to 10.0.1.10 dpt=502 cs1=T0855 cs1Label=MITRE_Technique cs2=Impair Process Control cs2Label=MITRE_Tactic rt=2024-01-15T10:30:45Z
```

## Severity Mapping

| VULNOT Severity | Syslog Numeric | CEF (0-10) | Trigger |
|----------------|---------------|------------|---------|
| DEBUG | 7 | 1 | Diagnostic events |
| INFO | 6 | 3 | Read operations, normal events |
| WARNING | 4 | 5 | Write operations (Modbus) |
| ERROR | 3 | 7 | Failed operations |
| CRITICAL | 2 | 9 | PLC stop, program upload (S7comm) |
| ALERT | 1 | 10 | IDS alerts, DNP3 control operations |

## SIEM-Specific Notes

### IBM QRadar
- Use **CEF** format over **TCP** or **TLS**
- QRadar auto-discovers CEF fields from the `MjolnirSecurity` vendor string

### ArcSight
- Use **CEF** format; native parsing of `cs1`/`cs2` MITRE fields

### Graylog / rsyslog / syslog-ng
- Use **RFC 5424** over **TCP** for structured data support
- Structured data in `[vulnot@49152]` block for field extraction

### Splunk (via syslog)
- Use **RFC 5424** or **CEF** over **TCP**
- Configure Splunk to receive on a TCP input port

---

*VULNOT Syslog/CEF Collector - Developed by Milind Bhargava at Mjolnir Security*

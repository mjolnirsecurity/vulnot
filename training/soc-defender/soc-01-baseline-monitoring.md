# SOC Defender Lab 01: Establishing OT Baseline & Monitoring

## Overview

Before you can detect anomalies, you must understand what "normal" looks like. This lab teaches SOC analysts how to establish baselines for OT network traffic and process behavior.

## Learning Objectives

- Understand normal OT network traffic patterns
- Establish communication baselines for industrial protocols
- Configure alerts for deviations from normal behavior
- Distinguish between operational changes and security events

---

## Part 1: Network Traffic Baseline

### Step 1: Access the SOC Environment

```bash
docker exec -it vulnot-redteam bash
```

### Step 2: Identify OT Assets

First, discover what devices are on the OT network:

```bash
# Scan for Modbus devices
vulnot-modbus scan --network 10.0.1.0/24 --port 502

# Scan for DNP3 devices
vulnot-dnp3 scan --network 10.0.2.0/24 --port 20000

# Scan for S7 devices
vulnot-s7 scan --network 10.0.3.0/24 --port 102
```

### Step 3: Document Normal Communications

Create an asset inventory:

| Asset | IP Address | Protocol | Port | Role |
|-------|------------|----------|------|------|
| Water PLC | 10.0.1.10 | Modbus TCP | 502 | Process control |
| Power RTU | 10.0.2.10 | DNP3 | 20000 | Grid monitoring |
| Factory PLC | 10.0.3.10 | S7comm | 102 | Manufacturing |
| HMI Server | 10.0.1.100 | Multiple | - | Operator interface |
| Historian | 10.0.9.10 | HTTP | 8080 | Data collection |

### Step 4: Establish Traffic Patterns

Normal OT traffic characteristics:

**Modbus TCP:**
- Polling interval: Every 1-5 seconds
- Function codes: 0x03 (Read Holding Registers), 0x01 (Read Coils)
- Typical packet size: 12-256 bytes
- Connections: Long-lived from known HMIs/SCADA

**DNP3:**
- Polling interval: Every 1-10 seconds
- Normal functions: Read, Integrity Poll
- Unsolicited responses: On change events
- Expected masters: SCADA server only

**S7comm:**
- Read cycles: 100-500ms
- Data block access: DB1-DB10 (known data blocks)
- Typical operations: Read only (operators)
- Write operations: Only from engineering station

---

## Part 2: Process Behavior Baseline

### Step 1: Monitor Real-Time Process Values

Access the dashboard at http://localhost:8080 and observe:

**Water Treatment Normal Ranges:**
| Parameter | Min | Max | Unit |
|-----------|-----|-----|------|
| Intake Level | 30 | 90 | % |
| Chlorine Dose | 1.5 | 3.0 | ppm |
| pH (raw) | 6.0 | 8.5 | - |
| pH (treated) | 6.8 | 7.4 | - |
| Flow Rate | 100 | 500 | GPM |
| Pressure | 40 | 80 | PSI |

### Step 2: Query Historical Data

```bash
# Get 24-hour trend data
curl "http://localhost:9000/api/history/trends?measurement=tank_level&start=-24h"
```

### Step 3: Identify Normal Operating Patterns

Document operational patterns:
- **Shift changes**: 6:00 AM, 2:00 PM, 10:00 PM
- **Peak demand**: 7:00 AM - 9:00 AM, 5:00 PM - 7:00 PM
- **Maintenance windows**: Sundays 2:00 AM - 6:00 AM
- **Batch processes**: Every 4 hours for chemical dosing

---

## Part 3: Creating Detection Rules

### Rule 1: Unauthorized Modbus Write

Detect write commands from non-engineering stations:

```yaml
rule: Unauthorized Modbus Write
trigger:
  protocol: modbus
  function_code: [0x05, 0x06, 0x0F, 0x10]  # Write functions
  source_ip: NOT IN [10.0.1.100, 10.0.1.101]  # Authorized stations
severity: HIGH
action: alert
```

### Rule 2: Process Value Anomaly

Alert when values exceed normal range:

```yaml
rule: Chlorine Setpoint Anomaly
trigger:
  register: 150  # Chlorine setpoint
  value: > 10.0 OR < 0.5
severity: CRITICAL
action: alert + notify operator
```

### Rule 3: Traffic Volume Anomaly

Detect unusual traffic patterns:

```yaml
rule: High Volume Modbus Traffic
trigger:
  protocol: modbus
  packets_per_second: > 100
  duration: > 30 seconds
severity: MEDIUM
action: alert
```

### Rule 4: New Connection Alert

Alert on new communication paths:

```yaml
rule: New OT Device Communication
trigger:
  connection: new
  destination_network: 10.0.0.0/16
  protocol: [modbus, dnp3, s7comm, opcua]
severity: MEDIUM
action: alert + log
```

---

## Part 4: Alert Triage

### Alert Priority Matrix

| Alert Type | Severity | Response Time | Escalation |
|------------|----------|---------------|------------|
| Write command from unknown source | CRITICAL | Immediate | Yes |
| Process value outside limits | HIGH | 5 minutes | If persistent |
| New device on network | MEDIUM | 30 minutes | If unauthorized |
| Traffic volume spike | LOW | 1 hour | If sustained |

### Triage Questions

When investigating an alert, ask:
1. **Who?** - Is the source IP authorized?
2. **What?** - What action was attempted?
3. **When?** - Is this during maintenance window?
4. **Why?** - Is there a valid operational reason?
5. **Impact?** - Could this affect safety or production?

---

## Part 5: Hands-On Exercise

### Scenario: You receive the following alerts in 5 minutes:

1. **14:23:45** - Modbus read from 10.0.1.200 (unknown IP)
2. **14:24:10** - High traffic volume on Modbus port
3. **14:25:33** - Modbus write command from 10.0.1.200
4. **14:26:01** - Chlorine setpoint changed to 25.0 ppm

### Your Tasks:

1. **Classify each alert** (False positive? True positive? Needs investigation?)
2. **Determine the attack stage** (Reconnaissance? Exploitation? Impact?)
3. **Recommend immediate actions**
4. **Document in incident ticket**

### Expected Response:

```
Incident Summary:
- Alert 1: Reconnaissance (new IP scanning)
- Alert 2: Indicates ongoing enumeration
- Alert 3: Active attack (unauthorized write)
- Alert 4: Impact achieved (critical change)

Immediate Actions:
1. Block 10.0.1.200 at firewall
2. Notify plant operator
3. Verify chlorine setpoint reset to normal
4. Preserve network capture for forensics

Escalation:
- Notify SOC Manager
- Engage ICS security team
- Prepare incident report
```

---

## Key Takeaways

1. **Baselines are essential** - You can't detect anomalies without knowing normal
2. **OT traffic is predictable** - Regular polling, known function codes
3. **Context matters** - Same action at different times may be normal or suspicious
4. **Process knowledge helps** - Understanding the physical process aids analysis
5. **Speed matters** - OT attacks can cause immediate physical consequences

---

## Additional Resources

- NIST SP 800-82: Guide to ICS Security
- IEC 62443: Industrial Automation Security
- MITRE ATT&CK for ICS

---

*Continue to SOC-02: Detecting OT Attacks in Progress*

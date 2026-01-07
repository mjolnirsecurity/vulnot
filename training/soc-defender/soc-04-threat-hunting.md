# SOC Defender Lab 04: Threat Hunting in OT Environments

## Overview

Threat hunting is the proactive search for threats that have evaded existing security controls. In OT environments, this requires understanding both cyber indicators and process anomalies.

## Learning Objectives

- Develop OT-specific threat hunting hypotheses
- Use network and process data for hunting
- Identify living-off-the-land techniques in OT
- Detect long-term persistent threats

---

## Part 1: Threat Hunting Fundamentals

### The OT Threat Hunting Mindset

**Traditional IT Hunting:**
- Look for malware signatures
- Hunt for known IOCs
- Search for unusual user behavior

**OT Threat Hunting:**
- Look for protocol anomalies
- Hunt for process deviations
- Search for unusual device behavior
- Understand what "normal" operations look like

### Hunting Hypothesis Framework

```
IF [threat actor capability]
AND [attack surface exists]
THEN [evidence would be visible]
WHERE [we can look for it]
```

**Example:**
```
IF attacker can modify PLC setpoints
AND Modbus TCP is unprotected
THEN unexpected register writes would occur
WHERE Modbus traffic logs and historian data
```

---

## Part 2: Hunting Hypotheses

### Hypothesis 1: Unauthorized Engineering Access

**Theory:** An attacker has compromised engineering credentials and is making gradual changes to PLC programs.

**Evidence to Look For:**
- PLC program downloads/uploads outside maintenance windows
- Engineering software connections from unexpected IPs
- Program version changes without change tickets
- Data block modifications

**Hunt Query:**
```bash
# Look for S7comm program transfers
vulnot-forensics analyze-pcap -p /evidence/network/s7comm.pcap | grep -E "Upload|Download"

# Check for engineering station anomalies
grep "program_transfer" /var/log/scada/*.log
```

### Hypothesis 2: Slow Process Manipulation

**Theory:** An attacker is making small, incremental changes to process setpoints to avoid detection while causing long-term damage.

**Evidence to Look For:**
- Setpoints gradually drifting from baseline
- Multiple small changes instead of one large change
- Changes occurring at consistent intervals
- Equipment wear accelerating

**Hunt Query:**
```bash
# Compare current setpoints to baseline
curl "http://localhost:9000/api/process/current" | jq '.setpoints'

# Look for gradual changes in historian
curl "http://localhost:9000/api/history/trends?measurement=setpoint&start=-30d"
```

### Hypothesis 3: Dormant Backdoor

**Theory:** Attacker installed persistence during initial compromise and is waiting to activate.

**Evidence to Look For:**
- New scheduled tasks on HMI/engineering stations
- Modified startup scripts
- New network listeners
- Unexpected outbound connections

**Hunt Query:**
```bash
# Check for new network listeners
netstat -tlnp | grep -v ESTABLISHED

# Look for new scheduled tasks
crontab -l
ls -la /etc/cron.d/
```

### Hypothesis 4: Protocol Tunneling

**Theory:** Attacker is hiding malicious traffic inside legitimate OT protocol communications.

**Evidence to Look For:**
- Unusual data lengths in Modbus/DNP3 packets
- High entropy in protocol data fields
- Unexpected register read patterns
- Traffic to unusual destinations

**Hunt Query:**
```bash
# Analyze packet sizes for anomalies
vulnot-forensics analyze-pcap -p /evidence/network/modbus.pcap | grep -E "length|size"
```

---

## Part 3: Hands-On Hunting Exercise

### Scenario: Post-Incident Hunt

Three months ago, your organization detected and contained a Modbus-based attack. Management wants to know if the attacker might still have access.

### Hunting Tasks:

**Task 1: Network Persistence Check**
```bash
# Look for unusual network connections
vulnot-modbus scan --network 10.0.1.0/24 --port 502

# Check for new devices
diff baseline_assets.txt current_assets.txt
```

**Task 2: Process Data Analysis**
```bash
# Compare process trends to historical baseline
curl "http://localhost:9000/api/history/trends?start=-90d"

# Look for gradual deviations
python3 analyze_trends.py --detect-drift
```

**Task 3: Configuration Audit**
```bash
# Check PLC configurations against known-good
vulnot-s7 --target 10.0.3.10 info
vulnot-modbus read --target 10.0.1.10 --register 0 --count 200
```

**Task 4: Log Analysis**
```bash
# Search for suspicious patterns
vulnot-forensics analyze-logs -l /var/log/scada/*.log

# Look for off-hours activity
grep -E "0[0-6]:" /var/log/scada/*.log | grep -v "maintenance"
```

---

## Part 4: Hunting Toolkit

### Essential Tools for OT Hunting

| Tool | Purpose |
|------|---------|
| vulnot-forensics | Log and evidence analysis |
| vulnot-modbus | Modbus traffic analysis |
| vulnot-dnp3 | DNP3 traffic analysis |
| vulnot-s7 | S7comm traffic analysis |
| Wireshark | Deep packet inspection |
| tcpdump | Network capture |

### Hunting Queries

**Find all write operations:**
```bash
# Modbus writes in logs
grep -E "function_code.*(05|06|0F|10)" /var/log/modbus.log

# DNP3 controls
grep -E "direct_operate|select|operate" /var/log/dnp3.log
```

**Find unauthorized access:**
```bash
# New source IPs
awk '{print $1}' /var/log/access.log | sort | uniq -c | sort -rn

# Access outside business hours
grep -E " (0[0-5]|2[2-3]):" /var/log/access.log
```

**Find process anomalies:**
```bash
# Values outside normal range
curl "http://localhost:9000/api/process/current" | jq '.[] | select(.value > .max or .value < .min)'
```

---

## Part 5: Documenting Findings

### Hunt Report Template

```markdown
# Threat Hunt Report

**Hunt ID:** TH-2024-001
**Hypothesis:** [Your hypothesis]
**Date Range:** [Start] to [End]
**Analyst:** [Name]

## Executive Summary
[Brief summary of findings]

## Methodology
[Tools and techniques used]

## Data Sources
- Network captures: [list]
- Log files: [list]
- Process data: [list]

## Findings

### Finding 1: [Title]
- **Evidence:** [What you found]
- **Significance:** [Why it matters]
- **Confidence:** [High/Medium/Low]
- **Recommendation:** [What to do]

## Conclusion
[Overall assessment]

## Next Steps
[Follow-up actions]
```

---

## Part 6: Building a Hunting Program

### Quarterly Hunt Calendar

| Quarter | Focus Area | Hypotheses |
|---------|------------|------------|
| Q1 | Network persistence | Backdoors, tunneling |
| Q2 | Process manipulation | Gradual changes, setpoint drift |
| Q3 | Credential compromise | Unauthorized access, privilege escalation |
| Q4 | Supply chain | Vendor access, third-party compromise |

### Metrics to Track

- Hunts conducted per quarter
- Findings per hunt (true positive rate)
- Time to complete investigation
- Recommendations implemented
- Detection rule improvements

---

## Key Takeaways

1. **Proactive is better** - Don't wait for alerts to find threats
2. **Know your baseline** - You can't hunt without understanding normal
3. **Think like an attacker** - Use attack knowledge to form hypotheses
4. **Process data matters** - OT hunting requires process understanding
5. **Document everything** - Findings drive improvements

---

*This completes the SOC Defender training series. Continue building your skills with hands-on practice in the VULNOT environment.*

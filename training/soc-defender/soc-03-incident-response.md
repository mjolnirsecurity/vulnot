# SOC Defender Lab 03: Incident Response for OT Environments

## Overview

OT incident response requires balancing security concerns with safety and operational continuity. This lab teaches the unique aspects of responding to incidents in industrial control system environments.

## Learning Objectives

- Execute OT-specific incident response procedures
- Coordinate with plant operations during incidents
- Make containment decisions that prioritize safety
- Preserve evidence while maintaining operations

---

## Part 1: OT Incident Response Principles

### Key Differences from IT Incident Response

| IT Response | OT Response |
|-------------|-------------|
| Isolate first, ask questions later | Safety first, then containment |
| Reboot to clean state | Rebooting may cause process upset |
| Apply patches immediately | Patches require change management |
| Forensics can take time | Process may need to continue |
| Data confidentiality priority | Safety and availability priority |

### The OT IR Priority Order

1. **SAFETY** - Protect human life
2. **Environment** - Prevent environmental damage
3. **Equipment** - Prevent physical damage
4. **Production** - Maintain operations
5. **Data** - Preserve evidence

---

## Part 2: Incident Classification

### OT Incident Severity Levels

**CRITICAL (Immediate Response)**
- Safety system compromised
- Process in dangerous state
- Active attack causing physical impact
- Loss of control capability

**HIGH (15-minute Response)**
- Unauthorized write commands detected
- PLC program modified
- Remote access compromise
- Multiple systems affected

**MEDIUM (1-hour Response)**
- Reconnaissance activity detected
- Unauthorized network access
- Single system anomaly
- Process deviation (non-critical)

**LOW (4-hour Response)**
- Port scanning detected
- Minor configuration change
- Single failed login attempt
- Traffic anomaly (no impact)

---

## Part 3: Response Playbooks

### Playbook 1: Unauthorized PLC Write Detected

**Trigger:** Write command from unauthorized source

**Immediate Actions (0-5 minutes):**
```
1. [ ] Alert plant operator immediately
2. [ ] Document current process state
3. [ ] Verify what values were changed
4. [ ] Determine if process is in safe state
5. [ ] Block source IP at firewall (if safe to do so)
```

**Short-term Actions (5-30 minutes):**
```
1. [ ] Coordinate with operator to revert changes
2. [ ] Capture network traffic for evidence
3. [ ] Identify all affected PLCs
4. [ ] Check for persistence mechanisms
5. [ ] Assess impact on production
```

**Documentation:**
```
Incident ID: INC-2024-001
Time Detected: 14:25:33
Source IP: 10.0.1.200
Target: Water PLC (10.0.1.10)
Action: Modbus Write to Register 150
Value Changed: 2.0 → 25.0 (Chlorine setpoint)
Impact: Critical safety parameter modified
Status: Contained
```

### Playbook 2: Ransomware on IT/OT Boundary

**Trigger:** Ransomware detected on DMZ systems

**Immediate Actions:**
```
1. [ ] Verify OT systems are isolated
2. [ ] Check IT/OT firewall rules
3. [ ] Confirm no ransomware traffic crossed to OT
4. [ ] Alert OT operations team
5. [ ] Prepare for potential manual operations
```

**Containment Decision Tree:**
```
Can OT operate independently?
├── YES → Isolate IT, continue OT operations
└── NO → Evaluate manual operation capability
         ├── YES → Switch to manual, isolate IT
         └── NO → Controlled shutdown may be needed
```

### Playbook 3: Safety System Compromise (TRITON-style)

**Trigger:** Safety instrumented system shows anomalies

**Immediate Actions (CRITICAL):**
```
1. [ ] Notify plant manager IMMEDIATELY
2. [ ] Do NOT trust safety system readings
3. [ ] Prepare for manual emergency shutdown
4. [ ] Isolate SIS from network
5. [ ] Physical inspection of process state
```

**Safety Decision:**
```
If SIS integrity cannot be verified:
→ Manual process shutdown until verified
→ Physical key switch to PROGRAM mode
→ Compare SIS program against known-good backup
→ Engage SIS vendor for assistance
```

---

## Part 4: Coordination Procedures

### Who to Contact

| Role | Contact Reason | Priority |
|------|----------------|----------|
| Shift Supervisor | Any OT incident | IMMEDIATE |
| Plant Manager | Critical incidents | 15 minutes |
| OT Engineer | Technical assessment | 30 minutes |
| IT Security | Forensics support | 1 hour |
| Vendor Support | System-specific help | As needed |
| Legal/Compliance | Regulatory incidents | 4 hours |
| Law Enforcement | Criminal activity | Per policy |

### Communication Template

**Initial Notification:**
```
PRIORITY: [CRITICAL/HIGH/MEDIUM]
INCIDENT: Unauthorized access to [system]
TIME: [HH:MM UTC]
IMPACT: [current/potential impact]
STATUS: [investigating/contained/ongoing]
ACTION NEEDED: [specific request]
NEXT UPDATE: [time]
```

**Update Template:**
```
INCIDENT UPDATE - INC-2024-001
TIME: [HH:MM UTC]
STATUS: [new status]
FINDINGS: [what we know now]
ACTIONS TAKEN: [what we did]
NEXT STEPS: [what's planned]
ETA TO RESOLUTION: [estimate]
```

---

## Part 5: Evidence Preservation

### What to Capture

**Network Evidence:**
```bash
# Capture ongoing traffic
tcpdump -i eth0 -w incident_capture.pcap

# Save firewall logs
cp /var/log/firewall.log /evidence/

# Export flow data
netflow export > /evidence/flows.csv
```

**System Evidence:**
```bash
# PLC diagnostics
vulnot-forensics collect -e /evidence/plc

# Historian data
curl "http://localhost:9000/api/history/trends?start=-24h" > /evidence/history.json

# HMI logs
cp /var/log/scada/*.log /evidence/scada/
```

**Process Evidence:**
```bash
# Current values snapshot
vulnot-modbus read --target 10.0.1.10 --register 0 --count 200 > /evidence/plc_state.txt

# Screenshot HMI
scrot /evidence/hmi_screenshot.png
```

### Evidence Chain of Custody

```
EVIDENCE LOG
============
Item: Network capture (incident_capture.pcap)
Hash: SHA256: a1b2c3d4...
Collected by: SOC Analyst (badge #12345)
Date/Time: 2024-01-15 14:45:00 UTC
Storage: /evidence/network/
```

---

## Part 6: Recovery Procedures

### Verification Before Restart

**Checklist:**
```
[ ] All affected systems identified
[ ] Attack vector determined and blocked
[ ] Malware/backdoors removed
[ ] PLC programs verified against known-good
[ ] Setpoints verified against engineering specs
[ ] Network traffic verified normal
[ ] Operator confirms safe to restart
[ ] Management approval obtained
```

### Phased Restart

```
Phase 1: Verify isolated systems
├── Confirm no active attacker presence
├── Verify network segmentation
└── Test security controls

Phase 2: Restore monitoring
├── SCADA connectivity
├── Historian logging
└── Alert systems

Phase 3: Reconnect PLCs
├── One system at a time
├── Verify behavior at each step
└── Monitor for anomalies

Phase 4: Return to production
├── Gradual increase in load
├── Enhanced monitoring period
└── Document lessons learned
```

---

## Part 7: Hands-On Exercise

### Scenario: Active Attack Response

You receive alerts indicating an active attack on the water treatment plant:

**14:25** - New IP detected on OT network (10.0.1.200)
**14:26** - High-volume Modbus reads from 10.0.1.200
**14:27** - Modbus write: Chlorine setpoint → 25.0 ppm
**14:28** - Operator calls: "Something's wrong with the chlorine!"

### Exercise Tasks:

**1. Immediate Response (2 minutes)**
- What's your first action?
- Who do you contact?
- What do you tell them?

**2. Containment (5 minutes)**
- How do you stop the attack?
- What's the risk of blocking the IP?
- What if the attacker is using the HMI?

**3. Assessment (10 minutes)**
- What evidence do you collect?
- How do you verify current process state?
- What other systems might be affected?

**4. Recovery (15 minutes)**
- How do you restore safe operation?
- What verification steps are needed?
- When is it safe to return to normal?

### Expected Response Timeline:

| Time | Action |
|------|--------|
| 14:28:30 | Acknowledge alert, notify operator |
| 14:29:00 | Verify process state with operator |
| 14:30:00 | Block 10.0.1.200 at firewall |
| 14:31:00 | Operator reverts chlorine setpoint |
| 14:32:00 | Start evidence collection |
| 14:35:00 | Verify no other changes made |
| 14:40:00 | Confirm process stable |
| 14:45:00 | Initial incident report |
| 15:00:00 | Detailed investigation begins |

---

## Post-Incident Activities

### After Action Review

Questions to answer:
1. How did the attacker gain access?
2. What was the attack objective?
3. How long were they in the network?
4. What detection gaps existed?
5. What could we have done differently?

### Improvement Actions

- [ ] Update detection rules based on IOCs
- [ ] Review network segmentation
- [ ] Enhance monitoring coverage
- [ ] Update response playbooks
- [ ] Conduct additional training

---

## Key Takeaways

1. **Safety always comes first** - Don't make the situation worse
2. **Work with operations** - They know the process best
3. **Preserve evidence carefully** - But not at expense of safety
4. **Communicate clearly** - Keep stakeholders informed
5. **Document everything** - You'll need it for the report

---

*Continue to SOC-04: Threat Hunting in OT Environments*

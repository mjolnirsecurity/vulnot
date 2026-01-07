# Forensics Lab 04: Colonial Pipeline Ransomware Investigation

## Background: The Real Colonial Pipeline Attack (2021)

On May 7, 2021, Colonial Pipeline—operator of the largest refined petroleum pipeline in the United States—was hit by a ransomware attack that forced the company to halt all pipeline operations for six days. The attack caused fuel shortages across the southeastern United States.

### How the Attack Happened

1. **Initial Access**: Compromised VPN credentials (no MFA)
2. **Ransomware Deployment**: DarkSide ransomware on IT systems
3. **Business Decision**: Shut down OT systems to prevent spread
4. **Ransom Paid**: $4.4 million in Bitcoin (partially recovered by FBI)
5. **Recovery**: Six days to resume operations

### Real-World Impact
- 5,500 miles of pipeline shut down
- Fuel shortages in 17 states
- Panic buying and price spikes
- National emergency declared
- $4.4 million ransom paid

---

## Lab Scenario

A petroleum distribution company detected ransomware on several IT servers. Before the ransomware spread further, the SOC team shut down connections between IT and OT networks. However, they are unsure if the OT environment was compromised. Pipeline operations have been manually switched to local control.

**Your Mission**: Determine if OT systems were compromised and assess readiness for restart.

## Lab Environment

- **IT Systems**: Simulated compromised servers
- **OT Systems**: vulnot process simulators
- **Evidence**: Pre-staged ransomware artifacts and logs

## Investigation Steps

### Step 1: Scope Assessment

Access the investigation workstation:

```bash
docker exec -it vulnot-redteam bash
```

Determine which systems show signs of compromise:

```bash
vulnot-forensics collect -e /evidence
```

### Step 2: IT/OT Boundary Analysis

Examine firewall logs for any traffic that crossed the IT/OT boundary:

```bash
vulnot-forensics analyze-logs -l /evidence/logs/firewall_dmz.log
```

**Critical questions:**
- Did any ransomware traffic reach OT networks?
- Were there lateral movement attempts into OT?
- Were OT credentials potentially exposed?

### Step 3: Ransomware Analysis

Identify the ransomware variant and its capabilities:

```bash
# Examine ransomware artifacts
cat /evidence/malware/ransom_note.txt
```

**DarkSide characteristics:**
- Double extortion (encrypt + data theft)
- Windows-focused (not PLC-specific)
- RaaS (Ransomware-as-a-Service) model

### Step 4: OT System Verification

Check OT systems for integrity:

```bash
# Verify PLC connectivity and state
vulnot-modbus scan --network 10.0.1.0/24 --port 502

# Check for unexpected changes
vulnot-modbus read --target 10.0.1.10 --register 0 --count 100
```

### Step 5: Restart Readiness Assessment

Verify OT systems are safe to restart:

```bash
vulnot-forensics iocs
```

## Expected Findings

### IT Compromise Scope
| System | Status | Evidence |
|--------|--------|----------|
| AD-SERVER-01 | Encrypted | Ransom note found |
| FILE-SERVER-02 | Encrypted | Ransom note found |
| SCADA-SERVER-01 | Clean | No artifacts |
| HISTORIAN-01 | Clean | No artifacts |
| HMI-01 | Clean | No artifacts |

### IT/OT Boundary Analysis
| Finding | Significance |
|---------|-------------|
| No ransomware traffic to OT | OT networks isolated |
| VPN credentials harvested | Could access OT VPN |
| No lateral movement to OT | Proactive shutdown worked |

### OT System Status
| System | Status | Recommendation |
|--------|--------|----------------|
| Pipeline PLC-001 | Normal | Clear to restart |
| Pipeline PLC-002 | Normal | Clear to restart |
| Valve Controller | Normal | Clear to restart |
| Flow Meters | Normal | Clear to restart |

## Colonial Pipeline Timeline

| Date | Event |
|------|-------|
| April 29 | Attackers gain VPN access with stolen credentials |
| May 6 | Data exfiltration begins |
| May 7 06:00 | Ransomware deployed, IT systems encrypted |
| May 7 06:30 | Colonial detects attack, shuts down pipeline |
| May 7 12:00 | DarkSide claims responsibility |
| May 8 | FBI and CISA engaged |
| May 9 | National emergency declared |
| May 10 | Colonial pays $4.4M ransom |
| May 12 | Pipeline restart begins |
| May 15 | Normal operations resume |
| June 7 | FBI recovers $2.3M of ransom |

## Lessons Learned

### Why OT Was Shut Down (Even Though It Wasn't Hit)
1. **Uncertainty** - Couldn't confirm OT was clean
2. **Shared Systems** - Billing systems were down (can't measure product)
3. **Safety** - Better to be safe than sorry
4. **Visibility** - Limited OT security monitoring

### What Should Have Been Different
1. **MFA on VPN** - Would have prevented initial access
2. **Network Segmentation** - Clear IT/OT boundaries
3. **OT Visibility** - Better monitoring to confirm OT status
4. **Incident Response Plan** - Pre-planned OT isolation procedures

## Forensic Report

Generate your investigation report:

```bash
vulnot-forensics report -e /evidence -o colonial_investigation.md
```

## Defense Recommendations

1. **Multi-Factor Authentication** - On all remote access
2. **Network Segmentation** - Strict IT/OT separation
3. **OT Monitoring** - Independent visibility into OT networks
4. **Offline Backups** - Air-gapped backups for critical systems
5. **Incident Response Plan** - OT-specific playbooks
6. **Manual Operations** - Train operators for manual control

## Key Takeaways

1. **Ransomware doesn't have to hit OT to impact operations**
2. **IT dependencies can force OT shutdowns**
3. **Visibility gaps cause conservative responses**
4. **Basic hygiene (MFA) prevents sophisticated attacks**
5. **Business continuity planning is essential**

---

*This lab is based on publicly available information about the Colonial Pipeline attack. It is intended for educational purposes in understanding the relationship between IT and OT security.*

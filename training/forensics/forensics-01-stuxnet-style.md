# Forensics Lab 01: Stuxnet-Style PLC Attack Investigation

## Background: The Real Stuxnet Attack (2010)

Stuxnet was a sophisticated cyber weapon jointly developed by the US NSA and Israeli Mossad to sabotage Iran's nuclear enrichment program at the Natanz facility. It remains one of the most significant ICS attacks in history.

### How Stuxnet Worked

1. **Initial Infection**: Spread via USB drives to air-gapped networks
2. **Target Identification**: Only activated on systems with Siemens S7-300/S7-400 PLCs
3. **Payload Delivery**: Injected malicious code into PLC program blocks
4. **Sabotage**: Modified centrifuge motor speeds (2Hz to 1,410Hz) while reporting normal values
5. **Stealth**: Used rootkits and stolen digital certificates to avoid detection

### Real-World Impact
- Destroyed approximately 1,000 centrifuges
- Set Iran's nuclear program back 2 years
- Cost estimated at $10 million in damages

---

## Lab Scenario

A chemical processing facility has experienced unusual equipment failures. Multiple variable frequency drives (VFDs) controlling critical mixers have failed over the past week. Maintenance initially blamed mechanical issues, but a security consultant noticed suspicious patterns.

**Your Mission**: Investigate if this is a Stuxnet-style cyber attack.

## Lab Environment

- **Target**: vulnot-factory-plc (S7comm on 10.0.3.10:102)
- **Attacker**: vulnot-attacker-factory container
- **Evidence**: Pre-staged artifacts simulating an ongoing attack

## Investigation Steps

### Step 1: Initial Triage

Access the investigation workstation:

```bash
docker exec -it vulnot-redteam bash
```

Review the initial incident report:

```bash
vulnot-forensics iocs
```

### Step 2: Network Traffic Analysis

Examine captured network traffic for S7comm anomalies:

```bash
vulnot-forensics analyze-pcap -p /evidence/network/s7comm_capture.pcap
```

**What to look for:**
- Unusual S7comm function codes (0x28 = Download, 0x29 = Upload)
- Program block transfers (OB1, FC, FB blocks)
- Connections from unauthorized IP addresses
- High-frequency read/write operations

### Step 3: PLC Program Analysis

Extract and compare the current PLC program with known-good backup:

```bash
vulnot-s7 --target 10.0.3.10 read --db 1
```

**Indicators of Compromise:**
- Modified Organization Blocks (OB1, OB35)
- New or modified Function Blocks
- Changes to timer/counter configurations
- Hidden data blocks with malicious logic

### Step 4: Memory Dump Analysis

Analyze the PLC memory for injected code:

```bash
vulnot-forensics analyze-memory -m /evidence/memory/plc_memory.bin
```

**Stuxnet-like patterns:**
- Code in unexpected memory regions
- Modified I/O image tables
- Altered setpoint values vs. reported values

### Step 5: Timeline Reconstruction

Build an attack timeline from all evidence sources:

```bash
vulnot-forensics analyze-logs -l /evidence/logs/plc_diagnostic.log
```

## Expected Findings

### Network IOCs
| Indicator | Significance |
|-----------|-------------|
| S7comm block download from 10.0.3.100 | Unauthorized program modification |
| Rapid PLC connections (>50/min) | Reconnaissance activity |
| OB35 (cyclic interrupt) modification | Timer-based payload trigger |

### Host IOCs
| Indicator | Significance |
|-----------|-------------|
| New FC block (FC100) | Malicious function block |
| Modified DB values | Setpoint manipulation |
| Diagnostic buffer cleared | Anti-forensics activity |

### Attack Timeline
| Time | Event |
|------|-------|
| T-7 days | Initial S7comm scanning |
| T-5 days | PLC program downloaded |
| T-3 days | Modified program uploaded |
| T-1 day | Payload activated (OB35 trigger) |
| T+0 | Equipment failures observed |

## Forensic Report Template

Generate a comprehensive report:

```bash
vulnot-forensics report -e /evidence -o stuxnet_investigation.md
```

## Key Lessons from Stuxnet

1. **Air gaps are not sufficient** - USB drives can bridge isolated networks
2. **PLCs can be weaponized** - Attackers can inject malicious logic into controllers
3. **Stealth is critical** - Stuxnet reported normal values while causing damage
4. **Supply chain matters** - Stolen certificates enabled trust bypass
5. **Targeted attacks require specific knowledge** - Attackers knew exact centrifuge configurations

## Real-World Investigation Resources

- [Langner's Stuxnet Deep Dive](https://www.langner.com/to-kill-a-centrifuge/)
- [IEEE Spectrum: The Real Story of Stuxnet](https://spectrum.ieee.org/the-real-story-of-stuxnet)
- [ICS-CERT Advisory](https://www.cisa.gov/uscert/ics)

## Defense Recommendations

Based on your investigation, recommend mitigations:

1. **Network Segmentation**: Isolate PLC networks from general OT
2. **Program Integrity Monitoring**: Hash and monitor PLC programs
3. **USB Controls**: Disable or monitor removable media
4. **Behavioral Monitoring**: Alert on unusual PLC communication patterns
5. **Regular Backups**: Maintain verified PLC program backups

---

*This lab is based on publicly available information about the Stuxnet attack. It is intended for educational purposes in understanding ICS forensics.*

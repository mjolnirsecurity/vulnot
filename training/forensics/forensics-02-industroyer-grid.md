# Forensics Lab 02: Industroyer/CrashOverride Power Grid Attack Investigation

## Background: The Real Industroyer Attack (2016)

On December 17, 2016, the Ukrainian capital Kyiv experienced a power outage affecting one-fifth of the city's power consumption. The attack targeted the Pivnichna (North) 330kV substation and was attributed to the Russian Sandworm Team.

### How Industroyer Worked

1. **Modular Design**: Main backdoor, launcher, data wiper, and protocol payloads
2. **Protocol Knowledge**: Native IEC 60870-5-101/104, IEC 61850, and OPC DA
3. **Attack Execution**: Launcher triggered payloads at specific times (Dec 17 & 20)
4. **Circuit Breaker Control**: Directly commanded breakers open via native protocols
5. **Anti-Recovery**: Wiped files and attacked SIPROTEC relays to prevent restoration

### Real-World Impact
- 1-hour blackout affecting Kiev
- 330kV substation de-energized
- Protective relay DoS attack to prevent re-energization
- Proof of concept for larger attacks

---

## Lab Scenario

A regional electrical utility detected unusual DNP3 traffic patterns during an overnight period. The following morning, several circuit breakers at a distribution substation were found in the OPEN state, despite no maintenance scheduled. SCADA logs show the breakers were commanded open, but no operator was logged in.

**Your Mission**: Investigate potential grid-targeted malware similar to Industroyer.

## Lab Environment

- **Target**: vulnot-power-rtu (DNP3 on 10.0.2.10:20000)
- **Attacker**: vulnot-attacker-power container
- **Evidence**: Pre-staged artifacts simulating the attack

## Investigation Steps

### Step 1: SCADA Log Analysis

Access the investigation workstation:

```bash
docker exec -it vulnot-redteam bash
```

Analyze SCADA event logs for unauthorized commands:

```bash
vulnot-forensics analyze-logs -l /evidence/logs/scada_events.log
```

**What to look for:**
- DNP3 Direct Operate commands without preceding Select
- Commands during non-operational hours
- Breaker OPEN commands from non-operator stations
- Unusual polling patterns

### Step 2: DNP3 Traffic Analysis

Examine captured DNP3 traffic:

```bash
vulnot-forensics analyze-pcap -p /evidence/network/dnp3_capture.pcap
```

**Industroyer-like patterns:**
- Function Code 0x04 (Direct Operate) without 0x03 (Select)
- Function Code 0x0D (Cold Restart) commands
- Unusual master addresses
- Data link layer anomalies

### Step 3: RTU Investigation

Query the RTU for current state and diagnostics:

```bash
vulnot-dnp3 read --target 10.0.2.10 --port 20000 --address 10
```

Check breaker status:
- BI-0 through BI-7 (Binary Inputs = breaker status)
- Identify which breakers were tripped

### Step 4: Malware Artifact Search

Industroyer used specific file artifacts. Search for similar patterns:

```bash
# Look for launcher artifacts (specific timestamps)
vulnot-forensics collect -e /evidence
```

**Key Industroyer artifacts:**
- Launcher with hardcoded activation times
- Protocol-specific DLLs (*.dll)
- Configuration files with target IPs/addresses
- Data wiper components

### Step 5: Protective Relay Analysis

Industroyer included a Siemens SIPROTEC DoS attack. Check relay status:

```bash
# Check if protective relays are responsive
vulnot-dnp3 read --target 10.0.2.10 --port 20000 --address 10
```

**SIPROTEC CVE-2015-5374 indicators:**
- Relays unresponsive to commands
- Relays stuck in "maintenance mode"
- UDP port 50000 traffic

## Expected Findings

### DNP3 Traffic IOCs
| Indicator | Significance |
|-----------|-------------|
| Direct Operate without Select | Malware behavior (skips safety) |
| Cold Restart command | Attempt to disrupt RTU |
| Unknown master address | Unauthorized control source |
| Rapid polling followed by commands | Reconnaissance + attack pattern |

### Timing Analysis
| Time | Event |
|------|-------|
| 23:45:00 | Initial connection from 10.0.2.100 |
| 23:47:30 | DNP3 class scan (reconnaissance) |
| 23:50:00 | Binary output point enumeration |
| 23:55:00 | First Direct Operate (Breaker 52-1) |
| 23:55:05 | Direct Operate (Breaker 52-2) |
| 23:55:10 | Direct Operate (Breaker 52-3) |
| 23:58:00 | SIPROTEC DoS packet sent |
| 00:00:00 | Data wiper executed |

### Malware Components Found
| Component | Purpose |
|-----------|---------|
| launcher.exe | Time-based payload activation |
| 101.dll | IEC 101 protocol handler |
| 104.dll | IEC 104 protocol handler |
| 61850.dll | IEC 61850 protocol handler |
| OPCClientDemo.dll | OPC DA client |
| haslo.dat | Configuration file |

## Attack Chain Reconstruction

```
[Initial Access] → [Lateral Movement] → [Payload Staging] → [Execution]
      ↓                    ↓                    ↓               ↓
   Spearphish         Credential          Install on        Launcher
   or VPN             harvesting          HMI/Eng           activates
                                          station           at 23:55
                                                               ↓
                                                     [Direct Operate]
                                                           ↓
                                                    [Breakers OPEN]
                                                           ↓
                                                    [SIPROTEC DoS]
                                                           ↓
                                                    [Data Wiper]
```

## Forensic Report

Generate your investigation report:

```bash
vulnot-forensics report -e /evidence -o industroyer_investigation.md
```

## Key Lessons from Industroyer

1. **Protocol knowledge is weaponized** - Attackers understand grid protocols intimately
2. **Time-based triggers** - Malware can wait for optimal attack windows
3. **Multi-protocol capability** - Single malware supports multiple grid protocols
4. **Anti-recovery tactics** - Protective relay attacks prevent quick restoration
5. **Proof of concept** - 2016 attack was likely testing for larger operations

## Real-World Investigation Resources

- [Dragos CRASHOVERRIDE Analysis](https://www.dragos.com/resources/whitepaper/crashoverride-analyzing-the-malware-that-attacks-power-grids/)
- [MITRE ATT&CK Campaign C0025](https://attack.mitre.org/campaigns/C0025/)
- [ESET Industroyer Analysis](https://www.welivesecurity.com/2017/06/12/industroyer-biggest-threat-industrial-control-systems-since-stuxnet/)

## Defense Recommendations

1. **DNP3 Secure Authentication** - Implement SA to prevent unauthorized commands
2. **Command Verification** - Require Select-Before-Operate (SBO) sequence
3. **Time Synchronization** - Monitor for systems with manipulated clocks
4. **Protective Relay Patching** - Apply SIPROTEC firmware updates
5. **Network Segmentation** - Isolate substations from corporate network
6. **Incident Response Plan** - Manual switching procedures for cyber events

---

*This lab is based on publicly available information about the Industroyer/CrashOverride attack. It is intended for educational purposes in understanding ICS forensics.*

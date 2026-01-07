# Forensics Lab 03: TRITON/TRISIS Safety System Attack Investigation

## Background: The Real TRITON Attack (2017)

TRITON (also known as TRISIS or HatMan) was discovered at a Saudi Arabian petrochemical plant in 2017. It is considered "the world's most murderous malware" because it specifically targeted Safety Instrumented Systems (SIS) - the last line of defense preventing catastrophic industrial accidents.

### How TRITON Worked

1. **Initial Access**: Compromised IT network, moved laterally to OT
2. **Engineering Station Compromise**: Infected Triconex engineering workstation
3. **PLC Exploitation**: Used zero-day to inject code into Triconex SIS controllers
4. **Payload**: Installed backdoor (imain.bin) to disable safety functions
5. **Intent**: Allow unsafe conditions to persist during a future attack

### Real-World Impact
- Safety systems triggered twice before discovery (false positive)
- Could have enabled release of toxic H2S gas
- Could have caused explosions with mass casualties
- Attributed to Russian government (TsNIIKhM)

---

## Lab Scenario

A chemical reactor facility experienced two unexpected safety system trips in the past month. Each time, the Triconex SIS put the plant into a safe state, but operators found no actual unsafe conditions. The plant's cybersecurity team discovered unusual files on the SIS engineering workstation.

**Your Mission**: Investigate a potential TRITON-style attack on the safety systems.

## Lab Environment

- **Target**: vulnot-reactor-opcua (OPC UA on 10.0.4.10:4840)
- **Simulated SIS**: Safety logic integrated with reactor simulation
- **Evidence**: Pre-staged artifacts mimicking TRITON infection

## Investigation Steps

### Step 1: Engineering Workstation Analysis

Access the investigation workstation:

```bash
docker exec -it vulnot-redteam bash
```

Examine the SIS engineering workstation for artifacts:

```bash
vulnot-forensics collect -e /evidence
```

**TRITON artifacts to look for:**
- trilog.exe (dropper)
- library.zip (payload container)
- imain.bin (backdoor binary)
- inject.bin (exploitation code)

### Step 2: Network Traffic Analysis

Analyze communication between engineering station and SIS:

```bash
vulnot-forensics analyze-pcap -p /evidence/network/sis_traffic.pcap
```

**What to look for:**
- TriStation protocol traffic (proprietary Schneider Electric)
- Program downloads to SIS controller
- Unusual connection patterns
- Memory read/write operations

### Step 3: SIS Controller Investigation

Examine the SIS controller state via OPC UA interface:

```bash
vulnot-opcua browse --target 10.0.4.10 --port 4840
```

**Safety system indicators:**
- Modified safety logic blocks
- Changed trip setpoints
- Disabled alarm functions
- New user-defined functions

### Step 4: Memory Analysis

Analyze SIS controller memory dump for injected code:

```bash
vulnot-forensics analyze-memory -m /evidence/memory/sis_memory.bin
```

**TRITON backdoor characteristics:**
- Code in TRICONEX main processor memory
- Modified system calls
- RAT (Remote Access Trojan) functionality
- Capability to read/write/execute arbitrary code

### Step 5: Attack Chain Reconstruction

Build the complete attack timeline:

```bash
vulnot-forensics analyze-logs -l /evidence/logs/sis_diagnostic.log
```

## Expected Findings

### File System Artifacts
| File | Location | Purpose |
|------|----------|---------|
| trilog.exe | C:\Windows\Temp\ | Main dropper |
| library.zip | C:\Users\Engineer\AppData\ | Payload container |
| imain.bin | (embedded) | SIS backdoor |
| inject.bin | (embedded) | Zero-day exploit |

### Network IOCs
| Indicator | Significance |
|-----------|-------------|
| TriStation connections from workstation | Normal (engineering) |
| TriStation connections from 10.0.4.100 | Unauthorized (attacker) |
| Extended memory read operations | Reconnaissance |
| Program download outside change window | Suspicious |

### SIS Controller State
| Finding | Significance |
|---------|-------------|
| New function block (FB_MAIN_RAT) | Backdoor installed |
| Modified trip setpoint (reactor temp) | Safety margin reduced |
| Disabled H2S alarm | Critical safety compromise |
| Added network listener | Remote access capability |

## Attack Timeline

| Time | Event |
|------|-------|
| T-60 days | IT network compromised via spearphish |
| T-45 days | Lateral movement to OT network |
| T-30 days | Engineering workstation compromised |
| T-14 days | SIS reconnaissance (memory reads) |
| T-7 days | First payload attempt (caused trip) |
| T-3 days | Modified payload uploaded |
| T-1 day | Second trip (bug in exploit code) |
| T+0 | Investigation triggered |

## Attack Vector Analysis

```
[Spearphish] → [IT Foothold] → [Lateral Movement] → [OT Access]
                                                         ↓
                                              [Eng Workstation]
                                                         ↓
                                              [SIS Reconnaissance]
                                                         ↓
                                              [Exploit Development]
                                                         ↓
                                              [Payload Injection]
                                                         ↓
                                              [Backdoor Active]
```

## Why TRITON is "Murderous"

Safety systems exist to prevent catastrophic events:
- **Reactor overpressure** → Explosion
- **H2S release** → Toxic exposure (lethal)
- **Thermal runaway** → Fire, explosion
- **Loss of containment** → Environmental disaster

By disabling safety systems, attackers could:
1. Wait for an unsafe condition to develop naturally
2. Actively cause an unsafe condition via parallel attack
3. Allow the process to enter dangerous states

## Forensic Report

Generate comprehensive report:

```bash
vulnot-forensics report -e /evidence -o triton_investigation.md
```

## Key Lessons from TRITON

1. **Safety systems are targets** - Attackers understand SIS value
2. **Multiple attempts needed** - First payload caused safety trip (bug)
3. **Long dwell time** - Attackers spent months in network
4. **Specialized knowledge** - Required Triconex expertise
5. **Physical consequences** - Cyber attack → potential loss of life

## Real-World Investigation Resources

- [FireEye TRITON Analysis](https://www.mandiant.com/resources/blog/attackers-deploy-new-ics-attack-framework-triton)
- [Dragos TRISIS Report](https://www.dragos.com/resource/trisis/)
- [FBI PIN on TRITON](https://www.ic3.gov/CSA/2022/220325.pdf)
- [Midnight Blue Technical Analysis](https://www.midnightblue.nl/blog/analyzing-the-triton-industrial-malware)

## Defense Recommendations

1. **Physical Key Switch** - Require physical key to modify SIS program
2. **SIS Isolation** - Strict network segmentation for safety systems
3. **Change Detection** - Hash and monitor SIS program integrity
4. **Vendor Coordination** - Apply Schneider security patches
5. **Dual Engineering Stations** - Air-gapped backup for recovery
6. **Safety System Testing** - Regular proof tests with witnesses

---

*This lab is based on publicly available information about the TRITON/TRISIS attack. It is intended for educational purposes in understanding ICS forensics and the critical importance of safety system security.*

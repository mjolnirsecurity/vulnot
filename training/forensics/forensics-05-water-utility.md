# Forensics Lab 05: Water Treatment Facility Attack Investigation

## Background: Water Utility Attacks (2021-2024)

Multiple water treatment facilities have been targeted by cyber attackers, including the high-profile Oldsmar, Florida incident (2021) and subsequent attacks on water utilities by Iran-linked "Cyber Av3ngers" (2023-2024).

### Notable Incidents

**Oldsmar, Florida (Feb 2021)**
- Attacker remotely accessed HMI via TeamViewer
- Attempted to increase sodium hydroxide (lye) from 100ppm to 11,100ppm
- Operator noticed and reversed the change immediately
- Investigation later questioned whether it was external or insider

**Aliquippa, Pennsylvania (Nov 2023)**
- Iran-linked "Cyber Av3ngers" compromised Unitronics PLCs
- Displayed anti-Israel message on HMI
- Forced facility to manual operations
- Part of broader campaign against exposed PLCs

**Arkansas City, Kansas (Sept 2024)**
- Cybersecurity issue forced manual operations
- Similar pattern to other water utility attacks

---

## Lab Scenario

Your municipal water treatment facility received an alert from a vigilant operator who noticed the cursor moving on the HMI screen without anyone at the console. They observed someone attempting to change the chlorine dosing setpoint from 2.0 ppm to 200 ppm. The operator immediately disconnected the computer from the network.

**Your Mission**: Investigate the incident and determine if any process changes were made.

## Lab Environment

- **Target**: vulnot-water-plc (Modbus on 10.0.1.10:502)
- **HMI**: Dashboard at http://localhost:8080
- **Attacker**: vulnot-attacker-water container

## Investigation Steps

### Step 1: Immediate Response

Access the investigation workstation:

```bash
docker exec -it vulnot-redteam bash
```

Document the current process state:

```bash
# Read current setpoints and process values
vulnot-modbus read --target 10.0.1.10 --register 0 --count 50

# Check for any alarms
curl http://localhost:9000/api/alarms
```

### Step 2: HMI Forensics

Examine the compromised HMI workstation for remote access artifacts:

```bash
vulnot-forensics collect -e /evidence
```

**Remote access indicators:**
- TeamViewer logs
- AnyDesk artifacts
- VNC connections
- RDP sessions
- Browser-based remote access

### Step 3: Network Analysis

Analyze network traffic for unauthorized access:

```bash
vulnot-forensics analyze-pcap -p /evidence/network/hmi_traffic.pcap
```

**What to look for:**
- External IP connections to HMI
- Modbus write commands from HMI
- Unusual time-of-day activity
- Connection to known C2 infrastructure

### Step 4: Modbus Traffic Analysis

Examine Modbus traffic for unauthorized writes:

```bash
vulnot-forensics analyze-pcap -p /evidence/network/modbus_capture.pcap
```

**Critical Modbus function codes:**
- 0x05 (Force Single Coil) - Pump/valve control
- 0x06 (Write Single Register) - Setpoint changes
- 0x0F (Force Multiple Coils) - Batch changes
- 0x10 (Write Multiple Registers) - Batch changes

### Step 5: Process Data Verification

Compare historian data with expected values:

```bash
# Query historical setpoint values
curl "http://localhost:9000/api/history/trends?measurement=water_quality&start=-24h"
```

**Verify:**
- Chlorine dosing setpoint history
- pH adjustment history
- Chemical feed rates
- Any values outside normal range

## Expected Findings

### Remote Access Analysis
| Finding | Evidence Location |
|---------|-------------------|
| TeamViewer installed | C:\Program Files\TeamViewer |
| Last connection: 10.45.33.101 | TeamViewer logs |
| Connection time: 02:34 AM | Outside operational hours |
| Session duration: 4 minutes | Quick attack attempt |

### Modbus Traffic IOCs
| Time | Function | Register | Value | Description |
|------|----------|----------|-------|-------------|
| 02:34:15 | Read | 0-100 | - | Reconnaissance |
| 02:35:30 | Read | 100-200 | - | More recon |
| 02:36:45 | Write | 150 | 20000 | Chlorine SP (BLOCKED) |
| 02:36:48 | Write | 150 | 20000 | Retry (BLOCKED) |
| 02:37:00 | Disconnect | - | - | Operator intervention |

### Process Impact Assessment
| Parameter | Normal Range | Current | Status |
|-----------|--------------|---------|--------|
| Chlorine Dose | 1.5-3.0 ppm | 2.0 ppm | ✓ Normal |
| pH | 6.8-7.4 | 7.2 | ✓ Normal |
| Turbidity | <1 NTU | 0.5 NTU | ✓ Normal |
| Fluoride | 0.7 ppm | 0.7 ppm | ✓ Normal |

## Attack Timeline Reconstruction

| Time | Event |
|------|-------|
| 02:30 AM | Attacker initiates TeamViewer connection |
| 02:34 AM | Connection established to HMI |
| 02:35 AM | Attacker navigates to chemical control screen |
| 02:36 AM | Attacker attempts to modify chlorine setpoint |
| 02:37 AM | Operator notices cursor movement |
| 02:37 AM | Operator disconnects network cable |
| 02:38 AM | Attacker connection lost |
| 02:40 AM | Operator notifies supervisor |
| 03:00 AM | Security team engaged |

## Why This Attack (Almost) Worked

1. **Remote Access Enabled** - TeamViewer allowed external connections
2. **No MFA** - Single password for remote access
3. **Default Credentials** - Easy password on TeamViewer
4. **Flat Network** - HMI directly connected to PLC
5. **Overnight Attack** - Fewer staff to notice
6. **No Modbus Authentication** - PLC accepts any commands

## What Saved the Plant

1. **Vigilant Operator** - Noticed cursor movement
2. **Quick Thinking** - Disconnected network immediately
3. **Process Limits** - Physical safety systems as backup
4. **No Damage** - Attack interrupted before completion

## Forensic Report

Generate your report:

```bash
vulnot-forensics report -e /evidence -o water_investigation.md
```

## Defense Recommendations

### Immediate Actions
1. **Disable Remote Access** - Remove TeamViewer/AnyDesk from HMIs
2. **Network Segmentation** - Isolate HMIs from internet
3. **Change All Passwords** - Especially default credentials
4. **Enable MFA** - On any remote access that must remain

### Long-Term Improvements
1. **Jump Servers** - Require authenticated jump for OT access
2. **VPN with MFA** - If remote access is needed
3. **Network Monitoring** - Alert on Modbus write commands
4. **Physical Limits** - Configure PLCs to reject unsafe values
5. **Security Awareness** - Train operators to recognize attacks

## Unitronics-Specific IOCs (Cyber Av3ngers)

For Unitronics PLC attacks:
- Default credentials: 1111
- Port: 20256 (PCOM protocol)
- HMI defacement with political messages
- Vision Series PLCs targeted

---

*This lab is based on publicly available information about water utility attacks. It is intended for educational purposes in understanding the importance of securing critical water infrastructure.*

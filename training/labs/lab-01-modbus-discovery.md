# Lab 1: Modbus Discovery and Enumeration

## Objective
Learn to discover and enumerate Modbus devices on an OT network using various tools and techniques.

## Prerequisites
- VULNOT platform running (`./vulnot.sh start`)
- Access to the attacker workstation

## Scenario
You have been hired to perform a security assessment of a municipal water treatment facility. Your first task is to identify all Modbus-enabled devices on the OT network segment.

## Time: 30 minutes

---

## Part 1: Network Discovery (10 minutes)

### Task 1.1: Connect to Attacker Workstation

```bash
docker exec -it vulnot-attacker-water bash
```

You should see the VULNOT banner with target information.

### Task 1.2: Basic Network Scan

Use nmap to discover live hosts on the OT network:

```bash
nmap -sn 10.0.1.0/24
```

**Question 1:** How many hosts did you discover?

### Task 1.3: Modbus Port Scan

Scan for Modbus (port 502) specifically:

```bash
nmap -p 502 -sV 10.0.1.0/24
```

**Question 2:** Which IP addresses have port 502 open?

---

## Part 2: Modbus Device Identification (10 minutes)

### Task 2.1: Use VULNOT Scanner

The VULNOT scanner is a purpose-built tool for discovering Modbus devices:

```bash
vulnot-scan
```

**Question 3:** What additional information does vulnot-scan provide compared to nmap?

### Task 2.2: Nmap Modbus Scripts

Use Nmap's Modbus discovery script:

```bash
nmap -p 502 --script modbus-discover 10.0.1.10
```

Try this on all three PLCs.

**Question 4:** What Unit IDs are the PLCs configured with?

### Task 2.3: Device Identification

For each discovered device, use vulnot-read to identify it:

```bash
vulnot-read -t 10.0.1.10 -u 1
vulnot-read -t 10.0.1.11 -u 2
vulnot-read -t 10.0.1.12 -u 3
```

**Question 5:** What is the function of each PLC based on the register names?

---

## Part 3: Register Mapping (10 minutes)

### Task 3.1: Enumerate Holding Registers

Read holding registers from PLC-INTAKE:

```bash
vulnot-read -t 10.0.1.10 -u 1
```

Document the register addresses and their meanings.

### Task 3.2: Enumerate Coils

Read coil states:

```bash
vulnot-read -t 10.0.1.10 -u 1
```

**Question 6:** Which coils control pumps? What are their current states?

### Task 3.3: Traffic Analysis

In a new terminal, capture Modbus traffic:

```bash
watch-modbus
```

In the original terminal, read some registers. Observe the traffic.

**Question 7:** What Modbus function codes do you see for read operations?

---

## Deliverables

Create a reconnaissance report including:

1. Network diagram showing discovered devices
2. Device inventory table:
   | IP Address | Unit ID | Description | Open Ports |
   |------------|---------|-------------|------------|
   | | | | |

3. Register map for each PLC
4. Identified vulnerabilities (at least 3)

## Assessment Questions

1. Why is Modbus particularly vulnerable to attacks?
2. What security controls are missing from this environment?
3. How would you defend against the reconnaissance techniques you used?

## Next Lab

In Lab 2, you will learn to read process values in real-time and understand how the water treatment process works.

---

## Solution Key (Instructor Only)

<details>
<summary>Click to reveal answers</summary>

**Question 1:** 4 hosts (3 PLCs + 1 gateway/attacker)

**Question 2:** 10.0.1.10, 10.0.1.11, 10.0.1.12

**Question 3:** Unit IDs, response status, exception handling

**Question 4:** Unit 1, Unit 2, Unit 3 respectively

**Question 5:**
- 10.0.1.10: Raw Water Intake & Pumping
- 10.0.1.11: Water Treatment Process  
- 10.0.1.12: Clearwell & Distribution

**Question 6:** COIL[0] and COIL[1] control pumps P101 and P102

**Question 7:** Function code 3 (Read Holding Registers), Function code 1 (Read Coils)

</details>

# VULNOT Training Curriculum

This document outlines the complete training curriculum for the VULNOT platform.

---

## Official Training Programs

Comprehensive instructor-led training for VULNOT is offered exclusively through **Mjolnir Training**. Our expert instructors provide hands-on guidance through all scenarios and attack techniques.

### Contact for Training

📧 **training@mjolnirsecurity.com**

For corporate training, custom scenarios, or private sessions, please reach out to our training team.

---

## Course Overview

### VULNOT Fundamentals (2 Days)

**Target Audience:** Security professionals new to OT security

**Prerequisites:**
- Basic networking knowledge
- Linux command line familiarity
- Understanding of TCP/IP protocols

**Labs Covered:** 1-4

**Learning Objectives:**
- Understand OT/ICS fundamentals
- Perform OT network reconnaissance
- Exploit Modbus and DNP3 protocols
- Understand industrial process impact

---

### VULNOT Advanced (3 Days)

**Target Audience:** Security professionals with OT experience

**Prerequisites:**
- Completion of VULNOT Fundamentals or equivalent
- Experience with penetration testing
- Understanding of industrial protocols

**Labs Covered:** 5-8

**Learning Objectives:**
- Exploit advanced OT protocols (S7comm, OPC UA, BACnet, MQTT)
- Conduct historian attacks and forensics
- Understand safety system implications
- Perform incident response in OT environments

---

### VULNOT Master Class (5 Days)

**Target Audience:** Senior security professionals and OT specialists

**Prerequisites:**
- Completion of VULNOT Advanced
- Strong penetration testing background
- OT/ICS domain knowledge

**Labs Covered:** Complete curriculum + Capstone

**Certification:** VULNOT OT Security Practitioner

**Learning Objectives:**
- Master all 8 OT protocols
- Execute APT campaign simulations
- Conduct full security assessments
- Map to compliance frameworks
- Generate professional reports

---

## Lab Curriculum

### Lab 1: Modbus Discovery (45 minutes)

**Difficulty:** ⭐ Beginner

**Scenario:** Mjolnir Training Water Treatment Facility

**Objectives:**
1. Understand Modbus TCP protocol fundamentals
2. Perform network reconnaissance
3. Identify PLC devices and their functions
4. Map Modbus address space

**Skills Developed:**
- Network scanning techniques
- Modbus protocol analysis
- OT asset identification

**Tools Used:**
- `vulnot-scan`
- `nmap`
- `vulnot-read`

**Key Concepts:**
- Modbus function codes
- Holding registers vs coils
- Unit IDs

---

### Lab 2: Modbus Exploitation (60 minutes)

**Difficulty:** ⭐ Beginner

**Scenario:** Mjolnir Training Water Treatment Facility

**Objectives:**
1. Read process values from PLCs
2. Write to writable registers
3. Manipulate pump and valve states
4. Understand process impact

**Skills Developed:**
- Modbus exploitation
- Process manipulation
- Impact assessment

**Tools Used:**
- `vulnot-read`
- `vulnot-write`
- `vulnot-monitor`

**Attack Techniques:**
- T0831 - Manipulation of Control
- T0836 - Modify Parameter
- T0879 - Damage to Property

---

### Lab 3: DNP3 Substation Attack (75 minutes)

**Difficulty:** ⭐⭐ Intermediate

**Scenario:** Mjolnir Training Power Grid

**Objectives:**
1. Understand DNP3 protocol structure
2. Enumerate RTU points
3. Execute Select-Before-Operate
4. Trip circuit breakers

**Skills Developed:**
- DNP3 protocol expertise
- Power grid understanding
- Coordinated attack execution

**Tools Used:**
- `vulnot-dnp3`
- Wireshark

**Attack Techniques:**
- T0855 - Unauthorized Command Message
- T0831 - Manipulation of Control
- T0826 - Loss of Availability

**Case Study:** Ukraine 2015 Power Grid Attack

---

### Lab 4: S7comm Manufacturing Sabotage (90 minutes)

**Difficulty:** ⭐⭐ Intermediate

**Scenario:** Mjolnir Training Manufacturing Facility

**Objectives:**
1. Fingerprint Siemens PLCs
2. Read data blocks
3. Modify production parameters
4. Stop PLC CPU

**Skills Developed:**
- S7comm protocol expertise
- PLC programming concepts
- Manufacturing process understanding

**Tools Used:**
- `vulnot-s7`
- `snap7`

**Attack Techniques:**
- T0843 - Program Download
- T0816 - Device Restart/Shutdown
- T0882 - Theft of Operational Information

**Case Study:** Stuxnet technical analysis

---

### Lab 5: OPC UA Reactor Compromise (90 minutes)

**Difficulty:** ⭐⭐ Intermediate

**Scenario:** Mjolnir Training Chemical Reactor

**Objectives:**
1. Browse OPC UA address space
2. Exploit anonymous access
3. Modify reactor setpoints
4. Understand safety implications

**Skills Developed:**
- OPC UA security model
- Chemical process safety
- SIS considerations

**Tools Used:**
- `vulnot-opcua`
- `opcua-client`

**Attack Techniques:**
- T0869 - Standard Application Layer Protocol
- T0836 - Modify Parameter
- T0837 - Loss of Safety

**Case Study:** TRITON/TRISIS attack on safety systems

---

### Lab 6: BACnet Building Takeover (75 minutes)

**Difficulty:** ⭐⭐ Intermediate

**Scenario:** Mjolnir Training Smart Building

**Objectives:**
1. Discover BACnet devices
2. Enumerate object properties
3. Manipulate HVAC settings
4. Control lighting systems

**Skills Developed:**
- BACnet protocol expertise
- Building automation systems
- Physical impact understanding

**Tools Used:**
- `vulnot-bacnet`
- `bacnet-tools`

**Attack Techniques:**
- T0846 - Remote System Discovery
- T0831 - Manipulation of Control

---

### Lab 7: MQTT/IIoT Supply Chain (90 minutes)

**Difficulty:** ⭐⭐⭐ Advanced

**Scenario:** Mjolnir Training IIoT Sensor Network

**Objectives:**
1. Enumerate MQTT topics
2. Subscribe to sensitive data
3. Inject false sensor readings
4. Compromise edge gateways
5. Inject malicious firmware

**Skills Developed:**
- MQTT protocol expertise
- IIoT architecture
- Supply chain attack techniques

**Tools Used:**
- `vulnot-mqtt`
- `mosquitto_sub`
- `mosquitto_pub`

**Attack Techniques:**
- T0869 - Standard Application Layer Protocol
- T0839 - Module Firmware
- T0862 - Supply Chain Compromise

---

### Lab 8: Historian Attacks & Forensics (120 minutes)

**Difficulty:** ⭐⭐⭐⭐ Expert

**Scenario:** Mjolnir Training OT Environment

**Objectives:**
1. Enumerate historian tags
2. Execute SQL injection
3. Exfiltrate historical data
4. Manipulate records
5. Delete evidence
6. Perform forensic investigation

**Skills Developed:**
- OT historian security
- SQL injection techniques
- Digital forensics
- Timeline reconstruction

**Tools Used:**
- `vulnot-historian`
- `vulnot-forensics`
- `sqlmap`

**Attack Techniques:**
- T0890 - Exploitation for Credential Access
- T0882 - Theft of Operational Information
- T0872 - Indicator Removal on Host

---

### Lab 9: Capstone Assessment (4-8 hours)

**Difficulty:** ⭐⭐⭐⭐ Expert

**Scenario:** Complete Mjolnir Training Environment

**Objectives:**
1. Conduct full reconnaissance
2. Identify all vulnerabilities
3. Execute multi-protocol attacks
4. Perform forensic investigation
5. Map to IEC 62443/NIST CSF
6. Generate professional report

**Assessment Phases:**
1. Reconnaissance (60 min)
2. Vulnerability Assessment (90 min)
3. Exploitation (90 min)
4. Forensics (60 min)
5. Compliance Mapping (45 min)
6. Reporting (60 min)

**Scoring Rubric:**

| Phase | Points |
|-------|--------|
| Reconnaissance | 100 |
| Vulnerability Assessment | 150 |
| Exploitation | 150 |
| Forensics | 100 |
| Compliance | 100 |
| Reporting | 150 |
| **Total** | **750** |

**Passing Score:** 600 points

**Certification:** VULNOT OT Security Practitioner

---

## Learning Paths

### Path 1: OT Penetration Tester

Focus on offensive techniques:

```
Lab 1 → Lab 2 → Lab 3 → Lab 4 → Lab 7 → Lab 9
```

Duration: 3-4 days

### Path 2: OT Security Analyst

Focus on detection and response:

```
Lab 1 → Lab 2 → Defense Module → Lab 8 → Hunting Module
```

Duration: 2-3 days

### Path 3: OT Compliance Specialist

Focus on frameworks and assessments:

```
Lab 1 → Lab 2 → Compliance Module → Lab 9 (Reporting focus)
```

Duration: 2 days

### Path 4: Complete OT Security Professional

All labs in sequence:

```
Lab 1 → Lab 2 → Lab 3 → Lab 4 → Lab 5 → Lab 6 → Lab 7 → Lab 8 → Lab 9
```

Duration: 5 days (Master Class)

---

## CTF Challenges

VULNOT includes 25+ CTF challenges across all protocols:

| Category | Challenges | Points Range |
|----------|------------|--------------|
| Modbus | 4 | 50-300 |
| DNP3 | 4 | 100-500 |
| S7comm | 4 | 100-450 |
| OPC UA | 3 | 100-400 |
| BACnet | 3 | 100-350 |
| MQTT | 4 | 75-350 |
| Historian | 3 | 150-400 |
| Forensics | 3 | 200-300 |

Access CTF at: `http://localhost:8080/ctf`

---

## Compliance Framework Mapping

### IEC 62443 Coverage

| Foundational Requirement | Labs |
|--------------------------|------|
| FR1 - Identification & Authentication | 1, 2, 5, 7 |
| FR2 - Use Control | 2, 4, 5 |
| FR3 - System Integrity | 4, 7, 8 |
| FR4 - Data Confidentiality | 8 |
| FR5 - Restricted Data Flow | 3, 6 |
| FR6 - Timely Response | 8 |
| FR7 - Resource Availability | 3, 4 |

### MITRE ATT&CK for ICS Coverage

| Tactic | Techniques Covered |
|--------|-------------------|
| Initial Access | T0866, T0886 |
| Execution | T0807, T0858 |
| Persistence | T0839, T0857 |
| Evasion | T0872 |
| Discovery | T0846, T0888 |
| Collection | T0802, T0882 |
| Command & Control | T0869 |
| Inhibit Response | T0816, T0826 |
| Impair Process | T0831, T0836, T0837 |
| Impact | T0826, T0879 |

---

## Resources

### Pre-Training Reading

1. NIST SP 800-82 - Guide to ICS Security
2. IEC 62443 Overview
3. MITRE ATT&CK for ICS

### Reference Materials

- Protocol specifications (Modbus, DNP3, S7comm, OPC UA, BACnet, EtherNet/IP, MQTT)
- ICS-CERT advisories
- Case studies (Ukraine 2015, TRITON, Stuxnet)

### Post-Training

- VULNOT GitHub repository
- Mjolnir Security blog
- OT security community resources

---

## Training Delivery Options

### Public Training

Scheduled courses at Mjolnir Training facilities.

Contact: training@mjolnirsecurity.com

### Private Training

On-site training at your facility with customized scenarios.

### Virtual Training

Live instructor-led training via video conference with cloud-based lab access.

### Self-Paced

Lab materials available for self-study (certification requires instructor-led assessment).

---

*VULNOT Training Curriculum - Developed by Milind Bhargava at Mjolnir Security*

*For training inquiries: training@mjolnirsecurity.com*

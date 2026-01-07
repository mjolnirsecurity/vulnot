# VULNOT Training Materials

## Overview

This directory contains comprehensive OT/ICS security training materials organized by learning path and skill level.

---

## Training Paths

### 🔴 Red Team Labs (Offensive Security)
Learn to think like an attacker and understand OT vulnerabilities.

| Lab | Protocol | Difficulty | Description |
|-----|----------|------------|-------------|
| [Lab 01](labs/lab-01-modbus-discovery.md) | Modbus TCP | Beginner | Device discovery and enumeration |
| [Lab 02](labs/lab-02-modbus-exploitation.md) | Modbus TCP | Intermediate | Register manipulation attacks |
| [Lab 03](labs/lab-03-dnp3-substation.md) | DNP3 | Intermediate | Power grid control attacks |
| [Lab 04](labs/lab-04-s7-manufacturing.md) | S7comm | Intermediate | Manufacturing PLC exploitation |
| [Lab 05](labs/lab-05-opcua-industrial.md) | OPC UA | Intermediate | Process control manipulation |
| [Lab 06](labs/lab-06-bacnet-building.md) | BACnet | Intermediate | Building automation attacks |
| [Lab 07](labs/lab-07-mqtt-iiot.md) | MQTT | Intermediate | IIoT infrastructure attacks |
| [Lab 08](labs/lab-08-historian-attacks.md) | HTTP/SQL | Advanced | Data historian exploitation |
| [Lab 09](labs/lab-09-multi-vector.md) | Multiple | Advanced | Coordinated multi-protocol attacks |

### 🔵 Blue Team Labs (SOC Defender)
Learn to detect, respond to, and investigate OT security incidents.

| Lab | Focus | Difficulty | Description |
|-----|-------|------------|-------------|
| [SOC 01](soc-defender/soc-01-baseline-monitoring.md) | Monitoring | Beginner | Establishing OT baselines |
| [SOC 02](soc-defender/soc-02-detecting-attacks.md) | Detection | Intermediate | Real-time attack detection |
| [SOC 03](soc-defender/soc-03-incident-response.md) | Response | Intermediate | OT incident response procedures |
| [SOC 04](soc-defender/soc-04-threat-hunting.md) | Hunting | Advanced | Proactive threat hunting |

### 🔍 Forensics Labs (Investigation)
Learn to investigate real-world OT attacks based on documented incidents.

| Lab | Attack | Year | Description |
|-----|--------|------|-------------|
| [Forensics 01](forensics/forensics-01-stuxnet-style.md) | Stuxnet | 2010 | PLC program manipulation |
| [Forensics 02](forensics/forensics-02-industroyer-grid.md) | Industroyer | 2016 | Power grid attacks |
| [Forensics 03](forensics/forensics-03-triton-safety.md) | TRITON | 2017 | Safety system compromise |
| [Forensics 04](forensics/forensics-04-colonial-pipeline.md) | Colonial Pipeline | 2021 | Ransomware IT/OT impact |
| [Forensics 05](forensics/forensics-05-water-utility.md) | Water Attacks | 2021-24 | Water treatment attacks |

---

## Learning Paths by Role

### For Security Analysts
1. Start with SOC 01-02 (monitoring basics)
2. Complete Red Team Labs 01-02 (understand attacks)
3. Progress to SOC 03-04 (advanced defense)
4. Study Forensics Labs for case studies

### For Penetration Testers
1. Complete all Red Team Labs sequentially
2. Study Forensics Labs to understand real attacks
3. Review SOC Labs to understand defender perspective

### For ICS Engineers
1. Start with Red Team Labs 01-04 (understand vulnerabilities)
2. Complete SOC 01 (baseline your systems)
3. Review Forensics Labs for threat awareness

### For Management
1. Review Forensics Lab case studies
2. Understand incident impacts
3. Use for risk assessment discussions

---

## Tools Reference

### Attack Tools (Attacker Container)
| Tool | Protocol | Usage |
|------|----------|-------|
| vulnot-modbus | Modbus TCP | `vulnot-modbus --help` |
| vulnot-dnp3 | DNP3 | `vulnot-dnp3 --help` |
| vulnot-s7 | S7comm | `vulnot-s7 --help` |
| vulnot-opcua | OPC UA | `vulnot-opcua --help` |
| vulnot-bacnet | BACnet | `vulnot-bacnet --help` |
| vulnot-mqtt | MQTT | `vulnot-mqtt --help` |
| vulnot-enip | EtherNet/IP | `vulnot-enip --help` |
| vulnot-historian | Historian | `vulnot-historian --help` |
| vulnot-forensics | Investigation | `vulnot-forensics --help` |

### Access Points
| Service | URL | Credentials |
|---------|-----|-------------|
| Dashboard | http://localhost:8080 | None |
| Grafana | http://localhost:8081 | admin/vulnot |
| API | http://localhost:9000 | None |
| Historian | http://localhost:8443 | admin/admin |

---

## Lab Environment

### Starting the Lab
```bash
cd infrastructure/docker
docker-compose up -d
```

### Accessing Attacker Workstations
```bash
# General red team
docker exec -it vulnot-redteam bash

# Protocol-specific attackers
docker exec -it vulnot-attacker-water bash
docker exec -it vulnot-attacker-power bash
docker exec -it vulnot-attacker-factory bash
```

### Resetting the Lab
```bash
# Reset process state
curl -X POST http://localhost:9000/api/scenario/reset

# Full restart
docker-compose down && docker-compose up -d
```

---

## Compliance Mapping

These labs support training for:
- **NERC CIP** - Bulk Electric System security
- **IEC 62443** - Industrial automation security
- **NIST SP 800-82** - ICS security guide
- **TSA Security Directives** - Pipeline security
- **AWWA** - Water sector guidelines

---

## Contributing

To add new labs:
1. Follow the existing lab format
2. Include clear objectives and prerequisites
3. Provide step-by-step instructions
4. Add expected outputs/findings
5. Include defense recommendations

---

## Disclaimer

This training material is for educational purposes only. All attack techniques demonstrated should only be used in authorized training environments. Attacking real industrial control systems without authorization is illegal and dangerous.

---

## Contact

| Channel | Details |
|---------|---------|
| Website | https://mjolnirsecurity.com |
| GitHub | https://github.com/mjolnirsecurity/vulnot |
| Training | training@mjolnirsecurity.com |
| Commercial | sales@mjolnirsecurity.com |

---

*Developed by Milind Bhargava at Mjolnir Security*
*VULNOT v1.0*

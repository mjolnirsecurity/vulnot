# VULNOT v1.0 - Vulnerable OT Security Training Platform

<p align="center">
  <img src="docs/images/vulnot-logo.png" alt="VULNOT Logo" width="300"/>
</p>

<p align="center">
  <strong>A comprehensive, intentionally vulnerable OT/ICS security training environment</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#scenarios">Scenarios</a> •
  <a href="#training">Training</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <a href="https://github.com/mjolnirsecurity/vulnot">
    <img src="https://img.shields.io/badge/GitHub-mjolnirsecurity%2Fvulnot-blue?logo=github" alt="GitHub"/>
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green" alt="License"/>
  </a>
  <a href="https://mjolnirsecurity.com">
    <img src="https://img.shields.io/badge/By-Mjolnir%20Security-orange" alt="Mjolnir Security"/>
  </a>
</p>

---

## ⚠️ WARNING

**VULNOT is intentionally vulnerable and designed for educational purposes only.**

- ❌ Do NOT expose to the internet
- ❌ Do NOT use in production environments
- ❌ Do NOT connect to real OT/ICS networks
- ✅ Use only in isolated lab environments
- ✅ Always obtain proper authorization before security testing

---

## About

VULNOT (Vulnerable OT) is a comprehensive OT/ICS security training platform developed by **Milind Bhargava** at **[Mjolnir Security](https://mjolnirsecurity.com)** — a 100% Canadian-owned, pure-play cybersecurity firm with 580+ DFIR engagements and SOC 2 Type 2 certification. Born from lessons learned across hundreds of real-world engagements, VULNOT provides realistic, intentionally vulnerable industrial control system simulations for security professionals to learn offensive and defensive OT security techniques in a safe, legal environment.

### Repository

```bash
git clone https://github.com/mjolnirsecurity/vulnot.git
```

### Why VULNOT?

- **Realistic Scenarios**: 9 industrial scenarios simulating real-world OT environments
- **Multi-Protocol**: 8 industrial protocols (Modbus, DNP3, S7comm, OPC UA, BACnet, EtherNet/IP, MQTT, PROFINET)
- **Complete Toolkit**: 17+ attack tools, forensics capabilities, and APT campaign simulations
- **Defense Training**: IDS rules, SIEM correlation, incident response playbooks
- **Compliance Mapping**: IEC 62443, NIST CSF, NERC CIP, MITRE ATT&CK for ICS
- **Gamification**: CTF challenges, scoring, and achievements

---

## Features

### 🏭 9 Industrial Scenarios

| # | Scenario | Protocol | Port | Network |
|---|----------|----------|------|---------|
| 1 | Water Treatment Plant | Modbus TCP | 502 | 10.0.1.0/24 |
| 2 | Power Grid Substation | DNP3 | 20000 | 10.0.2.0/24 |
| 3 | Manufacturing Line | S7comm | 102 | 10.0.3.0/24 |
| 4 | Chemical Reactor | OPC UA | 4840 | 10.0.4.0/24 |
| 5 | Building Automation | BACnet/IP | 47808 | 10.0.5.0/24 |
| 6 | Packaging Line | EtherNet/IP | 44818 | 10.0.6.0/24 |
| 7 | IIoT Smart Factory | MQTT | 1883 | 10.0.7.0/24 |
| 8 | CNC Motion Control | PROFINET | 34964 | 10.0.8.0/24 |
| 9 | OT Historian | HTTP API | 8553 | 10.0.9.0/24 |

### 🔧 17+ Attack Tools

| Category | Tools |
|----------|-------|
| **Reconnaissance** | `vulnot-scan`, `vulnot-dnp3 scan`, `vulnot-s7 scan`, `vulnot-opcua scan`, `vulnot-bacnet scan`, `vulnot-enip scan`, `vulnot-mqtt scan` |
| **Exploitation** | `vulnot-read`, `vulnot-write`, `vulnot-dnp3`, `vulnot-s7`, `vulnot-opcua`, `vulnot-bacnet`, `vulnot-enip`, `vulnot-mqtt`, `vulnot-historian` |
| **Advanced** | `vulnot-apt` (APT campaigns), `vulnot-forensics` (OT forensics), `vulnot-report` (Assessment reports) |

### 🛡️ Defense Capabilities

- **OT IDS**: 20+ protocol-specific detection rules
- **SIEM**: 20 correlation rules (sequence, aggregation, behavioral)
- **Playbooks**: 5 incident response playbooks
- **Threat Hunting**: 8 MITRE ATT&CK mapped hunt queries
- **Forensics**: PLC memory acquisition, timeline reconstruction, IOC extraction

### 📊 12+ Dashboards

| Dashboard | Path | Description |
|-----------|------|-------------|
| Main Dashboard | / | Landing page and navigation |
| Scenarios | /scenarios | All 9 industrial scenarios |
| Process HMIs | /water, /power-grid, /factory | Real-time process displays |
| Defense | /defense | SOC monitoring dashboard |
| Hunting | /hunting | Threat hunting queries |
| Forensics | /forensics | Incident investigation |
| Red Team | /redteam | Red vs Blue exercises |
| CTF | /ctf | Challenges & leaderboard |
| Compliance | /compliance | IEC 62443/NIST CSF assessment |
| Vulnerabilities | /vulnerabilities | Vulnerability management |
| Enterprise | /enterprise | Multi-site overview |

### 📚 9 Training Labs

| Lab | Topic | Duration | Difficulty |
|-----|-------|----------|------------|
| 1 | Modbus Discovery | 45 min | ⭐ Beginner |
| 2 | Modbus Exploitation | 60 min | ⭐ Beginner |
| 3 | DNP3 Substation Attack | 75 min | ⭐⭐ Intermediate |
| 4 | S7comm Manufacturing Sabotage | 90 min | ⭐⭐ Intermediate |
| 5 | OPC UA Reactor Compromise | 90 min | ⭐⭐ Intermediate |
| 6 | BACnet Building Takeover | 75 min | ⭐⭐ Intermediate |
| 7 | MQTT/IIoT Supply Chain | 90 min | ⭐⭐⭐ Advanced |
| 8 | Historian Attacks & Forensics | 120 min | ⭐⭐⭐⭐ Expert |
| 9 | Capstone Assessment | 4-8 hrs | ⭐⭐⭐⭐ Expert |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose v2.0+
- 8GB+ RAM recommended
- Linux, macOS, or Windows with WSL2

### Installation

```bash
# Clone the repository
git clone https://github.com/mjolnirsecurity/vulnot.git
cd vulnot

# Start all services
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# Wait for services to initialize (60-90 seconds)
docker-compose -f infrastructure/docker/docker-compose.yml ps

# Verify all containers are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Dashboard | http://localhost:8080 | N/A |
| Grafana | http://localhost:8081 | admin / vulnot |
| API | http://localhost:9000 | N/A |
| Historian | http://localhost:8553 | N/A (intentionally vulnerable) |

### Your First Attack

```bash
# Connect to the red team workstation
docker exec -it vulnot-redteam bash

# Discover OT devices on the water treatment network
vulnot-scan -n 10.0.1.0/24

# Read PLC registers (tank levels, pump status)
vulnot-read -t 10.0.1.10 -s 0 -c 10

# Modify a setpoint (CAUTION: affects simulated process)
vulnot-write -t 10.0.1.10 -r 1 -v 100

# Run an APT campaign simulation
vulnot-apt list
vulnot-apt start ukraine_2015
vulnot-apt run
```

---

## Scenarios

### Scenario 1: Water Treatment Plant (Modbus TCP)
**Network:** 10.0.1.0/24 | **Port:** 502

Simulates a municipal water treatment facility with intake reservoir control, chemical dosing (chlorine injection), and distribution pump management.

**Attack Vectors:** Unauthenticated register read/write, pump manipulation, chemical dosing attacks

### Scenario 2: Power Grid Substation (DNP3)
**Network:** 10.0.2.0/24 | **Port:** 20000

Simulates electrical substations with circuit breakers, voltage/current monitoring, and SCADA integration.

**Attack Vectors:** Breaker trip commands, measurement manipulation, Ukraine-2015 style coordinated attacks

### Scenario 3: Manufacturing Line (S7comm)
**Network:** 10.0.3.0/24 | **Port:** 102

Simulates Siemens S7-1500 PLCs controlling production line speed, robot coordination, and quality monitoring.

**Attack Vectors:** CPU stop commands, program modification, recipe theft, production sabotage

### Scenario 4: Chemical Reactor (OPC UA)
**Network:** 10.0.4.0/24 | **Port:** 4840

Simulates a batch chemical reactor with temperature/pressure control and safety interlocks.

**Attack Vectors:** Anonymous access, setpoint manipulation, safety system bypass (TRITON-style)

### Scenario 5: Building Automation (BACnet)
**Network:** 10.0.5.0/24 | **Port:** 47808/UDP

Simulates a smart building with HVAC control, lighting systems, and energy management.

**Attack Vectors:** Device enumeration, comfort manipulation, energy waste attacks

### Scenario 6: Packaging Line (EtherNet/IP)
**Network:** 10.0.6.0/24 | **Port:** 44818

Simulates Allen-Bradley packaging with conveyor control, labeling, and quality inspection.

**Attack Vectors:** Tag manipulation, line speed modification, quality bypass

### Scenario 7: IIoT Smart Factory (MQTT)
**Network:** 10.0.7.0/24 | **Port:** 1883

Simulates IIoT infrastructure with 17 sensors, 3 edge gateways, and firmware update mechanisms.

**Attack Vectors:** Topic enumeration, sensor spoofing, gateway compromise, firmware injection

### Scenario 8: CNC Motion Control (PROFINET)
**Network:** 10.0.8.0/24 | **Port:** 34964

Simulates a 5-axis CNC machining center with servo drives and spindle control.

**Attack Vectors:** Position manipulation, drive disable, program theft, motion disruption

### Scenario 9: OT Historian (HTTP API)
**Network:** 10.0.9.0/24 | **Port:** 8553

Simulates a process data historian with 64 tags and 24 hours of historical data.

**Attack Vectors:** SQL injection, data exfiltration, evidence deletion, historical data manipulation

---

## Training

### Official Training Programs

Comprehensive instructor-led training for VULNOT is offered exclusively through **Mjolnir Training**. Our expert instructors provide hands-on guidance through all scenarios and attack techniques.

**Available Courses:**

| Course | Duration | Labs Covered |
|--------|----------|--------------|
| VULNOT Fundamentals | 2 days | Labs 1-4 |
| VULNOT Advanced | 3 days | Labs 5-8 |
| VULNOT Master Class | 5 days | Complete curriculum + Capstone |

**Certification:** Successful completion of the Master Class includes the **VULNOT OT Security Practitioner** certification.

### Contact for Training

For corporate training, custom scenarios, or private sessions, please reach out via our **[contact form](website/contact.html)**.

### Self-Paced Labs

The training labs in `training/labs/` provide structured exercises. While self-study is possible, we recommend the official Mjolnir Training courses for the best learning experience with expert guidance and certification.

---

## Tool Reference

### Reconnaissance
```bash
vulnot-scan -n 10.0.1.0/24                    # Network discovery
vulnot-dnp3 scan -n 10.0.2.0/24               # DNP3 device scan
vulnot-s7 scan -n 10.0.3.0/24                 # Siemens S7 scan
vulnot-opcua scan -n 10.0.4.0/24              # OPC UA discovery
vulnot-bacnet scan -n 10.0.5.0/24             # BACnet discovery
vulnot-enip scan -n 10.0.6.0/24               # EtherNet/IP scan
vulnot-mqtt scan -n 10.0.7.0/24               # MQTT broker scan
```

### Exploitation
```bash
vulnot-read -t 10.0.1.10 -s 0 -c 10           # Modbus read
vulnot-write -t 10.0.1.10 -r 1 -v 100         # Modbus write
vulnot-dnp3 control -t 10.0.2.10 --point 0 --action trip
vulnot-s7 stop -t 10.0.3.10                   # Stop PLC CPU
vulnot-opcua write -t 10.0.4.10 -n "ns=2;s=Setpoint" -v 150
vulnot-mqtt publish -b 10.0.7.5 -t 'factory/control/cmd' -m 'stop'
vulnot-historian sqli -t 10.0.9.10 --type dump_history
```

### APT Campaigns
```bash
vulnot-apt list                               # List available campaigns
vulnot-apt show ukraine_2015                  # Show campaign details
vulnot-apt start ukraine_2015                 # Initialize campaign
vulnot-apt run                                # Execute next step
```

### Forensics
```bash
vulnot-forensics acquire-plc -t 10.0.3.10 -p s7comm -c CASE-001
vulnot-forensics analyze-pcap -f capture.pcap -c CASE-001
vulnot-forensics timeline -c CASE-001
vulnot-forensics preserve -c CASE-001 -o evidence.zip
```

### Reporting
```bash
vulnot-report generate -f markdown -o report.md
vulnot-report generate -f html -o report.html
```

---

## Compliance Mapping

VULNOT maps findings to major OT security frameworks:

| Framework | Coverage |
|-----------|----------|
| **IEC 62443-3-3** | 7 Foundational Requirements, 50+ Security Requirements |
| **NIST CSF** | All 5 Functions (Identify, Protect, Detect, Respond, Recover) |
| **NERC CIP** | CIP-002 through CIP-011 |
| **MITRE ATT&CK for ICS** | 40+ Techniques mapped |

---

## SIEM Integration

Forward all OT security logs to your SIEM platform for centralized monitoring, alerting, and compliance reporting.

### Supported Platforms

| SIEM Platform | Status | Documentation |
|---------------|--------|---------------|
| **Sumo Logic** | Primary | [integrations/siem/sumologic](integrations/siem/sumologic/) |
| **Splunk** | Supported | [integrations/siem/splunk](integrations/siem/splunk/) |
| **ELK Stack** | Supported | [integrations/siem/elk](integrations/siem/elk/) |
| **Google Chronicle** | Supported | [integrations/siem/chronicle](integrations/siem/chronicle/) |

### Features

- **Real-time Log Forwarding**: All protocol activity streamed via Redis pub/sub
- **MITRE ATT&CK Enrichment**: Automatic technique and tactic mapping
- **Normalized Log Format**: Consistent schema across all protocols
- **Batch Processing**: Configurable batch sizes and flush intervals

### Quick Start

```bash
# Sumo Logic (set your HTTP Source URL)
export SUMO_HTTP_SOURCE_URL="https://endpoint.sumologic.com/..."
cd integrations/siem/sumologic
docker-compose up -d
```

### Custom Dashboards

Need custom SIEM dashboards, correlation rules, or integration support? **[Contact us](website/contact.html)**.

---

## Website

The VULNOT multi-page website provides interactive documentation, HMI dashboard showcases, and detailed tool references.

| Page | Description |
|------|-------------|
| [Home](website/index.html) | Landing page with platform overview |
| [Dashboards](website/dashboards.html) | Gallery of 9 interactive HMI dashboards |
| [Training](website/training.html) | Red Team labs, Forensics cases, SOC courses |
| [Offensive](website/offensive.html) | 12 attack tools with full command documentation |
| [Defensive](website/defensive.html) | 6 defense capabilities with detailed descriptions |
| [Forensics](website/forensics.html) | 6 case studies + 2 forensics toolkits |
| [SIEM](website/siem.html) | 5 SIEM integrations with architecture diagrams |
| [Contact](website/contact.html) | Contact form |

### Sample Dashboards

Interactive HTML dashboards demonstrating HMI interfaces for each scenario are available both as standalone files in [sample-dashboards/](sample-dashboards/) and wrapped with site navigation in [website/dashboards/](website/dashboards/).

---

## Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](docs/INSTALLATION.md) | Detailed setup instructions |
| [Architecture Overview](docs/ARCHITECTURE.md) | System design and components |
| [API Reference](docs/API_REFERENCE.md) | REST API documentation |
| [Training Curriculum](docs/TRAINING_CURRICULUM.md) | Lab objectives and learning paths |
| [Contributing Guide](docs/CONTRIBUTING.md) | How to contribute to VULNOT |

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details.

### Areas of Interest
- Additional OT protocols (HART, Foundation Fieldbus, PROFIBUS)
- New attack techniques and detection rules
- Training content and documentation
- Bug fixes and improvements

---

## License

MIT License - See [LICENSE](LICENSE) for details.

**This software is provided for educational purposes only.** Users are responsible for ensuring they have proper authorization before conducting any security testing.

---

## Credits

**VULNOT** was developed by **Milind Bhargava** at **[Mjolnir Security](https://mjolnirsecurity.com)**.

### Acknowledgments
- MITRE ATT&CK for ICS team
- ICS-CERT for vulnerability advisories
- The OT security research community
- Open source contributors

---

## Contact

| Purpose | Contact |
|---------|---------|
| Website | [https://mjolnirsecurity.com](https://mjolnirsecurity.com) |
| GitHub | [https://github.com/mjolnirsecurity/vulnot](https://github.com/mjolnirsecurity/vulnot) |
| Inquiries | [Contact Form](website/contact.html) |

---

<p align="center">
  <strong>Built for OT Security Professionals</strong><br>
  <em>© 2026 Mjolnir Security. All rights reserved.</em>
</p>

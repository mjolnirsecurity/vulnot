# VULNOT Architecture Overview

This document describes the system architecture, components, and design decisions of the VULNOT platform.

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Component Overview](#component-overview)
3. [Network Architecture](#network-architecture)
4. [Data Flow](#data-flow)
5. [Security Considerations](#security-considerations)
6. [Deployment Models](#deployment-models)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Dashboard  │  │   Grafana   │  │  CLI Tools  │  │  Training Labs      │ │
│  │   :8080     │  │   :8081     │  │  (Attacker) │  │  (Documentation)    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘ │
└─────────┼────────────────┼────────────────┼─────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Backend (:9000)                            │   │
│  │  • REST API         • WebSocket (Real-time)    • Process Data        │   │
│  │  • Authentication   • Alarm Management         • Control Commands    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                │
          ▼                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│  ┌────────────────────┐      ┌────────────────────┐                         │
│  │       Redis        │      │     InfluxDB       │                         │
│  │   (Pub/Sub, State) │      │  (Time Series DB)  │                         │
│  │      :6379         │      │      :8086         │                         │
│  └────────────────────┘      └────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                │
          ▼                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OT SIMULATION LAYER                                  │
│                                                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  Water  │ │  Power  │ │ Factory │ │ Reactor │ │Building │ │Packaging│   │
│  │ Modbus  │ │  DNP3   │ │ S7comm  │ │ OPC UA  │ │ BACnet  │ │ EIP     │   │
│  │ :502    │ │ :20000  │ │ :102    │ │ :4840   │ │ :47808  │ │ :44818  │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
│                                                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                                        │
│  │  IIoT   │ │   CNC   │ │Historian│                                        │
│  │  MQTT   │ │PROFINET │ │  HTTP   │                                        │
│  │ :1883   │ │ :34964  │ │ :8553   │                                        │
│  └─────────┘ └─────────┘ └─────────┘                                        │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEFENSE LAYER                                        │
│  ┌────────────────────┐      ┌────────────────────┐                         │
│  │     OT IDS         │      │   SIEM Correlation │                         │
│  │  (20+ Rules)       │      │   (20 Rules)       │                         │
│  └────────────────────┘      └────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Overview

### Simulators

Each simulator provides a realistic OT device with intentional vulnerabilities:

| Simulator | Protocol | Vulnerabilities | Files |
|-----------|----------|-----------------|-------|
| Water Treatment | Modbus TCP | No auth, writable registers | `simulators/modbus-water/` |
| Power Grid | DNP3 | No SA, direct operate | `simulators/dnp3-power/` |
| Manufacturing | S7comm | CPU stop, no protection | `simulators/s7-factory/` |
| Chemical Reactor | OPC UA | Anonymous access | `simulators/opcua-industrial/` |
| Building | BACnet | No encryption | `simulators/bacnet-building/` |
| Packaging | EtherNet/IP | Tag access | `simulators/ethernet-ip/` |
| IIoT | MQTT | No auth, wildcard sub | `simulators/mqtt-iiot/` |
| CNC | PROFINET | Direct drive access | `simulators/profinet-motion/` |
| Historian | HTTP | SQL injection | `simulators/historian/` |

### Attack Tools

Located in `attacker/scripts/`:

```
vulnot-scan         # Network discovery
vulnot-read         # Modbus read
vulnot-write        # Modbus write
vulnot-dnp3         # DNP3 operations
vulnot-s7           # S7comm operations
vulnot-opcua        # OPC UA operations
vulnot-bacnet       # BACnet operations
vulnot-enip         # EtherNet/IP operations
vulnot-mqtt         # MQTT operations
vulnot-historian    # Historian attacks
vulnot-apt          # APT campaign manager
vulnot-forensics    # Forensics toolkit
vulnot-report       # Report generator
```

### Defense Components

Located in `defense/`:

```
defense/
├── ids/                    # Intrusion Detection System
│   ├── ot_ids.py          # Main IDS engine
│   └── rules/             # Detection rules
├── siem/
│   └── rules/
│       └── correlation_rules.py  # 20 SIEM correlation rules
├── playbooks/
│   └── incident_response.md      # IR playbooks
├── compliance/
│   └── iec62443.py        # IEC 62443 assessment
└── forensics/             # Forensics tools
```

### Dashboard Application

Located in `apps/dashboard/`:

- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS with custom OT/HMI theme
- **State Management**: Zustand
- **Real-time**: WebSocket connections

Pages:
- `/` - Landing and navigation
- `/scenarios` - All 9 scenarios overview
- `/water`, `/power-grid`, `/factory` - Process HMIs
- `/defense` - SOC monitoring
- `/hunting` - Threat hunting
- `/forensics` - Investigation tools
- `/redteam` - Red vs Blue exercises
- `/ctf` - CTF challenges
- `/compliance` - IEC 62443/NIST CSF
- `/vulnerabilities` - Vulnerability management
- `/enterprise` - Multi-site view

### API Backend

Located in `apps/api/`:

- **Framework**: FastAPI
- **Real-time**: WebSocket support
- **Database**: Redis (state), InfluxDB (time series)

---

## Network Architecture

### Docker Networks

```yaml
networks:
  vulnot-backend:     # Internal services
    subnet: 172.20.0.0/16
    
  vulnot-ot-water:    # Scenario 1
    subnet: 10.0.1.0/24
    
  vulnot-ot-power:    # Scenario 2
    subnet: 10.0.2.0/24
    
  vulnot-ot-factory:  # Scenario 3
    subnet: 10.0.3.0/24
    
  vulnot-ot-reactor:  # Scenario 4
    subnet: 10.0.4.0/24
    
  vulnot-ot-building: # Scenario 5
    subnet: 10.0.5.0/24
    
  vulnot-ot-packaging:# Scenario 6
    subnet: 10.0.6.0/24
    
  vulnot-ot-iiot:     # Scenario 7
    subnet: 10.0.7.0/24
    
  vulnot-ot-motion:   # Scenario 8
    subnet: 10.0.8.0/24
    
  vulnot-ot-historian:# Scenario 9
    subnet: 10.0.9.0/24
```

### IP Address Assignments

| Device | IP Address | Network |
|--------|------------|---------|
| Water PLC | 10.0.1.10 | vulnot-ot-water |
| Water Attacker | 10.0.1.100 | vulnot-ot-water |
| Power RTU | 10.0.2.10 | vulnot-ot-power |
| Power Attacker | 10.0.2.100 | vulnot-ot-power |
| Factory PLC | 10.0.3.10 | vulnot-ot-factory |
| Factory Attacker | 10.0.3.100 | vulnot-ot-factory |
| Reactor OPC | 10.0.4.10 | vulnot-ot-reactor |
| Building BAS | 10.0.5.10 | vulnot-ot-building |
| Packaging PLC | 10.0.6.10 | vulnot-ot-packaging |
| MQTT Broker | 10.0.7.5 | vulnot-ot-iiot |
| IIoT Gateway | 10.0.7.10-12 | vulnot-ot-iiot |
| CNC Machine | 10.0.8.10 | vulnot-ot-motion |
| Historian | 10.0.9.10 | vulnot-ot-historian |

### Purdue Model Alignment

```
┌─────────────────────────────────────────────────────────────┐
│ Level 5: Enterprise Network                                  │
│   Dashboard, Grafana, API (simulated as accessible)         │
├─────────────────────────────────────────────────────────────┤
│ Level 4: Site Business Planning and Logistics               │
│   Historian (10.0.9.10)                                     │
├─────────────────────────────────────────────────────────────┤
│ Level 3: Site Operations                                     │
│   HMI Interfaces (via Dashboard)                            │
├─────────────────────────────────────────────────────────────┤
│ Level 2: Area Supervisory Control                           │
│   PLCs, RTUs, Controllers (10.0.x.10)                       │
├─────────────────────────────────────────────────────────────┤
│ Level 1: Basic Control                                       │
│   I/O, Sensors, Actuators (simulated within devices)        │
├─────────────────────────────────────────────────────────────┤
│ Level 0: Process                                             │
│   Physical Process (simulated values)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Process Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Simulator  │────▶│    Redis     │────▶│   Dashboard  │
│  (PLC/RTU)   │     │  (Pub/Sub)   │     │  (WebSocket) │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │
       │                    ▼
       │             ┌──────────────┐
       │             │   InfluxDB   │
       │             │ (Time Series)│
       │             └──────────────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│   Historian  │     │   Grafana    │
│  (SQL Vuln)  │     │  (Charts)    │
└──────────────┘     └──────────────┘
```

### Attack Detection Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Attacker   │────▶│  OT Network  │────▶│    OT IDS    │
│   Tools      │     │   Traffic    │     │  (Suricata)  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │     SIEM     │
                                          │ (Correlation)│
                                          └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │   Dashboard  │
                                          │   (Alerts)   │
                                          └──────────────┘
```

---

## Security Considerations

### Intentional Vulnerabilities

VULNOT includes these **intentional** vulnerabilities for training:

| Category | Vulnerabilities |
|----------|-----------------|
| Authentication | No auth on Modbus, DNP3, S7comm, MQTT |
| Encryption | No TLS on OT protocols |
| Access Control | Writable registers, CPU stop commands |
| Input Validation | SQL injection in Historian |
| Segmentation | Flat networks (by default) |

### Isolation Requirements

**CRITICAL**: VULNOT must be deployed in isolation:

1. **No Internet Access**: Block all outbound connections
2. **No Production Networks**: Never connect to real OT systems
3. **Host Firewall**: Restrict access to training participants only
4. **Separate VLAN**: Deploy on dedicated training network

### Recommended Deployment

```bash
# Create isolated Docker network
docker network create --internal vulnot-isolated

# Block external access (host firewall)
sudo iptables -A INPUT -p tcp --dport 8080 -s 192.168.100.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8080 -j DROP
```

---

## Deployment Models

### Single Host (Development/Training)

All containers on one machine:

```
┌─────────────────────────────────────┐
│           Single Host               │
│                                     │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │ DB  │ │ API │ │ Web │ │Sims │   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
│                                     │
└─────────────────────────────────────┘
```

### Multi-Host (Enterprise Training)

Distributed across multiple machines:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  App Host   │     │   OT Host   │     │ Attack Host │
│             │     │             │     │             │
│  Dashboard  │     │ Simulators  │     │ Attacker    │
│  API        │◀───▶│ (All 9)     │◀───▶│ Workstation │
│  Grafana    │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Cloud Deployment (Instructor-Led)

For Mjolnir Training courses:

```
┌─────────────────────────────────────────────────────────┐
│                    Cloud Provider                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Instructor  │  │  Student 1   │  │  Student N   │  │
│  │   Instance   │  │   Instance   │  │   Instance   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  VPN Required for Access                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
vulnot/
├── README.md                    # Main documentation
├── LICENSE                      # MIT License
├── docker-compose.yml           # Quick start compose
├── .env.example                 # Environment template
│
├── docs/                        # Documentation
│   ├── INSTALLATION.md
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── TRAINING_CURRICULUM.md
│   └── CONTRIBUTING.md
│
├── simulators/                  # OT device simulators
│   ├── modbus-water/
│   ├── dnp3-power/
│   ├── s7-factory/
│   ├── opcua-industrial/
│   ├── bacnet-building/
│   ├── ethernet-ip/
│   ├── mqtt-iiot/
│   ├── profinet-motion/
│   └── historian/
│
├── attacker/                    # Attack tools
│   ├── Dockerfile
│   ├── scripts/                 # CLI tools
│   ├── apt/                     # APT campaigns
│   └── tools/                   # Legacy tools
│
├── defense/                     # Defense capabilities
│   ├── ids/                     # Intrusion detection
│   ├── siem/                    # SIEM rules
│   ├── playbooks/               # IR playbooks
│   ├── compliance/              # IEC 62443
│   └── forensics/               # Forensics tools
│
├── apps/                        # Web applications
│   ├── api/                     # FastAPI backend
│   └── dashboard/               # Next.js frontend
│
├── training/                    # Training materials
│   └── labs/                    # Lab exercises
│
└── infrastructure/              # Deployment
    └── docker/                  # Docker Compose files
```

---

*VULNOT Architecture - Developed by Milind Bhargava at Mjolnir Security*

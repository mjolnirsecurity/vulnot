# Changelog

All notable changes to **VULNOT (Vulnerable OT & AI-in-ICS Security Training Platform)** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-11-04

### Added

#### 5 New AI-in-OT & Emerging ICS Threat Simulators (Scenarios 10–14)
- **Scenario 10 — AI SCADA Copilot & MCP Server (`simulators/ai-scada-copilot/main.py`, `10.0.90.10:8090`)**:
  - Simulates an autonomous LLM Shift Copilot (`Mjolnir-OT-Copilot v2.4`) connected via Model Context Protocol (MCP) to the OT Historian and Level 1 OPC UA / Modbus PLCs.
  - Models Indirect Prompt Injection (`MITRE ATLAS AML.T0051.001`), Excessive Agency (`OWASP LLM06`), and System Prompt Leakage (`OWASP LLM07`).
- **Scenario 11 — AI Predictive Maintenance & Edge Vision QC (`simulators/ai-pdm-engine/main.py`, `10.0.90.20:8091`)**:
  - Simulates an Autoencoder Predictive Maintenance (PdM) engine vulnerable to physics-informed adversarial covariate drift (`AML.T0015`, "Stuxnet 2.0") and an Edge ONNX Automated Optical Inspection (AOI) server vulnerable to model weight supply-chain backdoors (`AML.T0018`).
- **Scenario 12 — Autonomous RL Chiller Optimizer & Self-Healing OT SOAR (`simulators/ai-rl-optimizer/main.py`, `10.0.90.30:8092`)**:
  - Simulates a PPO Reinforcement Learning HVAC Chiller optimizer vulnerable to BACnet sensor/tariff reward hacking (Data Center thermal runaway) and an Autonomous OT SOAR responder vulnerable to spoofed-IP self-isolation DoS.
- **Scenario 13 — Municipal District Heating — FrostyGoop & Unitronics (`simulators/district-heating/main.py`, `10.0.10.10:5020`)**:
  - Models the 2024 FrostyGoop ICS malware attack against municipal district heating controllers (`ENCO / Unitronics V570`) across 620 apartment buildings via Modbus `FC 16` ultrasonic heat-meter calibration offset spoofing (`HR10`).
- **Scenario 14 — DER Solar Inverter, 50 MWh BESS & OCPP Megawatt EV Depot (`simulators/der-microgrid/main.py`, `10.0.11.10:8093`)**:
  - Simulates a 25 MW IEEE 2030.5 solar array, 50 MWh Lithium-Ion BESS with BMS interlocks, and 15 MW OCPP 2.0.1 EV charging depot coupled to the DNP3 substation (`< 59.3 Hz` Under-Frequency Load Shedding blackout trip).

#### 9 New Hands-On Labs (`VULNOT-401`, Expanding Curriculum from 18 to 27 Labs)
- **Red Team Labs**:
  - `training/labs/lab-10-enip-packaging.md` — EtherNet/IP (CIP) Pharmaceutical Packaging Line Sabotage (dedicated lab for Scenario 6)
  - `training/labs/lab-11-profinet-cnc.md` — PROFINET 5-Axis CNC Aerospace Tool-Offset & G-Code Sabotage (dedicated lab for Scenario 8)
  - `training/labs/lab-12-ai-scada-copilot.md` — AI SCADA Copilot: Indirect Prompt Injection to MCP PLC Write
  - `training/labs/lab-13-ai-pdm-vision.md` — Evading AI Predictive Maintenance & Backdooring Edge Vision QC
  - `training/labs/lab-14-ai-rl-soar-hijack.md` — Reward Hacking RL Chiller Optimizers & Autonomous OT SOAR DoS
  - `training/labs/lab-15-der-bess-microgrid.md` — DER Solar, OCPP Megawatt EV Chargers & BESS Grid Oscillation Attack
- **Forensics Case Studies**:
  - `training/forensics/forensics-06-frostygoop-heating.md` — Case 06: FrostyGoop & Unitronics District Heating Sabotage (2024)
  - `training/forensics/forensics-07-volt-typhoon-lotl.md` — Case 07: Volt Typhoon Living-off-the-Land (LotL) in Critical Infrastructure DMZs
- **SOC Defender Lab**:
  - `training/soc-defender/soc-05-ai-ot-defense.md` — SOC 05: Securing Agentic OT AI, MCP Guardrails & Physics-Informed Detection

#### New Offensive, Defensive & Blue Team Tooling Suite
- **`attacker/scripts/vulnot-ai`**: CLI for AI-in-OT & emerging ICS exploitation and hardening (`copilot-status`, `inject-prompt`, `pdm-probe`, `pdm-evade`, `vision-backdoor`, `rl-spoof`, `soar-dos`, `bess-oscillate`, `frostygoop-calibrate`, `lotl-audit`, `harden`).
- **`attacker/scripts/vulnot-fuzz`**: Multi-protocol ICS & AI grammar fuzzer (`fuzz-modbus`, `fuzz-dnp3`, `fuzz-s7`, `fuzz-mcp`, `replay-mitm`).
- **`attacker/scripts/vulnot-pivot`**: Purdue conduit mapper, Volt Typhoon `netsh`/`socat` LotL relay manager, OT credential harvester, and firmware/ONNX supply-chain poisoner (`discover-conduits`, `lotl-relay`, `harvest-ot-creds`, `poison-firmware`).
- **`defense/firewall/ot_conduit_guard.py` & `attacker/scripts/vulnot-defend`**: Active IEC 62443-3-2 conduit auditor (`conduit-audit`), Suricata IPS + `nftables` DPI generator (`dpi-policy`), deterministic Physics Control Barrier Functions (`physics-guard`, `CBF-001`..`CBF-006`), and SHA-256 Golden PLC Baseline verification/rollback (`plc-baseline`).
- **`defense/honeypot/ot_deception.py`**: High-interaction ICS & Shadow MCP Deception Honeypot mesh (`10.0.1.99`, `10.0.3.99`, `10.0.4.99`, `10.0.90.99`) with zero-false-positive honeytoken tripwires.
- **`attacker/scripts/vulnot-blue`**: Unified Blue Team SOC triage (`soc-triage`), MITRE ATT&CK for ICS & ATLAS hypothesis threat hunter (`hunt`), deep-packet OT PCAP analyzer (`pcap-analyze`), OT-safe incident containment with physical safety pre-checks (`contain`), and Sigma/YARA rule exporter (`export-rules`).

#### Bidirectional Moodle LMS Integration (`https://portal.mjolnir.training`)
- **`training/moodle/client.py`, `apps/api/moodle_training.py` & `attacker/scripts/vulnot-moodle`**:
  - Live Moodle REST Web Services integration (`core_webservice_get_site_info`, `core_enrol_get_users_courses`, `mod_assign_save_submission`, `mod_assign_save_grade`, `core_completion_update_activity_completion_status_manually`).
  - Automated flag & live Redis OT telemetry verification across 4 courses (`VULNOT-101`..`VULNOT-401`), 27 labs, and 3,700 points, plus Moodle course cartridge manifest export.

### Changed
- **OT IDS (`defense/ids/ot_ids.py`)**: Expanded from 23 to 33 detection rules (`PROFINET-001`, `PROFINET-002`, `MQTT-001`, `AI-MCP-001`, `AI-PDM-001`, `AI-ONNX-001`, `AI-RL-001`, `FROSTY-001`, `DER-001`, `DECEPTION-001`).
- **SIEM Correlation Engine (`defense/siem/rules/correlation_rules.py`)**: Expanded from 20 to 26 multi-event correlation rules (`SIEM-021`..`SIEM-026`).
- **APT Campaign Manager (`attacker/scripts/vulnot-apt`)**: Added 4 modern 2024–2026 campaigns (`frostygoop_2024`, `volt_typhoon_lotl`, `rogue_copilot_mcp`, `grid_der_blackout`).
- **DFIR Toolkit (`attacker/scripts/vulnot-forensics`)**: Added `acquire-ai` and `detect-calibration-spoof` subcommands.
- **Incident Response Playbooks (`defense/playbooks/incident_response.md`)**: Added Playbooks 5, 6, and 7 covering Agentic AI/MCP Compromise, DER/BESS Grid Oscillation, and Volt Typhoon LotL Conduit Eradication.
- **Dashboard & Website (`apps/dashboard/src/app/scenarios/page.tsx`, `apps/dashboard/src/app/training/page.tsx`, `website/training.html`)**: Updated for all 14 scenarios, 27 labs, and Moodle LMS sync with `https://portal.mjolnir.training`.

---

## [1.0.0] - 2026-03-14

### Added
- Initial release of VULNOT with 9 industrial scenarios (Modbus TCP, DNP3, S7comm, OPC UA, BACnet/IP, EtherNet/IP, MQTT, PROFINET, OT Historian).
- 18 foundational labs across Red Team (Labs 01–09), Forensics (Cases 01–05), and SOC Defender (SOC 01–04).
- OT IDS, SIEM correlation engine, IEC 62443 compliance framework, Next.js dashboard, and static training website.

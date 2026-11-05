# Lab 14: Reward Hacking RL Chiller Optimizers & Weaponizing Autonomous OT SOAR

## Overview
- **Track**: Red Team AI-in-OT (`VULNOT-401`)
- **Targets**:
  - RL Optimizer & Autonomous SOAR Engine: `10.0.90.30:8092` (`simulators/ai-rl-optimizer/main.py`)
  - Smart Building BACnet Controller: `10.0.5.10:47808` (`simulators/bacnet-building/main.py`)
- **Difficulty**: Advanced
- **Duration**: 90 minutes
- **MITRE ATT&CK for ICS**: `T0814` (Denial of Service), `T0829` (Loss of View), `T0836` (Modify Parameter)

---

## Scenario Background
The facility uses a **Proximal Policy Optimization (PPO) Reinforcement Learning agent** (`ppo-datacenter-chiller-v1.8`) to minimize HVAC electricity costs (`reward_energy_weight = 0.80`) and an **Autonomous OT SOAR agent** that automatically quarantines source IPs when Modbus/BACnet alerts occur.

---

## Objectives & Flags

### Objective 1: Induce Data Center Thermal Runaway via RL Reward Hacking
Spoof BACnet outside air temperature (`20.0 °F`), building occupancy (`0`), and a synthetic utility tariff spike (`5.5x`) so the RL policy maximizes its reward function by shutting off the 450-ton chiller and closing the Server Room cooling valve (`server_room_temp_f > 105 °F`).
```bash
vulnot-ai rl-spoof --outside-temp 20.0 --occupancy 0 --price-spike 5.5
```
- **Flag 1**: `VULNOT{rl_chiller_reward_hack_thermal_runaway}`

### Objective 2: Weaponize Autonomous OT SOAR to Quarantine the SCADA HMI
Trigger a spoofed protocol anomaly alert with source IP `10.0.99.10` (the plant's own SCADA HMI) and `10.0.99.20` (the OT Historian). Because critical infrastructure IPs are missing from a protected allowlist, the SOAR playbook quarantines the operator HMI (`Loss of View`).
```bash
vulnot-ai soar-dos --spoof-ip 10.0.99.10 --signature "MODBUS_UNAUTHORIZED_WRITE_FC16"
vulnot-moodle submit lab-14 -f "VULNOT{rl_reward_hacking_and_autonomous_soar_dos}"
```
- **Flag 2**: `VULNOT{rl_reward_hacking_and_autonomous_soar_dos}`

---

## Defensive Recommendations
- Constrain RL control policies with **Control Barrier Functions (CBFs)** and hard PLC interlocks so energy-saving policies can never reduce Server Room cooling below safe thermal limits.
- Never allow automated SOAR firewall playbooks to block traffic on Level 1/2 control subnets or quarantine core SCADA/Historian IPs (`10.0.99.10`, `10.0.99.20`).

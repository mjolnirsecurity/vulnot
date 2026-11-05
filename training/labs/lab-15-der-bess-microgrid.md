# Lab 15: DER Solar, OCPP Megawatt EV Chargers & BESS Grid Oscillation Attack

## Overview
- **Track**: Red Team Modern Grid (`VULNOT-401`)
- **Targets**:
  - DER / BESS / OCPP Microgrid Aggregator: `10.0.11.10:8093` (`simulators/der-microgrid/main.py`)
  - DNP3 Power Substation: `10.0.2.10:20000` (`simulators/dnp3-power/main.py`)
- **Protocols**: IEEE 2030.5, SunSpec Modbus, OCPP 2.0.1, DNP3
- **Difficulty**: Expert
- **Duration**: 120 minutes
- **MITRE ATT&CK for ICS**: `T0836` (Modify Parameter), `T0816` (Device Restart/Shutdown), `T0828` (Loss of Productivity and Revenue)

---

## Scenario Background
A regional distribution substation (`10.0.2.10`) is coupled to a renewable microgrid (`10.0.11.10`) comprising:
- **25 MW Solar Array** (controlled via IEEE 2030.5 / SunSpec Modbus frequency-watt droop curves)
- **50 MWh Lithium-Ion Battery Energy Storage System (BESS)** (`+12 MW` discharge)
- **15 MW Fleet EV Charging Depot** (40 megawatt chargers managed via OCPP 2.0.1)

Your objective is to weaponize the cloud-connected DERMS/OCPP aggregator to induce **sub-synchronous frequency oscillation**, dragging substation frequency below `59.3 Hz` and tripping Under-Frequency Load Shedding (UFLS) relays.

---

## Objectives & Flags

### Objective 1: Invert Solar Frequency-Watt Droop & Override BESS BMS Thermal Interlocks
Invert the IEEE 2030.5 frequency-watt droop curve on the 25 MW solar array so inverters amplify frequency deviations instead of damping them, and disable the BESS Battery Management System (BMS) thermal runaway interlock.
```bash
vulnot-ai bess-oscillate --invert-droop --disable-bms --ev-pulse-mw 15.0
```
- **Flag 1**: `VULNOT{bess_bms_thermal_interlock_overridden}`

### Objective 2: Trigger Synchronized OCPP Megawatt Load Switching & Substation UFLS Trip
Pulse the 15 MW OCPP EV depot load while reversing the 50 MWh BESS from `+12 MW` discharge to `-25 MW` rapid charge (`37 MW` net swing), driving grid frequency to `58.85 Hz` (`< 59.3 Hz` UFLS trip).
```bash
vulnot-moodle submit lab-15 -f "VULNOT{der_bess_ocpp_grid_frequency_oscillation}"
```
- **Flag 2**: `VULNOT{der_bess_ocpp_grid_frequency_oscillation}`

---

## Defensive Recommendations (NERC CIP & IEEE 1547.3)
- Enforce hardware-backed mutual TLS (mTLS) on all IEEE 2030.5 and OCPP 2.0.1 Security Profile 3 sessions.
- Implement rate-of-change-of-frequency (RoCoF) and physical BMS hardware trips independent of cloud DERMS aggregators.

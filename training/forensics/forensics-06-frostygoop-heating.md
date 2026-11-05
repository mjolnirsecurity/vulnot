# Forensics 06: FrostyGoop & Unitronics District Heating Sabotage (2024)

## Overview
- **Track**: ICS Incident Forensics (`VULNOT-401`)
- **Incident Reference**: FrostyGoop ICS Malware (Lviv, Ukraine — January 2024) & CyberAv3ngers Unitronics Campaign (2023–2024)
- **Target Simulator**: `10.0.10.10:5020` (`simulators/district-heating/main.py`)
- **Protocols**: Modbus TCP (`502`/`5020`), Unitronics PCOM (`20256`)
- **Difficulty**: Advanced
- **Duration**: 120 minutes

---

## Incident Background
In January 2024, **FrostyGoop** became the ninth publicly known ICS-specific malware family—and the first to use **Modbus TCP** directly to cause civilian impact, disabling district heating to **600+ apartment buildings** in Lviv for nearly 48 hours during sub-zero temperatures (`-12 °C`).

Attackers gained initial access via an internet-exposed MikroTik router, pivoted to ENCO heating controllers (`10.0.10.10`), closed the main steam heating valves (`HR0`), and modified the ultrasonic heat-meter calibration offset register (`HR10 = +65.0 °C`) so the central SCADA HMI continued displaying normal `83.0 °C` supply water while actual water dropped to `18.0 °C`.

---

## Investigation Objectives & Flags

### Objective 1: Reconstruct the Modbus FC16 Calibration Spoofing Attack
Inspect the District Heating controller state and reproduce/analyze the FrostyGoop calibration register manipulation (`calibration_offset_c = +65.0 °C`, `main_steam_valve_pct = 0%`).
```bash
vulnot-ai frostygoop-calibrate --setpoint 15.0 --valve 0.0 --offset 65.0
```
- **Flag 1**: `VULNOT{frostygoop_enco_modbus_fc16_identified}`

### Objective 2: Correlate Reported vs. Actual Thermal Telemetry Discrepancy
Identify the `+65.0 °C` delta between `reported_supply_water_temp_c` (`83.0 °C`) and `actual_supply_water_temp_c` (`18.0 °C`) across the 620 affected apartment buildings and submit the forensic verification flag.
```bash
vulnot-moodle submit forensics-06 -f "VULNOT{frostygoop_modbus_calibration_spoof_detected}"
```
- **Flag 2**: `VULNOT{frostygoop_modbus_calibration_spoof_detected}`

---

## Lessons Learned & Remediation
- Never expose municipal heating controllers (ENCO, Unitronics V570) or edge MikroTik management interfaces directly to the public internet.
- Alert on any write (`FC06` / `FC16`) to sensor calibration offset registers (`HR10`–`HR12`), which should only change during scheduled annual metrology servicing.

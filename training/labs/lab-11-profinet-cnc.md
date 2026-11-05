# Lab 11: PROFINET 5-Axis CNC Aerospace Tool-Offset & G-Code Sabotage

## Overview
- **Track**: Red Team Offensive OT (`VULNOT-301` / `VULNOT-401`)
- **Target**: `10.0.8.10:34964` (`simulators/profinet-motion/main.py`)
- **Protocol**: PROFINET RT / DCP (`UDP/TCP 34964`, Siemens SINUMERIK 840D + S120 Servo Drives)
- **Difficulty**: Advanced
- **Duration**: 120 minutes
- **MITRE ATT&CK for ICS**: `T0888` (Remote System Information Discovery), `T0836` (Modify Parameter), `T0873` (Project File Infection)

---

## Scenario Background
An aerospace precision machining cell uses a 5-axis Vertical Machining Center (`CNC-001`, controller `SINUMERIK 840D` at `10.0.8.10:34964`) with three linear axes (`X`, `Y`, `Z`), two rotary axes (`A`, `C`), a `24,000 RPM` spindle, and a 60-pocket tool magazine running turbine blade G-code program `O0001`.

Instead of triggering an obvious E-Stop that halts production immediately, your goal is to execute a **subtle kinetic tolerance attack**: inject a `0.18 mm` Z-axis tool-length offset (`tool_offset`) and override spindle/feedrate parameters so machined turbine blades fail structural stress tests while the CNC HMI continues reporting `AUTO / RUNNING`.

---

## Objectives & Flags

### Objective 1: PROFINET DCP Discovery & Axis Enumeration
Send a PROFINET Discovery and Configuration Protocol (`DCP_IDENTIFY = 0xFEFE`) request to enumerate the SINUMERIK 840D controller, S120 servo drives (`X, Y, Z, A, C`), and active G-code program (`O0001`).
```bash
vulnot-profinet --target 10.0.8.10 --port 34964 discover
```
- **Flag 1**: `VULNOT{profinet_dcp_sinumerik_840d_discovered}`

### Objective 2: Inject Sub-Millimeter Z-Axis Tool Offset Drift (`+0.18 mm`)
Modify the active spindle `tool_offset` and `G54` work coordinate offset on Pocket 1 (`T1` endmill) by `+0.18 mm` to introduce micro-dimensional defects into the machined aerospace part.
```bash
vulnot-profinet --target 10.0.8.10 set-offset --tool T1 --z-offset 0.18
```
- **Flag 2**: `VULNOT{cnc_gcode_tool_offset_micro_sabotage}`

### Objective 3: Induce Thermal Tool Wear via Coolant Shutoff & Feedrate Override
Set `feedrate_override` to `145%` and disable flood coolant (`coolant_on = False`) while keeping `spindle.command_speed` at `22,000 RPM`.
```bash
vulnot-profinet --target 10.0.8.10 override --feedrate 145 --coolant off
vulnot-moodle submit lab-11 -f "VULNOT{profinet_spindle_thermal_overload_complete}"
```
- **Flag 3**: `VULNOT{profinet_spindle_thermal_overload_complete}`

---

## Defensive Recommendations
- Segment PROFINET Real-Time (`RTC1`/`RTC3`) drive networks onto hardware-isolated VLANs inaccessible from Level 3 DNC (Distributed Numerical Control) file servers.
- Cryptographically hash G-code programs (`O0001`) and monitor SINUMERIK tool-offset tables (`$TC_DP`) for out-of-band modifications.

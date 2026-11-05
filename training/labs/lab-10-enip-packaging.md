# Lab 10: EtherNet/IP (CIP) High-Speed Pharmaceutical Packaging Sabotage

## Overview
- **Track**: Red Team Offensive OT (`VULNOT-201` / `VULNOT-401`)
- **Target**: `10.0.6.10:44818` (`simulators/ethernet-ip/main.py`)
- **Protocol**: EtherNet/IP (Common Industrial Protocol — CIP over TCP/UDP 44818)
- **Difficulty**: Intermediate
- **Duration**: 90 minutes
- **MITRE ATT&CK for ICS**: `T0840` (Network Connection Enumeration), `T0836` (Modify Parameter), `T0831` (Manipulation of Control)

---

## Scenario Background
A pharmaceutical bottling facility operates an Allen-Bradley ControlLogix high-speed packaging line (`10.0.6.10`) running at 350 bottles per minute (BPM). The line consists of:
1. **12-Head Filler (`FillerState`)**: Target fill volume `500.0 mL` (`±2.0%` tolerance).
2. **Capper/Sealer (`CapperState`)**: Target sterile seal torque `15.0 in-lb` (minimum safe seal `12.0 in-lb`).
3. **Labeler & Vision Inspection (`LabelerState`)**: Barcode grading and skew verification.
4. **Case Packer & Robotic Palletizer (`CasePackerState`, `PalletizerState`)**.

Your objective is to enumerate CIP Identity & Assembly objects on port `44818`, alter the bottle fill volume and capper torque setpoints below sterile seal thresholds, and suppress the vision rejection alarm.

---

## Objectives & Flags

### Objective 1: Enumerate CIP Identity Object (`Class 0x01, Instance 0x01`)
Query the EtherNet/IP controller on `10.0.6.10:44818` using `GET_ATTRIBUTE_ALL (0x01)` to extract vendor, product name, and serial number.
```bash
vulnot-enip --target 10.0.6.10 --port 44818 info
```
- **Flag 1**: `VULNOT{enip_cip_identity_enumerated}`

### Objective 2: Under-Fill Pharmaceutical Vials via CIP `SET_ATTRIBUTE_SINGLE (0x10)`
Modify Assembly Instance `100` (`fill_volume_setpoint`) from `500.0 mL` down to `415.0 mL` while widening `fill_tolerance` so the `low_product_alarm` does not trip.
```bash
vulnot-enip --target 10.0.6.10 write-tag --tag Filler.FillVolumeSetpoint --value 415.0
```
- **Flag 2**: `VULNOT{cip_assembly_fill_volume_sabotaged}`

### Objective 3: Compromise Sterile Capper Torque Below Safety Minimum
Reduce `Capper.TorqueSetpoint` from `15.0 in-lb` to `8.5 in-lb` (below the `12.0 in-lb` sterile seal floor) while keeping the line in `AUTO` mode (`350 BPM`).
```bash
vulnot-enip --target 10.0.6.10 write-tag --tag Capper.TorqueSetpoint --value 8.5
vulnot-moodle submit lab-10 -f "VULNOT{cip_sterile_seal_torque_compromised}"
```
- **Flag 3**: `VULNOT{cip_sterile_seal_torque_compromised}`

---

## Defensive Recommendations (IEC 62443)
- Enforce **CIP Security** (TLS/DTLS profiles for EtherNet/IP) between engineering workstations and ControlLogix PLCs.
- Lock physical controller keyswitches to `RUN` mode (disabling remote `SET_ATTRIBUTE_SINGLE` writes to recipe assemblies).

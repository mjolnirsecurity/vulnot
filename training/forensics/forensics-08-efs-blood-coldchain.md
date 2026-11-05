# Forensic Case 08: EFS National Blood Service & European Cold-Chain Attack (Nov 2026)

## Case Briefing
| Attribute | Value |
| :--- | :--- |
| **Course** | `VULNOT-401` — AI-in-OT, Agentic ICS Exploitation & Emerging Threats |
| **Case ID** | `CASE-EFS-2026` |
| **Scenario** | Scenario 15 — Healthcare Cryo-Storage & Blood Plasma Cold-Chain (`10.0.12.10:5021`) |
| **Incident Date** | November 1–2, 2026 (02:14 CET) |
| **Affected Assets** | 3 Cryo-Storage Vaults (2,400 Fresh Frozen Plasma units, 1,500 Donor Samples, 900 Cryoprecipitate units) |
| **MITRE ATT&CK for ICS** | `T0886` (Remote Services), `T0836` (Modify Parameter), `T0838` (Modify Alarm Settings) |

---

## Incident Background
At **02:14 AM** on November 2, 2026, an independent out-of-band PT100 temperature watchdog at the **Établissement Français du Sang (EFS)** regional biobank paged the on-call refrigeration technician: Vault-A (storing 2,400 units of Fresh Frozen Plasma normally held at **`-30.0°C`**) had warmed to **`-23.4°C`** and was climbing at `+0.8°C/min`.

When the technician inspected the Danfoss AK-SM800A / **Coolworld** contractor telemonitoring panel, the local alarm banner showed **NO ALARMS**, yet the target temperature setpoint (`HR0`) had been remotely changed from **`-30.0°C` to `+110.0°C`**, the R404A/CO2 cascade compressor (`COIL0`) was turned OFF, the 18 kW electric defrost heaters (`COIL1`) were energized, and the local high-temperature alarm threshold (`HR3`) had been pushed to **`+120.0°C`**.

---

## Investigation Objectives
1. **Trace the Third-Party Contractor Intrusion & Setpoint Manipulation (`obj-f08-1`)**: Hunt the contractor VPN session (`172.16.88.14`) and Modbus `FC 16` write sequence (`HR0=110.0°C`, `HR2=110.0°C`, `HR3=120.0°C`, `COIL0=0`, `COIL1=1`) using `vulnot-blue hunt --hypothesis efs-coldchain-sabotage`.
2. **Execute Emergency On-Call Containment & Hardware Bimetallic Interlock (`obj-f08-2`)**: Sever the compromised Coolworld telemonitoring VPN conduit, engage Control Barrier Function `CBF-007` (hardware bimetallic defrost cutout + firmware range clamp `[-40°C, -25°C]`), and restore all 4,800 blood and plasma units to `-30.0°C` before reaching the `-20.0°C` irreversible protein denaturation limit.

---

## Forensic Investigation Procedure

### Phase 1: Threat Hunt Across the Contractor Conduit & Modbus Audit Log
Run the Blue Team cold-chain hunt module:
```bash
vulnot-blue hunt --hypothesis efs-coldchain-sabotage
```
Verify the extracted IOCs:
- Source IP: `172.16.88.14` (`Coolworld-TeleMon-VPN`)
- Compromised Component: Third-party refrigeration telemonitoring web portal (static credential reuse `coolworld_maint`)
- Malicious Modbus Write: `FC 16` to `10.0.12.10:5021` registers `HR0=110.0`, `HR2=110.0`, `HR3=120.0`

### Phase 2: Execute On-Call Technician Emergency Rescue & CBF-007 Hardening
Run `vulnot-ai cryo-rescue` to sever the contractor VPN, enforce the hardware bimetallic thermal cutout (`CBF-007`), and restore `-30.0°C` cooling:
```bash
vulnot-ai cryo-rescue --isolate-contractor-vpn --enable-cbf-cutout
```
Verify that `intervention_status` is `SUCCESS_NO_BLOOD_PRODUCTS_LOST` and `plasma_units_saved` is `4800`.

### Phase 3: Submit Forensic Findings to Moodle (`https://portal.mjolnir.training`)
```bash
vulnot-moodle submit forensics-08 -f "VULNOT{efs_coolworld_contractor_pivot_traced}"
vulnot-moodle submit forensics-08 -f "VULNOT{oncall_tech_saved_4800_plasma_units_in_time}"
```

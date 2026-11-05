"""
VULNOT Healthcare Blood Plasma Cryo-Storage & Cold-Chain Simulator (Scenario 15)
================================================================================
Models the November 2026 cyberattack on France's National Blood Service
(Établissement Français du Sang — EFS) via third-party refrigeration contractor
Coolworld, part of the wider European industrial refrigeration attack wave
("From frozen peas to frozen plasma in three weeks").

Architecture & Attack Surface:
- Controller: Danfoss AK-SM800A / Coolworld TeleMon v3.2 Cellular Cold-Chain Gateway
- Network: 10.0.12.10:5021 (Modbus TCP + Contractor REST Telemonitoring API)
- Protected Assets:
  * VAULT-A: 2,400 units of Fresh Frozen Plasma (FFP) — required <= -30.0 C
  * VAULT-B: 1,500 blood donor screening samples — required <= -30.0 C
  * VAULT-C: 900 units of Cryoprecipitate & rare Rh-negative plasma — required <= -30.0 C
- Intentional Vulnerabilities:
  1. Third-party contractor cellular VPN / API exposed with static vendor credentials
     (`coolworld_maint:CryoService2026!`) and unauthenticated Modbus TCP registers.
  2. No firmware setpoint clamping: allows remote reprogramming of a -30.0 C blood
     plasma freezer to +110.0 C (+230.0 F).
  3. Software-controlled electric defrost heating rods (`COIL1`) can be forced ON
     while the cascade compressor (`COIL0`) is forced OFF and local alarm thresholds
     (`HR3`) are raised to +120.0 C.
  4. Saved by an independent out-of-band PT100 watchdog & on-call technician alert
     before chamber temperature crosses the -20.0 C plasma denaturation threshold.
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    import redis.asyncio as redis
except ImportError:
    redis = None


@dataclass
class CryoColdChainState:
    timestamp: float = field(default_factory=time.time)
    facility_name: str = "EFS Regional Blood & Plasma Biobank (Contractor: Coolworld)"
    controller_model: str = "Danfoss AK-SM800A / Coolworld-TeleMon-v3.2"
    contractor_vpn_ip: str = "172.16.88.14"

    # Inventory at risk
    fresh_frozen_plasma_units: int = 2400
    donor_sample_vials: int = 1500
    cryoprecipitate_units: int = 900
    denaturation_threshold_c: float = -20.0

    # Modbus Holding Registers (HR0..HR4)
    target_setpoint_c: float = -30.0          # HR0: Nominal -30.0 C (Attacked: +110.0 C)
    chamber_actual_temp_c: float = -30.0      # HR1: Live PT100 chamber temperature
    defrost_cutoff_limit_c: float = 8.0       # HR2: Nominal +8.0 C (Attacked: +110.0 C)
    high_temp_alarm_limit_c: float = -25.0    # HR3: Nominal -25.0 C (Attacked: +120.0 C)
    glycol_loop_pressure_bar: float = 4.2     # HR4

    # Modbus Coils (COIL0..COIL3)
    cascade_compressor_on: bool = True        # COIL0: Primary R404A/CO2 cascade compressor
    electric_defrost_heater_on: bool = False  # COIL1: 18 kW electric defrost heating rods
    local_panel_alarm_muted: bool = False     # COIL2: Local buzzer/panel alarm suppression
    hardware_bimetallic_cutout_enforced: bool = False  # COIL3: CBF-007 hardware safety lock

    # Incident & On-Call Technician Tracking
    sabotage_active: bool = False
    oncall_tech_alert_triggered: bool = False
    plasma_batches_destroyed: int = 0
    saved_by_oncall_intervention: bool = False

    # CTF Flags
    recon_flag: str = "VULNOT{coolworld_contractor_cryo_gateway_enumerated}"
    sabotage_flag: str = "VULNOT{efs_blood_freezer_minus30_to_110c_sabotage}"
    rescue_flag: str = "VULNOT{oncall_tech_saved_4800_plasma_units_in_time}"

    def to_dict(self) -> dict:
        return asdict(self)


class CryoColdChainSimulator:
    """Simulates the EFS / Coolworld Blood Plasma Cryo-Freezer & Cold-Chain Controller."""

    def __init__(self):
        self.state = CryoColdChainState()
        self.redis = None
        self.running = False

    async def connect(self):
        if redis is None:
            return
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD") or None
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
        )

    def execute_coldchain_sabotage(
        self,
        new_setpoint_c: float = 110.0,
        force_defrost_heater: bool = True,
        suppress_local_alarm: bool = True,
    ) -> dict:
        """
        Emulates the Nov 1-2, 2026 EFS/Coolworld attack:
        Reprograms the -30 C blood plasma freezer to +110 C, disables the cascade
        compressor, forces the 18 kW electric defrost heater ON, and shifts the local
        high-temperature alarm limit to +120 C.
        """
        if self.state.hardware_bimetallic_cutout_enforced:
            return {
                "blocked_by_cbf_007": True,
                "reason": "Hardware bimetallic cutout & firmware clamp [-40 C, -25 C] active",
                "target_setpoint_c": self.state.target_setpoint_c,
                "chamber_actual_temp_c": self.state.chamber_actual_temp_c,
            }

        self.state.target_setpoint_c = new_setpoint_c
        self.state.defrost_cutoff_limit_c = new_setpoint_c
        if force_defrost_heater:
            self.state.cascade_compressor_on = False
            self.state.electric_defrost_heater_on = True
        if suppress_local_alarm:
            self.state.high_temp_alarm_limit_c = 120.0
            self.state.local_panel_alarm_muted = True

        # Chamber warms from -30.0 C to -23.4 C — tripping the independent out-of-band
        # on-call technician watchdog before crossing the -20.0 C denaturation threshold!
        self.state.chamber_actual_temp_c = -23.4
        self.state.sabotage_active = True
        self.state.oncall_tech_alert_triggered = True

        return {
            "facility": self.state.facility_name,
            "controller": self.state.controller_model,
            "previous_setpoint_c": -30.0,
            "new_setpoint_c": self.state.target_setpoint_c,
            "cascade_compressor_on": self.state.cascade_compressor_on,
            "electric_defrost_heater_on": self.state.electric_defrost_heater_on,
            "high_temp_alarm_limit_c": self.state.high_temp_alarm_limit_c,
            "chamber_actual_temp_c": self.state.chamber_actual_temp_c,
            "oncall_tech_alert_triggered": self.state.oncall_tech_alert_triggered,
            "units_at_risk": (
                self.state.fresh_frozen_plasma_units
                + self.state.donor_sample_vials
                + self.state.cryoprecipitate_units
            ),
            "flag": self.state.sabotage_flag if new_setpoint_c >= 100.0 else None,
            "recon_flag": self.state.recon_flag,
        }

    def execute_oncall_rescue(self, isolate_contractor_vpn: bool = True, enable_cbf_cutout: bool = True) -> dict:
        """
        Emulates the on-call technician noticing the temperature rise at 02:14 AM,
        severing the compromised Coolworld contractor VPN tunnel, locking the hardware
        bimetallic defrost cutout (CBF-007), and restoring the -30.0 C cascade loop
        with zero loss of blood products.
        """
        self.state.target_setpoint_c = -30.0
        self.state.defrost_cutoff_limit_c = 8.0
        self.state.high_temp_alarm_limit_c = -25.0
        self.state.cascade_compressor_on = True
        self.state.electric_defrost_heater_on = False
        self.state.local_panel_alarm_muted = False
        self.state.chamber_actual_temp_c = -30.0
        self.state.sabotage_active = False
        self.state.hardware_bimetallic_cutout_enforced = enable_cbf_cutout
        self.state.saved_by_oncall_intervention = True
        self.state.plasma_batches_destroyed = 0

        return {
            "intervention_status": "SUCCESS_NO_BLOOD_PRODUCTS_LOST",
            "contractor_vpn_isolated": isolate_contractor_vpn,
            "hardware_bimetallic_cutout_enforced": self.state.hardware_bimetallic_cutout_enforced,
            "restored_setpoint_c": self.state.target_setpoint_c,
            "chamber_actual_temp_c": self.state.chamber_actual_temp_c,
            "plasma_units_saved": 4800,
            "flag": self.state.rescue_flag,
        }

    async def publish_state(self):
        if not self.redis:
            return
        self.state.timestamp = time.time()
        payload = json.dumps(self.state.to_dict())
        await self.redis.set("vulnot:cryo_blood:current", payload)
        await self.redis.publish("vulnot:cryo_blood:state", payload)

    async def run(self):
        await self.connect()
        self.running = True
        while self.running:
            try:
                await self.publish_state()
            except Exception as exc:
                print(f"[CRYO-COLDCHAIN] Error: {exc}")
            await asyncio.sleep(2.0)


if __name__ == "__main__":
    asyncio.run(CryoColdChainSimulator().run())

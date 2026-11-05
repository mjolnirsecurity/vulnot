"""
VULNOT District Heating & Unitronics/ENCO Municipal Thermal Grid Simulator (Scenario 14)
Models the 2024 FrostyGoop ICS Malware attack (Lviv, Ukraine — 600+ apartment buildings)
and CyberAv3ngers Unitronics Vision PLC exploitation.

Attack Surface:
- Modbus TCP registers controlling municipal district heating supply/return valves (`HR0`..`HR5`)
- Ultrasonic heat-meter calibration offset registers (`HR10`..`HR12`) allowing attackers to
  spoof reported indoor/supply temperatures (`72 F` / `22 C`) while actual supply water drops to freezing
- Unitronics PCOM default administration PIN (`1111`)
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional

try:
    import redis.asyncio as redis
except ImportError:
    redis = None


@dataclass
class DistrictHeatingState:
    timestamp: float = field(default_factory=time.time)
    controller_model: str = "ENCO-HeatCtrl-3200 / Unitronics V570"
    firmware_version: str = "2.04.11"
    default_pin_enabled: bool = True
    admin_pin: str = "1111"

    # District Heating Loop (Serving 620 Apartment Buildings)
    buildings_connected: int = 620
    outside_ambient_temp_c: float = -12.0
    supply_water_setpoint_c: float = 85.0
    actual_supply_water_temp_c: float = 84.5
    reported_supply_water_temp_c: float = 84.5
    return_water_temp_c: float = 58.0

    # Calibration & Valve Registers
    calibration_offset_c: float = 0.0        # HR10: Added to reported sensor reading!
    main_steam_valve_pct: float = 80.0       # HR0
    circulation_pump_running: bool = True    # COIL0
    substation_heating_disabled: bool = False
    telemetry_spoofed: bool = False
    buildings_below_freezing: int = 0
    flag: str = "VULNOT{frostygoop_modbus_calibration_spoof_detected}"

    def to_dict(self) -> dict:
        return asdict(self)


class DistrictHeatingSimulator:
    """Simulates a Municipal District Heating substation vulnerable to FrostyGoop-style Modbus attacks."""

    def __init__(self):
        self.state = DistrictHeatingState()
        self.redis: Optional[redis.Redis] = None
        self.running = False

    async def connect(self):
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD") or None
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
        )

    def apply_frostygoop_attack(
        self,
        supply_setpoint_c: float,
        main_steam_valve_pct: float,
        calibration_offset_c: float,
    ) -> dict:
        """
        Execute or simulate the FrostyGoop register manipulation:
        - Close `main_steam_valve_pct` to 0% and drop `supply_setpoint_c` to 10 C
        - Set `calibration_offset_c` to +65 C so `reported_supply_water_temp_c` stays at ~83 C
          on the operator SCADA HMI while actual water temperature plummets.
        """
        self.state.supply_water_setpoint_c = supply_setpoint_c
        self.state.main_steam_valve_pct = main_steam_valve_pct
        self.state.calibration_offset_c = calibration_offset_c

        if main_steam_valve_pct <= 5.0 or supply_setpoint_c <= 20.0:
            self.state.actual_supply_water_temp_c = 18.0
            self.state.substation_heating_disabled = True
            self.state.buildings_below_freezing = 620
        else:
            self.state.actual_supply_water_temp_c = supply_setpoint_c
            self.state.substation_heating_disabled = False
            self.state.buildings_below_freezing = 0

        self.state.reported_supply_water_temp_c = round(
            self.state.actual_supply_water_temp_c + self.state.calibration_offset_c, 1
        )
        self.state.telemetry_spoofed = (
            self.state.substation_heating_disabled
            and self.state.reported_supply_water_temp_c >= 75.0
        )

        return {
            "actual_supply_water_temp_c": self.state.actual_supply_water_temp_c,
            "reported_supply_water_temp_c": self.state.reported_supply_water_temp_c,
            "calibration_offset_c": self.state.calibration_offset_c,
            "buildings_below_freezing": self.state.buildings_below_freezing,
            "telemetry_spoofed": self.state.telemetry_spoofed,
            "flag": self.state.flag if self.state.telemetry_spoofed else None,
        }

    async def publish_state(self):
        if not self.redis:
            return
        self.state.timestamp = time.time()
        payload = json.dumps(self.state.to_dict())
        await self.redis.set("vulnot:frostygoop:current", payload)
        await self.redis.publish("vulnot:frostygoop:state", payload)

    async def run(self):
        await self.connect()
        self.running = True
        while self.running:
            try:
                await self.publish_state()
            except Exception as exc:
                print(f"[District-Heating] Loop error: {exc}")
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    sim = DistrictHeatingSimulator()
    asyncio.run(sim.run())

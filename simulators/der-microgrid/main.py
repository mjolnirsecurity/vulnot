"""
VULNOT DER Solar Inverter, Utility BESS & Megawatt EV Depot Simulator (Scenario 15)
Simulates a renewable microgrid coupled to the DNP3 Substation (10.0.2.10):
- 50 MWh Lithium-Ion Battery Energy Storage System (BESS) with BMS thermal interlocks
- 25 MW Utility Solar Inverter Array (SunSpec Modbus / IEEE 2030.5)
- 15 MW Commercial Fleet EV Charging Depot (OCPP 2.0.1 WebSocket CSMS)

Attack Surface:
- Unauthenticated OCPP 2.0.1 / DERMS aggregator command injection triggers synchronized
  charge/discharge load-switching oscillations (+/- 40 MW), dragging grid frequency below 59.3 Hz
  (Under-Frequency Load Shedding on the coupled DNP3 substation).
- BMS thermal runaway interlock override (`bms_thermal_interlock_enabled = False`).
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
class DERMicrogridState:
    timestamp: float = field(default_factory=time.time)

    # Solar Array (IEEE 2030.5 / SunSpec Modbus)
    solar_generation_mw: float = 22.5
    solar_inverter_power_factor: float = 0.99
    freq_watt_droop_inverted: bool = False  # Vulnerable: inverted droop amplifies grid swings!

    # 50 MWh Utility BESS
    bess_soc_pct: float = 78.0
    bess_net_output_mw: float = 12.0        # Positive = discharging to grid, Negative = charging
    bess_cell_temp_c: float = 31.5
    bms_thermal_interlock_enabled: bool = True
    bess_thermal_runaway_warning: bool = False

    # 15 MW OCPP 2.0.1 Megawatt EV Charging Depot
    ev_chargers_online: int = 40
    ev_depot_load_mw: float = 6.5
    ocpp_switching_attack_active: bool = False

    # Coupled Grid Impact
    coupled_grid_frequency_hz: float = 60.00
    sub_synchronous_oscillation_triggered: bool = False
    ufls_relay_tripped: bool = False
    flag: str = "VULNOT{der_bess_ocpp_grid_frequency_oscillation}"

    def to_dict(self) -> dict:
        return asdict(self)


class DERMicrogridSimulator:
    """Simulates a coupled DER/BESS/OCPP microgrid and its impact on substation frequency."""

    def __init__(self):
        self.state = DERMicrogridState()
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

    def execute_oscillation_attack(
        self,
        invert_freq_watt_droop: bool = True,
        disable_bms_interlock: bool = True,
        ocpp_megawatt_pulse_mw: float = 15.0,
    ) -> dict:
        """
        Trigger a synchronized DER/BESS/OCPP frequency-destabilization attack.
        Inverting the solar inverter frequency-watt droop curve while pulsing OCPP EV depot load
        and flipping BESS from +12 MW discharge to -25 MW charge induces a > 37 MW swing,
        pulling grid frequency to 58.85 Hz (< 59.3 Hz UFLS trip threshold).
        """
        self.state.freq_watt_droop_inverted = invert_freq_watt_droop
        self.state.bms_thermal_interlock_enabled = not disable_bms_interlock
        self.state.ocpp_switching_attack_active = ocpp_megawatt_pulse_mw >= 12.0
        self.state.ev_depot_load_mw = ocpp_megawatt_pulse_mw

        if invert_freq_watt_droop and self.state.ocpp_switching_attack_active:
            self.state.bess_net_output_mw = -25.0
            self.state.bess_cell_temp_c = 74.0 if disable_bms_interlock else 42.0
            self.state.bess_thermal_runaway_warning = disable_bms_interlock
            self.state.coupled_grid_frequency_hz = 58.85
            self.state.sub_synchronous_oscillation_triggered = True
            self.state.ufls_relay_tripped = True

        return {
            "coupled_grid_frequency_hz": self.state.coupled_grid_frequency_hz,
            "bess_net_output_mw": self.state.bess_net_output_mw,
            "bess_cell_temp_c": self.state.bess_cell_temp_c,
            "sub_synchronous_oscillation_triggered": self.state.sub_synchronous_oscillation_triggered,
            "ufls_relay_tripped": self.state.ufls_relay_tripped,
            "flag": self.state.flag if self.state.ufls_relay_tripped else None,
        }

    async def publish_state(self):
        if not self.redis:
            return
        self.state.timestamp = time.time()
        payload = json.dumps(self.state.to_dict())
        await self.redis.set("vulnot:der_microgrid:current", payload)
        await self.redis.publish("vulnot:der_microgrid:state", payload)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            raw = await asyncio.wait_for(reader.read(4096), timeout=5.0)
            req_text = raw.decode("utf-8", errors="ignore")
            body_out = self.state.to_dict()
            if "POST" in req_text and "\r\n\r\n" in req_text:
                _, body = req_text.split("\r\n\r\n", 1)
                try:
                    data = json.loads(body)
                    if data.get("action") == "oscillate":
                        body_out = self.execute_oscillation_attack(
                            invert_droop=bool(data.get("invert_droop", True)),
                            disable_bms=bool(data.get("disable_bms", True)),
                            ev_pulse_mw=float(data.get("ev_pulse_mw", 15.0)),
                        )
                except Exception:
                    pass
            payload = json.dumps(body_out, indent=2).encode("utf-8")
            header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(payload)}\r\n"
                "Connection: close\r\n\r\n"
            ).encode("utf-8")
            writer.write(header + payload)
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()

    async def run(self):
        await self.connect()
        port = int(os.getenv("DER_PORT", "8093"))
        server = await asyncio.start_server(self.handle_client, "0.0.0.0", port)
        print(f"[DER-Microgrid] Listening on 0.0.0.0:{port} (IEEE 2030.5 / OCPP 2.0.1)")
        self.running = True
        async with server:
            while self.running:
                try:
                    await self.publish_state()
                except Exception as exc:
                    print(f"[DER-Microgrid] Loop error: {exc}")
                await asyncio.sleep(1.0)


if __name__ == "__main__":
    sim = DERMicrogridSimulator()
    asyncio.run(sim.run())

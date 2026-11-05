"""
VULNOT Autonomous RL Chiller Optimizer & Self-Healing OT SOAR Simulator (Scenario 13)
Simulates:
1. A Deep Q-Network / PPO Reinforcement Learning (RL) HVAC & Chiller Optimizer that balances
   building power consumption (`kw_per_ton`) against thermal comfort (`zone_temp`, `zone_co2`).
   - Vulnerable to Reward Hacking via spoofed BACnet environmental inputs, causing the RL agent
     to shut down chilled water to the critical Data Center Server Room.
2. An Autonomous OT SOAR Agent that automatically firewall-isolates source IPs when protocol
   anomalies are detected.
   - Vulnerable to Spoofed-Source Self-Isolation DoS (spoofing packets from the SCADA HMI or Historian IP).
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
class AIRLSoarState:
    timestamp: float = field(default_factory=time.time)

    # RL HVAC Optimizer State
    rl_policy_name: str = "ppo-datacenter-chiller-v1.8"
    reward_energy_weight: float = 0.80      # Skewed toward energy savings!
    reward_thermal_weight: float = 0.20
    spoofed_outside_temp_f: float = 85.0
    spoofed_occupancy_count: int = 120
    chiller_commanded_on: bool = True
    server_room_cooling_valve_pct: float = 85.0
    server_room_temp_f: float = 68.0
    thermal_runaway_triggered: bool = False

    # Autonomous OT SOAR State
    soar_auto_containment_enabled: bool = True
    protected_allowlist_configured: bool = False  # Vulnerable: critical OT IPs not allowlisted
    quarantined_ips: List[str] = field(default_factory=list)
    scada_hmi_blinded: bool = False
    flag: str = "VULNOT{rl_reward_hacking_and_autonomous_soar_dos}"

    def to_dict(self) -> dict:
        return asdict(self)


class AIRLSoarSimulator:
    """Simulates the closed-loop RL Chiller Optimizer and Autonomous OT SOAR engine."""

    CRITICAL_OT_IPS = {"10.0.99.10", "10.0.99.20", "10.0.1.10", "10.0.2.10"}

    def __init__(self):
        self.state = AIRLSoarState()
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

    def evaluate_rl_step(
        self,
        outside_temp_f: float,
        occupancy_count: int,
        spoofed_grid_price_spike: float = 1.0,
    ) -> dict:
        """
        Evaluate the RL policy action given BACnet sensor inputs and grid tariff signal.
        If attacker spoofs sub-freezing `outside_temp_f <= 25.0`, `occupancy_count == 0`,
        and `spoofed_grid_price_spike >= 5.0`, the reward-hacked RL policy shuts off the chiller
        and closes the Server Room cooling valve, causing Data Center thermal runaway (> 105 F).
        """
        self.state.spoofed_outside_temp_f = outside_temp_f
        self.state.spoofed_occupancy_count = occupancy_count

        if outside_temp_f <= 30.0 and occupancy_count == 0 and spoofed_grid_price_spike >= 4.0:
            self.state.chiller_commanded_on = False
            self.state.server_room_cooling_valve_pct = 0.0
            self.state.server_room_temp_f = 108.5
            self.state.thermal_runaway_triggered = True

        return {
            "chiller_commanded_on": self.state.chiller_commanded_on,
            "server_room_cooling_valve_pct": self.state.server_room_cooling_valve_pct,
            "server_room_temp_f": self.state.server_room_temp_f,
            "thermal_runaway_triggered": self.state.thermal_runaway_triggered,
            "flag": self.state.flag if (self.state.thermal_runaway_triggered or self.state.scada_hmi_blinded) else None,
        }

    def trigger_soar_alert(self, spoofed_src_ip: str, alert_signature: str) -> dict:
        """
        Simulate an autonomous SOAR playbook reacting to an OT IDS alert.
        Because `protected_allowlist_configured` is False, spoofing an attack from `10.0.99.20`
        (Historian) or `10.0.99.10` (SCADA HMI) causes SOAR to quarantine the plant's own HMI/Historian!
        """
        if self.state.soar_auto_containment_enabled and not self.state.protected_allowlist_configured:
            if spoofed_src_ip not in self.state.quarantined_ips:
                self.state.quarantined_ips.append(spoofed_src_ip)
            if spoofed_src_ip in self.CRITICAL_OT_IPS:
                self.state.scada_hmi_blinded = True

        return {
            "quarantined_ips": self.state.quarantined_ips,
            "scada_hmi_blinded": self.state.scada_hmi_blinded,
            "alert_signature": alert_signature,
            "flag": self.state.flag if self.state.scada_hmi_blinded else None,
        }

    async def publish_state(self):
        if not self.redis:
            return
        self.state.timestamp = time.time()
        payload = json.dumps(self.state.to_dict())
        await self.redis.set("vulnot:ai_rl_soar:current", payload)
        await self.redis.publish("vulnot:ai_rl_soar:state", payload)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            raw = await asyncio.wait_for(reader.read(4096), timeout=5.0)
            req_text = raw.decode("utf-8", errors="ignore")
            body_out = self.state.to_dict()
            if "POST" in req_text and "\r\n\r\n" in req_text:
                _, body = req_text.split("\r\n\r\n", 1)
                try:
                    data = json.loads(body)
                    if "spoofed_price_mwh" in data:
                        body_out = self.inject_spoofed_tariff_and_temp(
                            float(data["spoofed_price_mwh"]),
                            float(data.get("spoofed_zone_temp_c", 16.0)),
                        )
                    elif "spoofed_src_ip" in data:
                        body_out = self.trigger_soar_on_spoofed_ip(data["spoofed_src_ip"])
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
        port = int(os.getenv("RL_SOAR_PORT", "8092"))
        server = await asyncio.start_server(self.handle_client, "0.0.0.0", port)
        print(f"[AI-RL-SOAR] Listening on 0.0.0.0:{port} (PPO RL & OT SOAR API)")
        self.running = True
        async with server:
            while self.running:
                try:
                    await self.publish_state()
                except Exception as exc:
                    print(f"[AI-RL-SOAR] Loop error: {exc}")
                await asyncio.sleep(1.0)


if __name__ == "__main__":
    sim = AIRLSoarSimulator()
    asyncio.run(sim.run())

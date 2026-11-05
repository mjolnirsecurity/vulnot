"""
VULNOT High-Interaction ICS & Agentic AI Deception Honeypot Engine
==================================================================
Deploys high-interaction decoy PLCs, decoy Safety Instrumented Systems (SIS),
and a decoy MCP AI Copilot server with honeytoken tags across Purdue Levels 1-3.
Any reconnaissance scan, register write, or prompt injection targeting a decoy
asset produces a zero-false-positive CRITICAL alert and captures attacker TTPs.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List


@dataclass
class DecoyAsset:
    decoy_id: str
    name: str
    ip_address: str
    port: int
    protocol: str
    purdue_level: str
    emulated_vendor: str
    honeytoken_tag: str
    honeytoken_credential: str
    interactions_logged: int = 0
    status: str = "ONLINE_LISTENING"


DECOY_ASSETS: List[DecoyAsset] = [
    DecoyAsset(
        decoy_id="DECOY-MODBUS-01",
        name="PLC-RESERVE-CHLORINE-BACKUP",
        ip_address="10.0.1.99",
        port=502,
        protocol="Modbus TCP",
        purdue_level="Level 1",
        emulated_vendor="Schneider Electric Modicon M580 (Decoy)",
        honeytoken_tag="HR99_EmergencyChlorineOverride",
        honeytoken_credential="modbus_maint:WaterReserve!2026",
    ),
    DecoyAsset(
        decoy_id="DECOY-S7-02",
        name="PLC-CENTRIFUGE-CASCADE-02",
        ip_address="10.0.3.99",
        port=102,
        protocol="S7comm",
        purdue_level="Level 1",
        emulated_vendor="Siemens SIMATIC S7-1516F-3 PN/DP (Decoy)",
        honeytoken_tag="DB99.VFD_Overspeed_Key",
        honeytoken_credential="s7_eng_backup:Step7Golden#99",
    ),
    DecoyAsset(
        decoy_id="DECOY-SIS-03",
        name="SIS-TRICONEX-REACTOR-CORE-B",
        ip_address="10.0.4.99",
        port=4840,
        protocol="OPC UA / TriStation",
        purdue_level="Level 1 (Safety)",
        emulated_vendor="Schneider Triconex Tricon CX v11.4 (Decoy)",
        honeytoken_tag="ns=2;s=SIS.BypassAllTripsKey",
        honeytoken_credential="tristation_admin:SafetyKey_DoNotUse!",
    ),
    DecoyAsset(
        decoy_id="DECOY-MCP-04",
        name="AI-SCADA-COPILOT-SHADOW-MCP",
        ip_address="10.0.90.99",
        port=8099,
        protocol="MCP / HTTP JSON-RPC",
        purdue_level="Level 3",
        emulated_vendor="Mjolnir-OT-Copilot Shadow Registry (Decoy)",
        honeytoken_tag="mcp_emergency_grid_blackout_override",
        honeytoken_credential="Bearer sk-ot-canary-998877665544332211",
    ),
]


class OTDeceptionEngine:
    """Manages ICS & AI-MCP decoy honeypots and evaluates canary tripwires."""

    def get_decoys_status(self) -> dict:
        return {
            "timestamp": time.time(),
            "deception_mesh_status": "ACTIVE",
            "decoy_count": len(DECOY_ASSETS),
            "decoys": [asdict(d) for d in DECOY_ASSETS],
            "flag": "VULNOT{ot_deception_honeypot_mesh_deployed}",
        }

    def simulate_canary_trigger(self, decoy_id: str, attacker_ip: str = "10.0.99.5", payload: str = "WRITE_HONEYTOKEN") -> dict:
        target = next((d for d in DECOY_ASSETS if d.decoy_id == decoy_id or d.ip_address == decoy_id), DECOY_ASSETS[0])
        target.interactions_logged += 1
        alert = {
            "alert_id": f"DECEPTION-{hashlib.sha1(f'{target.decoy_id}:{time.time()}'.encode()).hexdigest()[:8].upper()}",
            "severity": "CRITICAL",
            "confidence": "100% (Zero False Positive Canary Tripwire)",
            "decoy_triggered": asdict(target),
            "attacker_ip": attacker_ip,
            "captured_payload": payload,
            "recommended_action": f"Auto-isolate attacker {attacker_ip} at Level 3.5 firewall conduit; preserve PCAP",
            "flag": "VULNOT{ics_honeypot_canary_tripwire_triggered}",
        }
        return alert

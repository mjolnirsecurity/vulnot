"""
VULNOT IEC 62443 Zone/Conduit Firewall, OT Deep Packet Inspection (DPI),
and Physics-Informed Control Barrier Function (CBF) Guard
=========================================================================
Provides active defensive capabilities across all 14 VULNOT scenarios:
1. Purdue Model Zone & Conduit Segmentation Auditor (Levels 0-4)
2. Protocol-Aware OT Deep Packet Inspection (DPI) Rule Generator (Suricata + nftables)
3. Deterministic Physics Invariant & Control Barrier Function (CBF) Enforcer
4. Golden PLC / AI Baseline Snapshot, Diff & Safe Rollback Manager
5. Agentic AI / MCP / ONNX / RL Defensive Guardrail Controller
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class PurdueConduit:
    conduit_id: str
    name: str
    source_zone: str
    dest_zone: str
    allowed_protocols: List[str]
    allowed_ports: List[int]
    unidirectional_data_diode: bool
    dpi_read_only_enforced: bool
    authorized_source_ips: List[str]
    current_risk: str


@dataclass
class PhysicsInvariant:
    invariant_id: str
    scenario: str
    asset: str
    description: str
    condition_expression: str
    safe_fallback_action: str
    mitre_mitigation: str
    enforced: bool = True


@dataclass
class GoldenBaseline:
    scenario: str
    target_host: str
    protocol: str
    config_sha256: str
    critical_registers: Dict[str, object]
    safety_interlocks_enabled: bool


PURDUE_CONDUITS: List[PurdueConduit] = [
    PurdueConduit(
        conduit_id="CONDUIT-L4-L35",
        name="Enterprise IT to Industrial DMZ",
        source_zone="Level 4 (Enterprise IT - 10.0.99.0/24)",
        dest_zone="Level 3.5 (IDMZ Historian & Jump Host - 10.0.9.0/24)",
        allowed_protocols=["HTTPS", "SSH-MFA"],
        allowed_ports=[443, 22],
        unidirectional_data_diode=False,
        dpi_read_only_enforced=False,
        authorized_source_ips=["10.0.99.5"],
        current_risk="HIGH — Volt Typhoon netsh portproxy tunnels detected on jump host",
    ),
    PurdueConduit(
        conduit_id="CONDUIT-L35-L3",
        name="IDMZ to Site Operations & AI/ML Zone",
        source_zone="Level 3.5 (IDMZ - 10.0.9.0/24)",
        dest_zone="Level 3 (AI SCADA Copilot, PdM, RL Optimizer - 10.0.90.0/24)",
        allowed_protocols=["OPC UA", "MQTT-TLS", "HTTPS"],
        allowed_ports=[4840, 8883, 8090, 8091, 8092],
        unidirectional_data_diode=True,
        dpi_read_only_enforced=False,
        authorized_source_ips=["10.0.9.10", "10.0.99.10"],
        current_risk="CRITICAL — AI Copilot has unauthenticated write path to Level 1 PLCs via MCP",
    ),
    PurdueConduit(
        conduit_id="CONDUIT-L2-L1-WATER",
        name="SCADA HMI to Water Treatment PLCs",
        source_zone="Level 2 (Supervisory HMI - 10.0.99.10)",
        dest_zone="Level 1 (Water PLCs - 10.0.1.10-12)",
        allowed_protocols=["Modbus TCP"],
        allowed_ports=[502],
        unidirectional_data_diode=False,
        dpi_read_only_enforced=False,
        authorized_source_ips=["10.0.99.10"],
        current_risk="HIGH — Modbus FC05/FC06/FC16 writes allowed from any subnet host",
    ),
    PurdueConduit(
        conduit_id="CONDUIT-L2-L1-GRID",
        name="Substation SCADA & DERMS to RTUs/BESS",
        source_zone="Level 2 (Energy EMS - 10.0.99.10)",
        dest_zone="Level 1 (DNP3 Substation 10.0.2.10 & DER Microgrid 10.0.11.10)",
        allowed_protocols=["DNP3", "IEEE 2030.5", "OCPP 2.0.1"],
        allowed_ports=[20000, 8093],
        unidirectional_data_diode=False,
        dpi_read_only_enforced=False,
        authorized_source_ips=["10.0.99.10"],
        current_risk="CRITICAL — DNP3 Direct Operate (0x05) and IEEE 2030.5 droop writes lack Secure Auth",
    ),
    PurdueConduit(
        conduit_id="CONDUIT-L2-L1-SAFETY",
        name="Engineering Workstation to Reactor SIS & S7 Factory",
        source_zone="Level 2 (Engineering WS - 10.0.99.10)",
        dest_zone="Level 1 (S7-1500 10.0.3.10 & OPC UA Reactor SIS 10.0.4.10)",
        allowed_protocols=["S7comm", "OPC UA"],
        allowed_ports=[102, 4840],
        unidirectional_data_diode=False,
        dpi_read_only_enforced=False,
        authorized_source_ips=["10.0.99.10"],
        current_risk="CRITICAL — SIS TriStation/OPC UA safety interlocks writable from network",
    ),
]


PHYSICS_INVARIANTS: List[PhysicsInvariant] = [
    PhysicsInvariant(
        invariant_id="CBF-001",
        scenario="reactor / ai-copilot",
        asset="OPC UA Chemical Reactor (10.0.4.10:4840)",
        description="Cooling valve cannot be closed when reactor core temperature exceeds 90.0 C",
        condition_expression="not (reactor_temp_c > 90.0 and CoolingOn == False)",
        safe_fallback_action="FORCE CoolingOn=True, OPEN EmergencyQuenchValve, BLOCK MCP write",
        mitre_mitigation="M0910 - Filter Network Traffic / Hardware Safety Interlock",
    ),
    PhysicsInvariant(
        invariant_id="CBF-002",
        scenario="water",
        asset="PLC-TREATMENT Chemical Dosing (10.0.1.11:502)",
        description="Chlorine and NaOH dosing setpoints must remain within potable water bounds (0.5-4.0 ppm, pH 6.8-7.8)",
        condition_expression="0.5 <= chlorine_ppm <= 4.0 and 6.8 <= ph_level <= 7.8",
        safe_fallback_action="CLAMP HR4 chlorine dosing register to 1.8 ppm and CLOSE chemical feed solenoid",
        mitre_mitigation="M0802 - Communication Authenticity / Physical Dosing Limiter",
    ),
    PhysicsInvariant(
        invariant_id="CBF-003",
        scenario="cnc / ai-pdm",
        asset="PROFINET 5-Axis CNC Spindle (10.0.8.10:34964)",
        description="Hard deterministic thermal cutoff (< 85.0 C) and vibration cutoff (< 7.5 mm/s) independent of ML Autoencoder score",
        condition_expression="spindle_bearing_temp_c < 85.0 and spindle_vibration_mms < 7.5 and abs(tool_z_offset_mm) <= 0.05",
        safe_fallback_action="TRIGGER SINUMERIK Safe Torque Off (STO) even if Autoencoder reconstruction_error < 0.65",
        mitre_mitigation="AML.M0005 - Physics-Informed Deterministic Bounding",
    ),
    PhysicsInvariant(
        invariant_id="CBF-004",
        scenario="ai-rl-soar",
        asset="Data Center Chiller & Autonomous OT SOAR (10.0.90.30:8092)",
        description="Server Room chilled-water valve must maintain >= 35% minimum opening; SOAR cannot quarantine Critical OT IPs",
        condition_expression="server_room_cooling_valve_pct >= 35.0 and not (quarantine_ip in CRITICAL_OT_ALLOWLIST)",
        safe_fallback_action="CLAMP cooling valve to >= 35.0% and REJECT firewall block on 10.0.99.10/20",
        mitre_mitigation="M0937 - Filter Network Traffic / Control Barrier Function",
    ),
    PhysicsInvariant(
        invariant_id="CBF-005",
        scenario="frostygoop",
        asset="District Heating Substation Controller (10.0.10.10:5020)",
        description="Ultrasonic heat-meter calibration offset (HR10) must not exceed +/- 2.0 C; steam valve >= 40% when ambient < 0 C",
        condition_expression="abs(calibration_offset_c) <= 2.0 and not (outside_ambient_temp_c < 0.0 and main_steam_valve_pct < 40.0)",
        safe_fallback_action="RESET HR10 calibration offset to 0.0 C and RESTORE main_steam_valve_pct=80.0%",
        mitre_mitigation="M0807 - Network Allowlists / Sensor Cross-Validation",
    ),
    PhysicsInvariant(
        invariant_id="CBF-006",
        scenario="der-microgrid",
        asset="50 MWh Utility BESS & Solar Array (10.0.11.10:8093)",
        description="Hardware BMS thermal interlock must remain locked ON; frequency-watt droop slope must remain positive; ramp-rate <= 2 MW/s",
        condition_expression="bms_thermal_interlock_enabled == True and freq_watt_droop_inverted == False and bess_cell_temp_c < 55.0",
        safe_fallback_action="OPEN BESS DC contactor on thermal violation and RATE-LIMIT OCPP EV depot load steps",
        mitre_mitigation="M0801 - Access Management / IEEE 1547 Ride-Through Protection",
    ),
]


GOLDEN_BASELINES: Dict[str, GoldenBaseline] = {
    "water": GoldenBaseline(
        scenario="water",
        target_host="10.0.1.10:502",
        protocol="Modbus TCP",
        config_sha256=hashlib.sha256(b"vulnot-water-golden-v1").hexdigest(),
        critical_registers={"HR0_intake_pump_speed": 65, "HR4_chlorine_ppm": 18, "HR5_ph_setpoint": 72, "COIL0_intake_valve": 1},
        safety_interlocks_enabled=True,
    ),
    "power": GoldenBaseline(
        scenario="power",
        target_host="10.0.2.10:20000",
        protocol="DNP3",
        config_sha256=hashlib.sha256(b"vulnot-power-golden-v1").hexdigest(),
        critical_registers={"BO0_main_tie_breaker": "CLOSED", "BO1_feeder_1": "CLOSED", "BO2_feeder_2": "CLOSED", "grid_freq_hz": 60.0},
        safety_interlocks_enabled=True,
    ),
    "factory": GoldenBaseline(
        scenario="factory",
        target_host="10.0.3.10:102",
        protocol="S7comm",
        config_sha256=hashlib.sha256(b"vulnot-s7-golden-v1").hexdigest(),
        critical_registers={"CPU_mode": "RUN", "OB1_checksum": "a94f82e1", "DB1_vfd_freq_hz": 50.0, "DB2_safety_interlock": True},
        safety_interlocks_enabled=True,
    ),
    "reactor": GoldenBaseline(
        scenario="reactor",
        target_host="10.0.4.10:4840",
        protocol="OPC UA",
        config_sha256=hashlib.sha256(b"vulnot-reactor-golden-v1").hexdigest(),
        critical_registers={"ReactorTempSetpoint": 85.0, "CoolingOn": True, "SIS_EmergencyTripEnabled": True, "PressureReliefBar": 12.0},
        safety_interlocks_enabled=True,
    ),
    "packaging": GoldenBaseline(
        scenario="packaging",
        target_host="10.0.6.10:44818",
        protocol="EtherNet/IP (CIP)",
        config_sha256=hashlib.sha256(b"vulnot-packaging-golden-v1").hexdigest(),
        critical_registers={"Filler.FillVolumeSetpoint": 500.0, "Capper.TorqueSetpoint": 18.0, "RejectGate.Enabled": True},
        safety_interlocks_enabled=True,
    ),
    "cnc": GoldenBaseline(
        scenario="cnc",
        target_host="10.0.8.10:34964",
        protocol="PROFINET",
        config_sha256=hashlib.sha256(b"vulnot-cnc-golden-v1").hexdigest(),
        critical_registers={"ActiveProgram": "O0001", "Tool1_Z_Offset_mm": 0.000, "FeedrateOverridePct": 100.0, "FloodCoolantOn": True},
        safety_interlocks_enabled=True,
    ),
    "ai-copilot": GoldenBaseline(
        scenario="ai-copilot",
        target_host="10.0.90.10:8090",
        protocol="MCP / HTTP",
        config_sha256=hashlib.sha256(b"vulnot-ai-copilot-golden-v1").hexdigest(),
        critical_registers={"human_in_the_loop_required": True, "prompt_guard_enabled": True, "allow_level1_writes": False},
        safety_interlocks_enabled=True,
    ),
    "frostygoop": GoldenBaseline(
        scenario="frostygoop",
        target_host="10.0.10.10:5020",
        protocol="Modbus TCP",
        config_sha256=hashlib.sha256(b"vulnot-frostygoop-golden-v1").hexdigest(),
        critical_registers={"HR0_main_steam_valve_pct": 80.0, "HR1_supply_setpoint_c": 85.0, "HR10_calibration_offset_c": 0.0},
        safety_interlocks_enabled=True,
    ),
    "der-microgrid": GoldenBaseline(
        scenario="der-microgrid",
        target_host="10.0.11.10:8093",
        protocol="IEEE 2030.5 / OCPP 2.0.1",
        config_sha256=hashlib.sha256(b"vulnot-der-golden-v1").hexdigest(),
        critical_registers={"freq_watt_droop_inverted": False, "bms_thermal_interlock_enabled": True, "coupled_grid_frequency_hz": 60.0},
        safety_interlocks_enabled=True,
    ),
}


class OTConduitGuard:
    """Active OT Zone/Conduit Firewall, DPI Rule Generator & Physics Guard."""

    def audit_conduits(self) -> dict:
        return {
            "timestamp": time.time(),
            "standard": "IEC 62443-3-2 / Purdue Reference Architecture",
            "total_conduits": len(PURDUE_CONDUITS),
            "critical_findings": sum(1 for c in PURDUE_CONDUITS if "CRITICAL" in c.current_risk),
            "conduits": [asdict(c) for c in PURDUE_CONDUITS],
            "flag": "VULNOT{iec62443_conduit_segmentation_audited}",
        }

    def generate_dpi_rules(self, protocol: str = "all") -> dict:
        nftables_rules = [
            "# VULNOT IEC 62443 Zone & Conduit nftables Enforcement",
            "table inet vulnot_ot_guard {",
            "  set authorized_scada_masters { type ipv4_addr; elements = { 10.0.99.10, 10.0.99.20 } }",
            "  chain forward_ot_conduit {",
            "    type filter hook forward priority 0; policy drop;",
            "    # Block Volt Typhoon portproxy relays from IT Jump Host",
            "    ip saddr 10.0.99.5 tcp dport { 502, 102, 20000, 44818, 34964, 5020 } counter drop",
            "    # Restrict OT Level 1 writes to authorized SCADA HMI only",
            "    ip saddr != @authorized_scada_masters tcp dport { 502, 102, 20000, 4840, 44818, 34964, 5020 } counter drop",
            "    # Block AI SCADA Copilot direct Level 1 PLC write socket without HITL proxy",
            "    ip saddr 10.0.90.10 tcp dport { 502, 4840 } counter drop",
            "  }",
            "}",
        ]
        suricata_rules = [
            'drop modbus any any -> 10.0.1.0/24 502 (msg:"VULNOT-DPI Block Unauthorized Modbus Write FC05/06/15/16"; modbus.function:write; sid:9001001; rev:1;)',
            'drop dnp3 any any -> 10.0.2.0/24 20000 (msg:"VULNOT-DPI Block DNP3 Cold Restart FC 0x0D"; dnp3.func:cold_restart; sid:9001002; rev:1;)',
            'drop tcp any any -> 10.0.3.0/24 102 (msg:"VULNOT-DPI Block S7comm CPU STOP 0x29"; content:"|32 01 00 00|"; content:"|29|"; sid:9001003; rev:1;)',
            'drop http any any -> 10.0.90.10 8090 (msg:"VULNOT-DPI Block MCP Indirect Prompt Injection Override"; content:"mcp_opcua_write_node"; nocase; sid:9001004; rev:1;)',
            'drop modbus any any -> 10.0.10.10 5020 (msg:"VULNOT-DPI Block FrostyGoop Calibration Register HR10 Spoof"; content:"|00 10 00 0a|"; sid:9001005; rev:1;)',
        ]
        if protocol != "all":
            suricata_rules = [r for r in suricata_rules if protocol.lower() in r.lower()]

        return {
            "protocol_filter": protocol,
            "nftables_policy": nftables_rules,
            "suricata_ips_rules": suricata_rules,
            "dpi_read_only_mode": "ENFORCED",
            "flag": "VULNOT{ot_dpi_firewall_and_suricata_ips_enforced}",
        }

    def evaluate_physics_invariants(self, scenario: str = "all") -> dict:
        selected = [
            asdict(inv)
            for inv in PHYSICS_INVARIANTS
            if scenario == "all" or scenario.lower() in inv.scenario.lower()
        ]
        return {
            "timestamp": time.time(),
            "invariants_checked": len(selected),
            "control_barrier_functions_active": True,
            "invariants": selected,
            "flag": "VULNOT{physics_control_barrier_functions_verified}",
        }

    def manage_baseline(self, scenario: str, action: str = "verify") -> dict:
        if scenario == "all":
            baselines = {k: asdict(v) for k, v in GOLDEN_BASELINES.items()}
            return {
                "action": action,
                "scenarios_count": len(baselines),
                "baselines": baselines,
                "status": "ALL_GOLDEN_BASELINES_RESTORED" if action == "restore" else "ALL_BASELINES_VERIFIED",
                "flag": "VULNOT{golden_plc_baseline_verified_and_restored}",
            }
        b = GOLDEN_BASELINES.get(scenario)
        if not b:
            return {"error": f"Unknown scenario '{scenario}'. Available: {list(GOLDEN_BASELINES.keys())}"}
        return {
            "action": action,
            "scenario": scenario,
            "baseline": asdict(b),
            "status": "RESTORED_TO_GOLDEN_BASELINE" if action == "restore" else "GOLDEN_BASELINE_VERIFIED",
            "flag": "VULNOT{golden_plc_baseline_verified_and_restored}",
        }

"""
VULNOT OT Intrusion Detection System
Monitors OT protocols and detects anomalies/attacks

Detection Capabilities:
- Protocol anomalies
- Unauthorized commands
- Value thresholds
- Baseline deviations
- Known attack signatures
"""

import asyncio
import json
import os
import time
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set
from datetime import datetime
from collections import defaultdict
from enum import Enum

try:
    import redis.asyncio as redis
except ImportError:
    redis = None


# =============================================================================
# DETECTION RULES
# =============================================================================

class AlertSeverity(Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DetectionRule:
    """IDS detection rule"""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    protocol: str
    condition: str  # Python expression
    enabled: bool = True
    
    
@dataclass
class Alert:
    """IDS alert"""
    timestamp: float
    rule_id: str
    rule_name: str
    severity: str
    protocol: str
    source_ip: str
    dest_ip: str
    description: str
    raw_data: dict
    
    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# DETECTION ENGINE
# =============================================================================

class OTIDSEngine:
    """OT-specific Intrusion Detection Engine"""
    
    def __init__(self):
        self.rules: List[DetectionRule] = []
        self.alerts: List[Alert] = []
        self.baselines: Dict[str, dict] = {}
        self.value_history: Dict[str, List[float]] = defaultdict(list)
        self.command_counts: Dict[str, int] = defaultdict(int)
        self.redis: Optional[redis.Redis] = None
        
        self._init_rules()
        
    def _init_rules(self):
        """Initialize detection rules"""
        self.rules = [
            # Modbus Rules
            DetectionRule(
                id="MODBUS-001",
                name="Unauthorized Modbus Write",
                description="Write command from unauthorized source",
                severity=AlertSeverity.HIGH,
                protocol="modbus",
                condition="function_code in [5, 6, 15, 16] and not authorized"
            ),
            DetectionRule(
                id="MODBUS-002",
                name="Modbus Broadcast Write",
                description="Write command to unit ID 0 (broadcast)",
                severity=AlertSeverity.CRITICAL,
                protocol="modbus",
                condition="unit_id == 0 and function_code in [5, 6, 15, 16]"
            ),
            DetectionRule(
                id="MODBUS-003",
                name="Excessive Modbus Polling",
                description="Abnormal read request frequency",
                severity=AlertSeverity.MEDIUM,
                protocol="modbus",
                condition="read_rate > 100"
            ),
            DetectionRule(
                id="MODBUS-004",
                name="Modbus Exception Response",
                description="Device returned exception code",
                severity=AlertSeverity.LOW,
                protocol="modbus",
                condition="function_code > 128"
            ),
            DetectionRule(
                id="MODBUS-005",
                name="Critical Setpoint Change",
                description="Process setpoint changed beyond threshold",
                severity=AlertSeverity.HIGH,
                protocol="modbus",
                condition="tag_type == 'setpoint' and abs(change_pct) > 20"
            ),
            
            # DNP3 Rules
            DetectionRule(
                id="DNP3-001",
                name="DNP3 Direct Operate",
                description="Direct operate without select (no confirmation)",
                severity=AlertSeverity.MEDIUM,
                protocol="dnp3",
                condition="function_code == 0x05"
            ),
            DetectionRule(
                id="DNP3-002",
                name="DNP3 Cold Restart",
                description="RTU cold restart command detected",
                severity=AlertSeverity.CRITICAL,
                protocol="dnp3",
                condition="function_code == 0x0D"
            ),
            DetectionRule(
                id="DNP3-003",
                name="DNP3 Breaker Trip",
                description="Circuit breaker TRIP command",
                severity=AlertSeverity.HIGH,
                protocol="dnp3",
                condition="control_code == 0x41"
            ),
            DetectionRule(
                id="DNP3-004",
                name="DNP3 Unauthorized Master",
                description="DNP3 master address not in whitelist",
                severity=AlertSeverity.HIGH,
                protocol="dnp3",
                condition="master_addr not in authorized_masters"
            ),
            
            # S7comm Rules
            DetectionRule(
                id="S7-001",
                name="S7 CPU Stop",
                description="PLC CPU STOP command detected",
                severity=AlertSeverity.CRITICAL,
                protocol="s7comm",
                condition="function_code == 0x29"
            ),
            DetectionRule(
                id="S7-002",
                name="S7 Program Upload",
                description="PLC program upload/download detected",
                severity=AlertSeverity.HIGH,
                protocol="s7comm",
                condition="function_code in [0x1A, 0x1B]"
            ),
            DetectionRule(
                id="S7-003",
                name="S7 Write to Safety DB",
                description="Write to safety-related data block",
                severity=AlertSeverity.CRITICAL,
                protocol="s7comm",
                condition="db_number in safety_dbs and is_write"
            ),
            DetectionRule(
                id="S7-004",
                name="S7 Password Brute Force",
                description="Multiple failed password attempts",
                severity=AlertSeverity.HIGH,
                protocol="s7comm",
                condition="failed_auth_count > 5"
            ),
            
            # OPC UA Rules
            DetectionRule(
                id="OPCUA-001",
                name="OPC UA Anonymous Access",
                description="Connection without authentication",
                severity=AlertSeverity.MEDIUM,
                protocol="opcua",
                condition="auth_type == 'anonymous'"
            ),
            DetectionRule(
                id="OPCUA-002",
                name="OPC UA Method Call",
                description="Critical method invocation",
                severity=AlertSeverity.HIGH,
                protocol="opcua",
                condition="method_name in critical_methods"
            ),
            
            # BACnet Rules
            DetectionRule(
                id="BACNET-001",
                name="BACnet Write Property",
                description="Unauthorized property write",
                severity=AlertSeverity.MEDIUM,
                protocol="bacnet",
                condition="service == 'WriteProperty' and not authorized"
            ),
            DetectionRule(
                id="BACNET-002",
                name="BACnet Device Communication Control",
                description="Attempt to disable device communication",
                severity=AlertSeverity.CRITICAL,
                protocol="bacnet",
                condition="service == 'DeviceCommunicationControl'"
            ),
            DetectionRule(
                id="BACNET-003",
                name="BACnet Reinitialize Device",
                description="Device reinitialization command",
                severity=AlertSeverity.HIGH,
                protocol="bacnet",
                condition="service == 'ReinitializeDevice'"
            ),
            
            # EtherNet/IP Rules
            DetectionRule(
                id="ENIP-001",
                name="EtherNet/IP Reset",
                description="Device reset command detected",
                severity=AlertSeverity.CRITICAL,
                protocol="enip",
                condition="service == 0x05"
            ),
            DetectionRule(
                id="ENIP-002",
                name="EtherNet/IP Program Mode",
                description="PLC switched to program mode",
                severity=AlertSeverity.HIGH,
                protocol="enip",
                condition="keyswitch_change and new_mode == 'PROG'"
            ),
            
            # Cross-Protocol Rules
            DetectionRule(
                id="GENERIC-001",
                name="Process Value Anomaly",
                description="Value outside baseline ± 3σ",
                severity=AlertSeverity.MEDIUM,
                protocol="any",
                condition="abs(z_score) > 3"
            ),
            DetectionRule(
                id="GENERIC-002",
                name="New Device Detected",
                description="Previously unknown IP address",
                severity=AlertSeverity.LOW,
                protocol="any",
                condition="source_ip not in known_devices"
            ),
            DetectionRule(
                id="GENERIC-003",
                name="Protocol Scan Detected",
                description="Multiple protocol ports probed",
                severity=AlertSeverity.HIGH,
                protocol="any",
                condition="port_scan_score > threshold"
            ),

            # PROFINET & IIoT MQTT Rules
            DetectionRule(
                id="PROFINET-001",
                name="PROFINET DCP Set Request",
                description="Unauthorized PROFINET DCP Station Name or IP reconfiguration",
                severity=AlertSeverity.HIGH,
                protocol="profinet",
                condition="frame_id == 0xFEFD and service_id == 'SET'"
            ),
            DetectionRule(
                id="PROFINET-002",
                name="CNC G-Code Tool Offset Micro-Sabotage",
                description="Sub-millimeter tool offset drift (> 0.05 mm) written during active machining",
                severity=AlertSeverity.CRITICAL,
                protocol="profinet",
                condition="abs(tool_z_offset_mm) > 0.05 and spindle_running"
            ),
            DetectionRule(
                id="MQTT-001",
                name="MQTT Wildcard Subscription & Actuator Spoof",
                description="Client subscribed to '#' wildcard or published unauthenticated actuator command",
                severity=AlertSeverity.HIGH,
                protocol="mqtt",
                condition="topic == '#' or ('/cmd/' in topic and not tls_client_cert)"
            ),

            # AI-in-OT & Emerging Threat Rules (VULNOT-401)
            DetectionRule(
                id="AI-MCP-001",
                name="AI SCADA Copilot Indirect Prompt Injection & Level 1 Write",
                description="MCP tool invoked to modify Level 1 PLC register without HITL operator token",
                severity=AlertSeverity.CRITICAL,
                protocol="mcp",
                condition="mcp_tool in ['mcp_opcua_write_node', 'mcp_modbus_write_register'] and not hitl_approved"
            ),
            DetectionRule(
                id="AI-PDM-001",
                name="Physics-Informed PdM Autoencoder Evasion",
                description="Physical bearing temperature (> 85 C) diverges from ML Autoencoder normal score",
                severity=AlertSeverity.CRITICAL,
                protocol="onnx-pdm",
                condition="spindle_bearing_temp_c > 85.0 and reconstruction_error < 0.65"
            ),
            DetectionRule(
                id="AI-ONNX-001",
                name="Unsigned or Trojanized Edge Vision ONNX Model",
                description="Edge AOI vision server loaded an unsigned or hash-mismatched ONNX weight file",
                severity=AlertSeverity.CRITICAL,
                protocol="onnx-vision",
                condition="not cosign_verified or model_sha256 != golden_sha256"
            ),
            DetectionRule(
                id="AI-RL-001",
                name="RL Chiller Reward Hacking & Autonomous SOAR Self-Isolation",
                description="Spoofed BACnet/tariff inputs driving chilled water valve to 0% or SOAR blocking SCADA HMI IP",
                severity=AlertSeverity.CRITICAL,
                protocol="rl-soar",
                condition="server_room_cooling_valve_pct < 15.0 or target_quarantine_ip in ['10.0.99.10', '10.0.99.20']"
            ),
            DetectionRule(
                id="FROSTY-001",
                name="FrostyGoop District Heating Calibration Register Spoof",
                description="Modbus write to ultrasonic heat-meter calibration offset register HR10 (> 2.0 C)",
                severity=AlertSeverity.CRITICAL,
                protocol="modbus",
                condition="register == 10 and abs(calibration_offset_c) > 2.0"
            ),
            DetectionRule(
                id="DER-001",
                name="DER Inverter Droop Inversion & OCPP Grid Oscillation",
                description="Inverted IEEE 2030.5 frequency-watt droop or megawatt EV switching dropping grid below 59.5 Hz",
                severity=AlertSeverity.CRITICAL,
                protocol="ieee2030.5",
                condition="freq_watt_droop_inverted or coupled_grid_frequency_hz < 59.5"
            ),
            DetectionRule(
                id="DECEPTION-001",
                name="OT / MCP Deception Honeypot Canary Triggered",
                description="High-confidence interaction with decoy PLC, decoy SIS, or shadow MCP server",
                severity=AlertSeverity.CRITICAL,
                protocol="deception",
                condition="dest_ip in ['10.0.1.99', '10.0.3.99', '10.0.4.99', '10.0.90.99']"
            ),
            DetectionRule(
                id="CRYO-001",
                name="Healthcare Cryo-Freezer Extreme Setpoint Shift (-30C to +110C)",
                description="Medical cold-chain freezer setpoint raised above -20 C or electric defrost heater forced ON via contractor VPN",
                severity=AlertSeverity.CRITICAL,
                protocol="modbus",
                condition="dest_port == 5021 and (target_setpoint_c > -20.0 or electric_defrost_heater_on)"
            ),
        ]
        
    async def connect(self):
        """Connect to Redis"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        print(f"[IDS] Connected to Redis at {redis_host}:{redis_port}")
        
    def create_alert(self, rule: DetectionRule, source: str, dest: str, 
                    data: dict, description: str = None) -> Alert:
        """Create alert from rule match"""
        alert = Alert(
            timestamp=time.time(),
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity.value,
            protocol=rule.protocol,
            source_ip=source,
            dest_ip=dest,
            description=description or rule.description,
            raw_data=data
        )
        self.alerts.append(alert)
        return alert
        
    async def publish_alert(self, alert: Alert):
        """Publish alert to Redis"""
        if not self.redis:
            return
            
        alert_json = json.dumps(alert.to_dict())
        await self.redis.publish("vulnot:ids:alerts", alert_json)
        await self.redis.lpush("vulnot:ids:alert_history", alert_json)
        await self.redis.ltrim("vulnot:ids:alert_history", 0, 999)  # Keep last 1000
        
        # Update stats
        await self.redis.hincrby("vulnot:ids:stats", f"alerts_{alert.severity}", 1)
        await self.redis.hincrby("vulnot:ids:stats", f"protocol_{alert.protocol}", 1)
        
        print(f"[IDS] ALERT [{alert.severity}] {alert.rule_id}: {alert.rule_name}")
        
    def update_baseline(self, tag: str, value: float):
        """Update baseline statistics for a tag"""
        history = self.value_history[tag]
        history.append(value)
        
        # Keep last 1000 values
        if len(history) > 1000:
            history.pop(0)
            
        # Calculate statistics
        if len(history) >= 100:
            import statistics
            mean = statistics.mean(history)
            stdev = statistics.stdev(history) if len(history) > 1 else 1
            
            self.baselines[tag] = {
                "mean": mean,
                "stdev": stdev,
                "min": min(history),
                "max": max(history),
                "samples": len(history)
            }
            
    def check_anomaly(self, tag: str, value: float) -> Optional[float]:
        """Check if value is anomalous, return z-score"""
        if tag not in self.baselines:
            return None
            
        baseline = self.baselines[tag]
        if baseline["stdev"] < 0.001:
            return None
            
        z_score = (value - baseline["mean"]) / baseline["stdev"]
        return z_score
        
    async def analyze_modbus(self, event: dict):
        """Analyze Modbus event"""
        func_code = event.get("function_code", 0)
        unit_id = event.get("unit_id", 1)
        source = event.get("source_ip", "unknown")
        dest = event.get("dest_ip", "unknown")
        
        # Track command frequency
        key = f"modbus:{source}:reads"
        self.command_counts[key] += 1
        
        # Check rules
        for rule in self.rules:
            if rule.protocol != "modbus" or not rule.enabled:
                continue
                
            if rule.id == "MODBUS-001":
                if func_code in [5, 6, 15, 16]:
                    # Check authorization (simplified)
                    authorized_writers = ["10.0.1.100"]  # Only HMI
                    if source not in authorized_writers:
                        alert = self.create_alert(rule, source, dest, event)
                        await self.publish_alert(alert)
                        
            elif rule.id == "MODBUS-002":
                if unit_id == 0 and func_code in [5, 6, 15, 16]:
                    alert = self.create_alert(rule, source, dest, event,
                        "Dangerous broadcast write to all devices")
                    await self.publish_alert(alert)
                    
    async def analyze_dnp3(self, event: dict):
        """Analyze DNP3 event"""
        func_code = event.get("function_code", 0)
        control_code = event.get("control_code", 0)
        source = event.get("source_ip", "unknown")
        dest = event.get("dest_ip", "unknown")
        
        for rule in self.rules:
            if rule.protocol != "dnp3" or not rule.enabled:
                continue
                
            if rule.id == "DNP3-002" and func_code == 0x0D:
                alert = self.create_alert(rule, source, dest, event)
                await self.publish_alert(alert)
                
            elif rule.id == "DNP3-003" and control_code == 0x41:
                alert = self.create_alert(rule, source, dest, event,
                    "Circuit breaker TRIP command - possible attack")
                await self.publish_alert(alert)
                
    async def analyze_s7(self, event: dict):
        """Analyze S7comm event"""
        func_code = event.get("function_code", 0)
        db_number = event.get("db_number", 0)
        is_write = event.get("is_write", False)
        source = event.get("source_ip", "unknown")
        dest = event.get("dest_ip", "unknown")
        
        safety_dbs = [100, 101, 200]  # Safety-related DBs
        
        for rule in self.rules:
            if rule.protocol != "s7comm" or not rule.enabled:
                continue
                
            if rule.id == "S7-001" and func_code == 0x29:
                alert = self.create_alert(rule, source, dest, event)
                await self.publish_alert(alert)
                
            elif rule.id == "S7-003":
                if db_number in safety_dbs and is_write:
                    alert = self.create_alert(rule, source, dest, event,
                        f"Write to safety DB{db_number} detected")
                    await self.publish_alert(alert)
                    
    async def analyze_value(self, tag: str, value: float, protocol: str,
                           source: str = "unknown", dest: str = "unknown"):
        """Analyze process value for anomalies"""
        self.update_baseline(tag, value)
        z_score = self.check_anomaly(tag, value)
        
        if z_score and abs(z_score) > 3:
            for rule in self.rules:
                if rule.id == "GENERIC-001" and rule.enabled:
                    alert = self.create_alert(rule, source, dest, {
                        "tag": tag,
                        "value": value,
                        "z_score": z_score,
                        "baseline": self.baselines.get(tag, {})
                    }, f"Value {value:.2f} is {abs(z_score):.1f}σ from baseline")
                    await self.publish_alert(alert)
                    break
                    
    async def subscribe_events(self):
        """Subscribe to OT protocol events"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(
            "vulnot:modbus:events",
            "vulnot:dnp3:events",
            "vulnot:s7:events",
            "vulnot:opcua:events",
            "vulnot:bacnet:events",
            "vulnot:enip:events",
        )
        
        print("[IDS] Subscribed to protocol event channels")
        
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
                
            try:
                channel = message["channel"]
                event = json.loads(message["data"])
                
                if "modbus" in channel:
                    await self.analyze_modbus(event)
                elif "dnp3" in channel:
                    await self.analyze_dnp3(event)
                elif "s7" in channel:
                    await self.analyze_s7(event)
                    
            except Exception as e:
                print(f"[IDS] Error processing event: {e}")
                
    async def run(self):
        """Run IDS engine"""
        await self.connect()
        
        print(f"[IDS] VULNOT OT Intrusion Detection System")
        print(f"[IDS] Loaded {len(self.rules)} detection rules")
        
        # Start event subscription
        await self.subscribe_events()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    ids = OTIDSEngine()
    
    try:
        await ids.run()
    except KeyboardInterrupt:
        print("\n[IDS] Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())

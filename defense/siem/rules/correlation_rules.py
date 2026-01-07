"""
VULNOT SIEM Correlation Rules
Advanced correlation rules for OT security event detection

Rule Types:
- Single Event: Match on individual events
- Sequence: Events in specific order within timeframe
- Aggregation: Threshold-based detection
- Behavioral: Baseline deviation detection
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta


class RuleSeverity(Enum):
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class RuleType(Enum):
    SINGLE = "single"
    SEQUENCE = "sequence"
    AGGREGATION = "aggregation"
    BEHAVIORAL = "behavioral"


@dataclass
class CorrelationRule:
    """SIEM Correlation Rule"""
    id: str
    name: str
    description: str
    rule_type: RuleType
    severity: RuleSeverity
    mitre_technique: str
    enabled: bool = True
    
    # Matching conditions
    conditions: Dict = field(default_factory=dict)
    
    # Time window for correlation
    time_window_seconds: int = 60
    
    # Threshold for aggregation rules
    threshold: int = 1
    
    # Sequence for sequence rules
    sequence: List[Dict] = field(default_factory=list)
    
    # Response actions
    actions: List[str] = field(default_factory=list)
    
    # Suppression to avoid alert fatigue
    suppression_seconds: int = 300


# =============================================================================
# OT-SPECIFIC CORRELATION RULES
# =============================================================================

CORRELATION_RULES = [
    # =========================================================================
    # RECONNAISSANCE DETECTION
    # =========================================================================
    
    CorrelationRule(
        id="SIEM-001",
        name="OT Protocol Port Scan",
        description="Detects scanning of multiple OT protocol ports from single source",
        rule_type=RuleType.AGGREGATION,
        severity=RuleSeverity.MEDIUM,
        mitre_technique="T0846",
        conditions={
            "event_type": "connection_attempt",
            "destination_port": ["502", "102", "44818", "47808", "20000", "4840", "1883"],
        },
        threshold=3,
        time_window_seconds=60,
        actions=["alert", "log", "block_source"],
    ),
    
    CorrelationRule(
        id="SIEM-002",
        name="Modbus Device Discovery",
        description="Detects sequential Modbus read attempts to multiple addresses",
        rule_type=RuleType.AGGREGATION,
        severity=RuleSeverity.LOW,
        mitre_technique="T0846",
        conditions={
            "protocol": "modbus",
            "function_code": ["1", "2", "3", "4"],
            "unique_destinations": True,
        },
        threshold=5,
        time_window_seconds=30,
        actions=["alert", "log"],
    ),
    
    # =========================================================================
    # UNAUTHORIZED ACCESS
    # =========================================================================
    
    CorrelationRule(
        id="SIEM-003",
        name="Unauthorized OT Network Access",
        description="Detects OT protocol traffic from non-authorized sources",
        rule_type=RuleType.SINGLE,
        severity=RuleSeverity.HIGH,
        mitre_technique="T0866",
        conditions={
            "protocol": ["modbus", "dnp3", "s7comm", "opcua", "bacnet", "enip"],
            "source_zone": "!authorized_ot_clients",
        },
        actions=["alert", "log", "soc_notification"],
    ),
    
    CorrelationRule(
        id="SIEM-004",
        name="IT-to-OT Lateral Movement",
        description="Detects connections from IT network to OT devices",
        rule_type=RuleType.SINGLE,
        severity=RuleSeverity.HIGH,
        mitre_technique="T0867",
        conditions={
            "source_zone": "IT",
            "destination_zone": "OT",
            "destination_port": ["502", "102", "44818", "47808", "20000", "4840"],
        },
        actions=["alert", "log", "soc_notification", "block"],
    ),
    
    # =========================================================================
    # ATTACK SEQUENCE DETECTION
    # =========================================================================
    
    CorrelationRule(
        id="SIEM-005",
        name="PLC Attack Chain",
        description="Detects recon -> read -> write attack sequence",
        rule_type=RuleType.SEQUENCE,
        severity=RuleSeverity.CRITICAL,
        mitre_technique="T0831",
        sequence=[
            {"event": "modbus_read_holding", "count": 5},
            {"event": "modbus_write_register", "count": 1},
        ],
        time_window_seconds=300,
        actions=["alert", "soc_notification", "block_source", "incident_create"],
    ),
    
    CorrelationRule(
        id="SIEM-006",
        name="DNP3 Breaker Attack Sequence",
        description="Detects read -> select -> operate attack on breakers",
        rule_type=RuleType.SEQUENCE,
        severity=RuleSeverity.CRITICAL,
        mitre_technique="T0831",
        sequence=[
            {"event": "dnp3_read", "count": 1},
            {"event": "dnp3_select", "count": 1},
            {"event": "dnp3_operate", "count": 1},
        ],
        time_window_seconds=60,
        conditions={
            "object_type": "binary_output",
        },
        actions=["alert", "soc_notification", "block_source", "incident_create"],
    ),
    
    CorrelationRule(
        id="SIEM-007",
        name="S7comm PLC Stop Attack",
        description="Detects CPU STOP command preceded by reconnaissance",
        rule_type=RuleType.SEQUENCE,
        severity=RuleSeverity.CRITICAL,
        mitre_technique="T0816",
        sequence=[
            {"event": "s7_read_szl", "count": 1},
            {"event": "s7_cpu_stop", "count": 1},
        ],
        time_window_seconds=120,
        actions=["alert", "soc_notification", "block_source", "incident_create"],
    ),
    
    # =========================================================================
    # PROCESS MANIPULATION
    # =========================================================================
    
    CorrelationRule(
        id="SIEM-008",
        name="Setpoint Manipulation",
        description="Detects multiple setpoint changes in short period",
        rule_type=RuleType.AGGREGATION,
        severity=RuleSeverity.HIGH,
        mitre_technique="T0836",
        conditions={
            "event_type": "setpoint_change",
        },
        threshold=3,
        time_window_seconds=60,
        actions=["alert", "log", "soc_notification"],
    ),
    
    CorrelationRule(
        id="SIEM-009",
        name="Safety System Access",
        description="Any access to safety instrumented systems",
        rule_type=RuleType.SINGLE,
        severity=RuleSeverity.CRITICAL,
        mitre_technique="T0837",
        conditions={
            "destination_zone": "SIS",
            "event_type": ["write", "config_change", "firmware_update"],
        },
        actions=["alert", "soc_notification", "block", "incident_create"],
    ),
    
    # =========================================================================
    # DATA EXFILTRATION
    # =========================================================================
    
    CorrelationRule(
        id="SIEM-010",
        name="Historian Bulk Data Export",
        description="Detects large data exports from historian",
        rule_type=RuleType.AGGREGATION,
        severity=RuleSeverity.HIGH,
        mitre_technique="T0882",
        conditions={
            "destination": "historian",
            "action": "read",
            "data_volume_mb": ">10",
        },
        threshold=1,
        time_window_seconds=300,
        actions=["alert", "log", "soc_notification"],
    ),
    
    CorrelationRule(
        id="SIEM-011",
        name="Historian SQL Injection",
        description="Detects SQL injection attempts against historian",
        rule_type=RuleType.SINGLE,
        severity=RuleSeverity.HIGH,
        mitre_technique="T0890",
        conditions={
            "destination": "historian",
            "payload_contains": ["UNION", "SELECT", "DROP", "--", "1=1"],
        },
        actions=["alert", "log", "block", "soc_notification"],
    ),
    
    # =========================================================================
    # MQTT/IIoT ATTACKS
    # =========================================================================
    
    CorrelationRule(
        id="SIEM-012",
        name="MQTT Wildcard Subscription",
        description="Detects subscription to all topics",
        rule_type=RuleType.SINGLE,
        severity=RuleSeverity.MEDIUM,
        mitre_technique="T0869",
        conditions={
            "protocol": "mqtt",
            "action": "subscribe",
            "topic": "#",
        },
        actions=["alert", "log"],
    ),
    
    CorrelationRule(
        id="SIEM-013",
        name="MQTT Control Topic Injection",
        description="Detects messages to control topics from unauthorized sources",
        rule_type=RuleType.SINGLE,
        severity=RuleSeverity.HIGH,
        mitre_technique="T0831",
        conditions={
            "protocol": "mqtt",
            "action": "publish",
            "topic_contains": ["cmd", "control", "config", "firmware"],
        },
        actions=["alert", "soc_notification", "block"],
    ),
    
    # =========================================================================
    # ANTI-FORENSICS
    # =========================================================================
    
    CorrelationRule(
        id="SIEM-014",
        name="Historian Data Deletion",
        description="Detects deletion of historical data",
        rule_type=RuleType.SINGLE,
        severity=RuleSeverity.CRITICAL,
        mitre_technique="T0872",
        conditions={
            "destination": "historian",
            "action": "delete",
        },
        actions=["alert", "soc_notification", "incident_create"],
    ),
    
    CorrelationRule(
        id="SIEM-015",
        name="Log Clearing Attempt",
        description="Detects attempts to clear security logs",
        rule_type=RuleType.SINGLE,
        severity=RuleSeverity.CRITICAL,
        mitre_technique="T0872",
        conditions={
            "event_type": "log_clear",
        },
        actions=["alert", "soc_notification", "incident_create"],
    ),
    
    # =========================================================================
    # APT DETECTION
    # =========================================================================
    
    CorrelationRule(
        id="SIEM-016",
        name="Multi-Protocol Attack Campaign",
        description="Detects attacks spanning multiple OT protocols",
        rule_type=RuleType.AGGREGATION,
        severity=RuleSeverity.CRITICAL,
        mitre_technique="T0800",
        conditions={
            "event_type": ["write", "control", "stop"],
            "protocols_unique": True,
        },
        threshold=3,
        time_window_seconds=600,
        actions=["alert", "soc_notification", "incident_create", "block_source"],
    ),
    
    CorrelationRule(
        id="SIEM-017",
        name="Ukraine-Style Grid Attack",
        description="Detects coordinated breaker operations across substations",
        rule_type=RuleType.AGGREGATION,
        severity=RuleSeverity.CRITICAL,
        mitre_technique="T0831",
        conditions={
            "protocol": "dnp3",
            "event": "breaker_operate",
            "unique_targets": True,
        },
        threshold=2,
        time_window_seconds=300,
        actions=["alert", "soc_notification", "incident_create", "emergency_response"],
    ),
    
    # =========================================================================
    # BEHAVIORAL ANOMALIES
    # =========================================================================
    
    CorrelationRule(
        id="SIEM-018",
        name="Off-Hours OT Access",
        description="Detects OT system access outside normal hours",
        rule_type=RuleType.BEHAVIORAL,
        severity=RuleSeverity.MEDIUM,
        mitre_technique="T0859",
        conditions={
            "protocol": ["modbus", "dnp3", "s7comm", "opcua"],
            "action": ["write", "control"],
            "time_of_day": "!business_hours",
        },
        actions=["alert", "log"],
    ),
    
    CorrelationRule(
        id="SIEM-019",
        name="Abnormal Command Frequency",
        description="Detects unusual rate of control commands",
        rule_type=RuleType.BEHAVIORAL,
        severity=RuleSeverity.MEDIUM,
        mitre_technique="T0831",
        conditions={
            "event_type": "control_command",
            "rate": ">3x_baseline",
        },
        actions=["alert", "log"],
    ),
    
    CorrelationRule(
        id="SIEM-020",
        name="Process Value Anomaly",
        description="Detects sudden changes in process values",
        rule_type=RuleType.BEHAVIORAL,
        severity=RuleSeverity.HIGH,
        mitre_technique="T0836",
        conditions={
            "event_type": "process_value_change",
            "deviation": ">3_sigma",
        },
        actions=["alert", "log", "soc_notification"],
    ),
]


# =============================================================================
# RULE ENGINE
# =============================================================================

class CorrelationEngine:
    """SIEM Correlation Engine"""
    
    def __init__(self):
        self.rules = {r.id: r for r in CORRELATION_RULES}
        self.event_buffer: List[dict] = []
        self.triggered_rules: Dict[str, datetime] = {}
        
    def add_event(self, event: dict):
        """Add event to correlation buffer"""
        event['timestamp'] = datetime.now()
        self.event_buffer.append(event)
        
        # Prune old events
        cutoff = datetime.now() - timedelta(seconds=600)
        self.event_buffer = [e for e in self.event_buffer if e['timestamp'] > cutoff]
        
    def evaluate_rules(self) -> List[dict]:
        """Evaluate all rules against current events"""
        alerts = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
                
            # Check suppression
            if rule.id in self.triggered_rules:
                if datetime.now() - self.triggered_rules[rule.id] < timedelta(seconds=rule.suppression_seconds):
                    continue
            
            if rule.rule_type == RuleType.SINGLE:
                alert = self._evaluate_single(rule)
            elif rule.rule_type == RuleType.AGGREGATION:
                alert = self._evaluate_aggregation(rule)
            elif rule.rule_type == RuleType.SEQUENCE:
                alert = self._evaluate_sequence(rule)
            elif rule.rule_type == RuleType.BEHAVIORAL:
                alert = self._evaluate_behavioral(rule)
            else:
                continue
                
            if alert:
                self.triggered_rules[rule.id] = datetime.now()
                alerts.append(alert)
                
        return alerts
        
    def _evaluate_single(self, rule: CorrelationRule) -> Optional[dict]:
        """Evaluate single-event rule"""
        for event in reversed(self.event_buffer):
            if self._matches_conditions(event, rule.conditions):
                return self._create_alert(rule, [event])
        return None
        
    def _evaluate_aggregation(self, rule: CorrelationRule) -> Optional[dict]:
        """Evaluate aggregation rule"""
        cutoff = datetime.now() - timedelta(seconds=rule.time_window_seconds)
        matching_events = [
            e for e in self.event_buffer 
            if e['timestamp'] > cutoff and self._matches_conditions(e, rule.conditions)
        ]
        
        if len(matching_events) >= rule.threshold:
            return self._create_alert(rule, matching_events)
        return None
        
    def _evaluate_sequence(self, rule: CorrelationRule) -> Optional[dict]:
        """Evaluate sequence rule"""
        # Simplified sequence matching
        cutoff = datetime.now() - timedelta(seconds=rule.time_window_seconds)
        recent_events = [e for e in self.event_buffer if e['timestamp'] > cutoff]
        
        sequence_matched = []
        for seq_step in rule.sequence:
            for event in recent_events:
                if event.get('event') == seq_step['event']:
                    sequence_matched.append(event)
                    break
                    
        if len(sequence_matched) == len(rule.sequence):
            return self._create_alert(rule, sequence_matched)
        return None
        
    def _evaluate_behavioral(self, rule: CorrelationRule) -> Optional[dict]:
        """Evaluate behavioral rule"""
        # Placeholder for behavioral analysis
        return None
        
    def _matches_conditions(self, event: dict, conditions: dict) -> bool:
        """Check if event matches rule conditions"""
        for key, expected in conditions.items():
            actual = event.get(key)
            
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif isinstance(expected, str):
                if expected.startswith('!'):
                    if actual == expected[1:]:
                        return False
                elif actual != expected:
                    return False
                    
        return True
        
    def _create_alert(self, rule: CorrelationRule, events: List[dict]) -> dict:
        """Create alert from rule match"""
        return {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "severity": rule.severity.name,
            "mitre_technique": rule.mitre_technique,
            "description": rule.description,
            "timestamp": datetime.now().isoformat(),
            "event_count": len(events),
            "actions": rule.actions,
            "events": [
                {k: str(v) for k, v in e.items() if k != 'timestamp'}
                for e in events[:5]  # Limit to first 5
            ],
        }
        
    def get_rules_summary(self) -> List[dict]:
        """Get summary of all rules"""
        return [
            {
                "id": r.id,
                "name": r.name,
                "type": r.rule_type.value,
                "severity": r.severity.name,
                "enabled": r.enabled,
                "mitre": r.mitre_technique,
            }
            for r in self.rules.values()
        ]
        
    def export_rules(self) -> str:
        """Export rules as JSON"""
        return json.dumps([asdict(r) for r in self.rules.values()], indent=2, default=str)


if __name__ == "__main__":
    engine = CorrelationEngine()
    
    # Simulate events
    engine.add_event({
        "event": "modbus_read_holding",
        "source": "10.0.1.100",
        "destination": "10.0.1.10",
        "protocol": "modbus",
    })
    
    for i in range(5):
        engine.add_event({
            "event": "modbus_read_holding",
            "source": "10.0.1.100",
            "destination": "10.0.1.10",
            "protocol": "modbus",
        })
        
    engine.add_event({
        "event": "modbus_write_register",
        "source": "10.0.1.100",
        "destination": "10.0.1.10",
        "protocol": "modbus",
    })
    
    # Evaluate rules
    alerts = engine.evaluate_rules()
    for alert in alerts:
        print(f"ALERT: {alert['rule_name']} ({alert['severity']})")

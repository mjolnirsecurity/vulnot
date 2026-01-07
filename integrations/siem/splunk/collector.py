#!/usr/bin/env python3
"""
VULNOT Splunk Log Collector
Collects OT security logs and forwards to Splunk HEC (HTTP Event Collector)
"""

import os
import json
import time
import asyncio
import aiohttp
import redis.asyncio as redis
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

# =============================================================================
# CONFIGURATION
# =============================================================================

SPLUNK_HEC_URL = os.getenv("SPLUNK_HEC_URL", "")
SPLUNK_HEC_TOKEN = os.getenv("SPLUNK_HEC_TOKEN", "")
SPLUNK_INDEX = os.getenv("SPLUNK_INDEX", "vulnot_ot")
SPLUNK_SOURCE = os.getenv("SPLUNK_SOURCE", "vulnot-collector")
SPLUNK_SOURCETYPE = os.getenv("SPLUNK_SOURCETYPE", "vulnot:ot:security")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
FLUSH_INTERVAL = int(os.getenv("FLUSH_INTERVAL", "5"))

# SSL verification (disable for self-signed certs in lab)
SPLUNK_VERIFY_SSL = os.getenv("SPLUNK_VERIFY_SSL", "false").lower() == "true"

# =============================================================================
# LOG MODELS
# =============================================================================

class LogSeverity(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ALERT = "ALERT"

class LogCategory(Enum):
    NETWORK = "network"
    PROTOCOL = "protocol"
    PROCESS = "process"
    SECURITY = "security"
    SYSTEM = "system"

@dataclass
class OTSecurityLog:
    """Standardized OT Security Log Format"""
    timestamp: str
    source_ip: str
    dest_ip: str
    protocol: str
    action: str
    severity: str
    category: str
    message: str

    # Optional fields
    source_port: Optional[int] = None
    dest_port: Optional[int] = None
    function_code: Optional[int] = None
    register: Optional[int] = None
    value: Optional[Any] = None
    device_name: Optional[str] = None
    user: Optional[str] = None
    raw_data: Optional[str] = None

    # MITRE ATT&CK mapping
    mitre_technique: Optional[str] = None
    mitre_tactic: Optional[str] = None

    # Alert fields
    alert_id: Optional[str] = None
    alert_name: Optional[str] = None
    alert_type: Optional[str] = None

    def to_splunk_event(self) -> Dict[str, Any]:
        """Convert to Splunk HEC event format"""
        event_data = {k: v for k, v in asdict(self).items() if v is not None}

        # Parse timestamp to epoch
        try:
            dt = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
            epoch_time = dt.timestamp()
        except:
            epoch_time = time.time()

        return {
            "time": epoch_time,
            "source": SPLUNK_SOURCE,
            "sourcetype": SPLUNK_SOURCETYPE,
            "index": SPLUNK_INDEX,
            "event": event_data
        }

# =============================================================================
# LOG PARSERS (Same as Sumo Logic)
# =============================================================================

class ModbusLogParser:
    """Parse Modbus TCP logs"""

    FUNCTION_CODES = {
        1: "Read Coils",
        2: "Read Discrete Inputs",
        3: "Read Holding Registers",
        4: "Read Input Registers",
        5: "Write Single Coil",
        6: "Write Single Register",
        15: "Write Multiple Coils",
        16: "Write Multiple Registers",
        43: "Read Device Identification"
    }

    WRITE_FUNCTIONS = [5, 6, 15, 16]

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        func_code = log_data.get("function_code", 0)
        func_name = cls.FUNCTION_CODES.get(func_code, f"Unknown ({func_code})")

        if func_code in cls.WRITE_FUNCTIONS:
            severity = LogSeverity.WARNING.value
            mitre_technique = "T0855"
            mitre_tactic = "Impair Process Control"
        else:
            severity = LogSeverity.INFO.value
            mitre_technique = "T0802"
            mitre_tactic = "Collection"

        return OTSecurityLog(
            timestamp=log_data.get("timestamp", datetime.utcnow().isoformat()),
            source_ip=log_data.get("source_ip", "unknown"),
            dest_ip=log_data.get("dest_ip", "unknown"),
            source_port=log_data.get("source_port"),
            dest_port=log_data.get("dest_port", 502),
            protocol="modbus",
            action=func_name,
            function_code=func_code,
            register=log_data.get("register"),
            value=log_data.get("value"),
            severity=severity,
            category=LogCategory.PROTOCOL.value,
            message=f"Modbus {func_name} from {log_data.get('source_ip')} to {log_data.get('dest_ip')}",
            mitre_technique=mitre_technique,
            mitre_tactic=mitre_tactic,
            device_name=log_data.get("device_name")
        )

class DNP3LogParser:
    """Parse DNP3 logs"""

    FUNCTION_CODES = {
        1: "Read",
        2: "Write",
        3: "Select",
        4: "Operate",
        5: "Direct Operate",
        6: "Direct Operate No Ack",
        13: "Cold Restart",
        14: "Warm Restart"
    }

    CRITICAL_FUNCTIONS = [3, 4, 5, 6, 13, 14]

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        func_code = log_data.get("function_code", 0)
        func_name = cls.FUNCTION_CODES.get(func_code, f"Unknown ({func_code})")

        if func_code in cls.CRITICAL_FUNCTIONS:
            severity = LogSeverity.ALERT.value
            mitre_technique = "T0855"
            mitre_tactic = "Impair Process Control"
        else:
            severity = LogSeverity.INFO.value
            mitre_technique = "T0802"
            mitre_tactic = "Collection"

        return OTSecurityLog(
            timestamp=log_data.get("timestamp", datetime.utcnow().isoformat()),
            source_ip=log_data.get("source_ip", "unknown"),
            dest_ip=log_data.get("dest_ip", "unknown"),
            source_port=log_data.get("source_port"),
            dest_port=log_data.get("dest_port", 20000),
            protocol="dnp3",
            action=func_name,
            function_code=func_code,
            severity=severity,
            category=LogCategory.PROTOCOL.value,
            message=f"DNP3 {func_name} from {log_data.get('source_ip')} to {log_data.get('dest_ip')}",
            mitre_technique=mitre_technique,
            mitre_tactic=mitre_tactic,
            device_name=log_data.get("device_name")
        )

class S7CommLogParser:
    """Parse S7comm logs"""

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        action = log_data.get("action", "unknown")

        critical_actions = ["cpu_stop", "program_upload", "program_download", "memory_write"]
        if action.lower() in critical_actions:
            severity = LogSeverity.CRITICAL.value
            mitre_technique = "T0821"
            mitre_tactic = "Inhibit Response Function"
        else:
            severity = LogSeverity.INFO.value
            mitre_technique = "T0802"
            mitre_tactic = "Collection"

        return OTSecurityLog(
            timestamp=log_data.get("timestamp", datetime.utcnow().isoformat()),
            source_ip=log_data.get("source_ip", "unknown"),
            dest_ip=log_data.get("dest_ip", "unknown"),
            source_port=log_data.get("source_port"),
            dest_port=log_data.get("dest_port", 102),
            protocol="s7comm",
            action=action,
            severity=severity,
            category=LogCategory.PROTOCOL.value,
            message=f"S7comm {action} from {log_data.get('source_ip')} to {log_data.get('dest_ip')}",
            mitre_technique=mitre_technique,
            mitre_tactic=mitre_tactic,
            device_name=log_data.get("device_name")
        )

class ProcessLogParser:
    """Parse process/alarm logs"""

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        alarm_type = log_data.get("alarm_type", "info")

        severity_map = {
            "critical": LogSeverity.CRITICAL.value,
            "high": LogSeverity.ALERT.value,
            "warning": LogSeverity.WARNING.value,
            "info": LogSeverity.INFO.value
        }

        return OTSecurityLog(
            timestamp=log_data.get("timestamp", datetime.utcnow().isoformat()),
            source_ip=log_data.get("source_ip", "process"),
            dest_ip=log_data.get("dest_ip", "scada"),
            protocol="process",
            action=log_data.get("action", "alarm"),
            severity=severity_map.get(alarm_type, LogSeverity.INFO.value),
            category=LogCategory.PROCESS.value,
            message=log_data.get("message", "Process event"),
            alert_id=log_data.get("alarm_id"),
            alert_name=log_data.get("alarm_name"),
            alert_type=alarm_type,
            device_name=log_data.get("device_name"),
            value=log_data.get("value")
        )

class IDSAlertParser:
    """Parse IDS alert logs"""

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        return OTSecurityLog(
            timestamp=log_data.get("timestamp", datetime.utcnow().isoformat()),
            source_ip=log_data.get("source_ip", "unknown"),
            dest_ip=log_data.get("dest_ip", "unknown"),
            source_port=log_data.get("source_port"),
            dest_port=log_data.get("dest_port"),
            protocol=log_data.get("protocol", "unknown"),
            action="IDS_ALERT",
            severity=LogSeverity.ALERT.value,
            category=LogCategory.SECURITY.value,
            message=log_data.get("message", "IDS Alert"),
            alert_id=log_data.get("alert_id"),
            alert_name=log_data.get("rule_name"),
            alert_type=log_data.get("alert_type"),
            mitre_technique=log_data.get("mitre_technique"),
            mitre_tactic=log_data.get("mitre_tactic"),
            raw_data=log_data.get("raw_data")
        )

# =============================================================================
# SPLUNK COLLECTOR
# =============================================================================

class SplunkCollector:
    """Collects logs from Redis and forwards to Splunk HEC"""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.log_buffer: List[Dict] = []
        self.running = False

        self.parsers = {
            "modbus": ModbusLogParser,
            "dnp3": DNP3LogParser,
            "s7comm": S7CommLogParser,
            "process": ProcessLogParser,
            "ids": IDSAlertParser
        }

    async def connect(self):
        """Connect to Redis and initialize HTTP session"""
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

        # Create SSL context for self-signed certs
        ssl_context = None if SPLUNK_VERIFY_SSL else False
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        print(f"[SplunkCollector] Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")

    async def disconnect(self):
        """Cleanup connections"""
        if self.redis:
            await self.redis.close()
        if self.session:
            await self.session.close()

    async def send_to_splunk(self, events: List[Dict]) -> bool:
        """Send batch of events to Splunk HEC"""
        if not SPLUNK_HEC_URL or not SPLUNK_HEC_TOKEN:
            print("[SplunkCollector] Warning: SPLUNK_HEC_URL or SPLUNK_HEC_TOKEN not configured")
            return False

        if not events:
            return True

        try:
            # Format as newline-delimited JSON events
            payload = "\n".join(json.dumps(event) for event in events)

            headers = {
                "Authorization": f"Splunk {SPLUNK_HEC_TOKEN}",
                "Content-Type": "application/json"
            }

            async with self.session.post(
                SPLUNK_HEC_URL,
                data=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    print(f"[SplunkCollector] Sent {len(events)} events to Splunk")
                    return True
                else:
                    body = await response.text()
                    print(f"[SplunkCollector] Error: HTTP {response.status} - {body}")
                    return False

        except Exception as e:
            print(f"[SplunkCollector] Error sending to Splunk: {e}")
            return False

    async def process_log(self, channel: str, data: str) -> Optional[Dict]:
        """Parse and process a log entry"""
        try:
            log_data = json.loads(data)

            # Determine log type from channel
            if "modbus" in channel:
                parser = self.parsers["modbus"]
            elif "dnp3" in channel:
                parser = self.parsers["dnp3"]
            elif "s7comm" in channel or "s7" in channel:
                parser = self.parsers["s7comm"]
            elif "process" in channel or "alarm" in channel:
                parser = self.parsers["process"]
            elif "ids" in channel or "alert" in channel:
                parser = self.parsers["ids"]
            else:
                # Generic log - wrap in Splunk event format
                return {
                    "time": time.time(),
                    "source": SPLUNK_SOURCE,
                    "sourcetype": SPLUNK_SOURCETYPE,
                    "index": SPLUNK_INDEX,
                    "event": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "channel": channel,
                        "data": log_data
                    }
                }

            parsed_log = parser.parse(log_data)
            return parsed_log.to_splunk_event()

        except json.JSONDecodeError:
            print(f"[SplunkCollector] Invalid JSON: {data[:100]}")
            return None
        except Exception as e:
            print(f"[SplunkCollector] Error processing log: {e}")
            return None

    async def flush_buffer(self):
        """Flush log buffer to Splunk"""
        if self.log_buffer:
            events_to_send = self.log_buffer.copy()
            self.log_buffer.clear()
            await self.send_to_splunk(events_to_send)

    async def subscribe_to_channels(self):
        """Subscribe to Redis pub/sub channels for logs"""
        pubsub = self.redis.pubsub()

        channels = [
            "vulnot:logs:modbus",
            "vulnot:logs:dnp3",
            "vulnot:logs:s7comm",
            "vulnot:logs:opcua",
            "vulnot:logs:process",
            "vulnot:logs:ids",
            "vulnot:logs:*"
        ]

        await pubsub.psubscribe(*channels)
        print(f"[SplunkCollector] Subscribed to channels: {channels}")

        return pubsub

    async def run(self):
        """Main collector loop"""
        await self.connect()

        if not SPLUNK_HEC_URL or not SPLUNK_HEC_TOKEN:
            print("[SplunkCollector] WARNING: Splunk HEC not configured!")
            print("[SplunkCollector] Set SPLUNK_HEC_URL and SPLUNK_HEC_TOKEN")

        pubsub = await self.subscribe_to_channels()
        self.running = True

        last_flush = time.time()

        print("[SplunkCollector] Starting log collection...")

        try:
            async for message in pubsub.listen():
                if message["type"] in ["pmessage", "message"]:
                    channel = message.get("channel", message.get("pattern", "unknown"))
                    data = message.get("data", "{}")

                    parsed = await self.process_log(channel, data)
                    if parsed:
                        self.log_buffer.append(parsed)

                        # Print to console for debugging
                        event = parsed.get("event", {})
                        print(f"[LOG] {event.get('protocol', 'unknown')} | {event.get('severity', 'INFO')} | {event.get('message', '')[:80]}")

                # Flush buffer if conditions met
                if len(self.log_buffer) >= BATCH_SIZE or (time.time() - last_flush) >= FLUSH_INTERVAL:
                    await self.flush_buffer()
                    last_flush = time.time()

        except asyncio.CancelledError:
            print("[SplunkCollector] Shutting down...")
            await self.flush_buffer()
        finally:
            await self.disconnect()

# =============================================================================
# MAIN
# =============================================================================

async def main():
    print("=" * 60)
    print("VULNOT Splunk Log Collector")
    print("=" * 60)
    print(f"Splunk HEC URL: {'Configured' if SPLUNK_HEC_URL else 'NOT CONFIGURED'}")
    print(f"Splunk HEC Token: {'Configured' if SPLUNK_HEC_TOKEN else 'NOT CONFIGURED'}")
    print(f"Index: {SPLUNK_INDEX}")
    print(f"Sourcetype: {SPLUNK_SOURCETYPE}")
    print(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Flush Interval: {FLUSH_INTERVAL}s")
    print("=" * 60)

    collector = SplunkCollector()
    await collector.run()

if __name__ == "__main__":
    asyncio.run(main())

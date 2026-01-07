#!/usr/bin/env python3
"""
VULNOT Elasticsearch Log Collector
Collects OT security logs and forwards to Elasticsearch (ELK Stack)
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

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "vulnot-ot-logs")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER", "")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD", "")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY", "")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
FLUSH_INTERVAL = int(os.getenv("FLUSH_INTERVAL", "5"))

# Use data streams (Elasticsearch 7.9+)
USE_DATA_STREAMS = os.getenv("USE_DATA_STREAMS", "false").lower() == "true"

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

    source_port: Optional[int] = None
    dest_port: Optional[int] = None
    function_code: Optional[int] = None
    register: Optional[int] = None
    value: Optional[Any] = None
    device_name: Optional[str] = None
    user: Optional[str] = None
    raw_data: Optional[str] = None

    mitre_technique: Optional[str] = None
    mitre_tactic: Optional[str] = None

    alert_id: Optional[str] = None
    alert_name: Optional[str] = None
    alert_type: Optional[str] = None

    def to_elasticsearch(self) -> Dict[str, Any]:
        """Convert to Elasticsearch document format (ECS compatible)"""
        doc = {k: v for k, v in asdict(self).items() if v is not None}

        # Map to ECS fields
        doc["@timestamp"] = self.timestamp
        doc["event"] = {
            "category": self.category,
            "action": self.action,
            "severity": self._severity_to_number(),
            "severity_name": self.severity
        }
        doc["source"] = {
            "ip": self.source_ip,
            "port": self.source_port
        }
        doc["destination"] = {
            "ip": self.dest_ip,
            "port": self.dest_port
        }
        doc["network"] = {
            "protocol": self.protocol
        }

        # MITRE ATT&CK mapping
        if self.mitre_technique:
            doc["threat"] = {
                "technique": {
                    "id": self.mitre_technique
                },
                "tactic": {
                    "name": self.mitre_tactic
                },
                "framework": "MITRE ATT&CK for ICS"
            }

        # OT-specific fields
        doc["ot"] = {
            "protocol": self.protocol,
            "function_code": self.function_code,
            "register": self.register,
            "value": self.value,
            "device_name": self.device_name
        }

        return doc

    def _severity_to_number(self) -> int:
        severity_map = {
            "DEBUG": 1,
            "INFO": 2,
            "WARNING": 3,
            "ERROR": 4,
            "CRITICAL": 5,
            "ALERT": 6
        }
        return severity_map.get(self.severity, 2)

# =============================================================================
# LOG PARSERS
# =============================================================================

class ModbusLogParser:
    FUNCTION_CODES = {
        1: "Read Coils", 2: "Read Discrete Inputs",
        3: "Read Holding Registers", 4: "Read Input Registers",
        5: "Write Single Coil", 6: "Write Single Register",
        15: "Write Multiple Coils", 16: "Write Multiple Registers",
        43: "Read Device Identification"
    }
    WRITE_FUNCTIONS = [5, 6, 15, 16]

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        func_code = log_data.get("function_code", 0)
        func_name = cls.FUNCTION_CODES.get(func_code, f"Unknown ({func_code})")

        if func_code in cls.WRITE_FUNCTIONS:
            severity = LogSeverity.WARNING.value
            mitre_technique, mitre_tactic = "T0855", "Impair Process Control"
        else:
            severity = LogSeverity.INFO.value
            mitre_technique, mitre_tactic = "T0802", "Collection"

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
    FUNCTION_CODES = {
        1: "Read", 2: "Write", 3: "Select", 4: "Operate",
        5: "Direct Operate", 6: "Direct Operate No Ack",
        13: "Cold Restart", 14: "Warm Restart"
    }
    CRITICAL_FUNCTIONS = [3, 4, 5, 6, 13, 14]

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        func_code = log_data.get("function_code", 0)
        func_name = cls.FUNCTION_CODES.get(func_code, f"Unknown ({func_code})")

        if func_code in cls.CRITICAL_FUNCTIONS:
            severity = LogSeverity.ALERT.value
            mitre_technique, mitre_tactic = "T0855", "Impair Process Control"
        else:
            severity = LogSeverity.INFO.value
            mitre_technique, mitre_tactic = "T0802", "Collection"

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
    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        action = log_data.get("action", "unknown")
        critical_actions = ["cpu_stop", "program_upload", "program_download", "memory_write"]

        if action.lower() in critical_actions:
            severity = LogSeverity.CRITICAL.value
            mitre_technique, mitre_tactic = "T0821", "Inhibit Response Function"
        else:
            severity = LogSeverity.INFO.value
            mitre_technique, mitre_tactic = "T0802", "Collection"

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
# ELASTICSEARCH COLLECTOR
# =============================================================================

class ElasticsearchCollector:
    """Collects logs from Redis and forwards to Elasticsearch"""

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

        # Configure auth
        auth = None
        headers = {}
        if ELASTICSEARCH_API_KEY:
            headers["Authorization"] = f"ApiKey {ELASTICSEARCH_API_KEY}"
        elif ELASTICSEARCH_USER and ELASTICSEARCH_PASSWORD:
            auth = aiohttp.BasicAuth(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD)

        self.session = aiohttp.ClientSession(auth=auth, headers=headers)
        print(f"[ESCollector] Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")

        # Create index template
        await self._create_index_template()

    async def _create_index_template(self):
        """Create index template for OT logs"""
        template = {
            "index_patterns": [f"{ELASTICSEARCH_INDEX}-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "protocol": {"type": "keyword"},
                        "source_ip": {"type": "ip"},
                        "dest_ip": {"type": "ip"},
                        "source_port": {"type": "integer"},
                        "dest_port": {"type": "integer"},
                        "action": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "message": {"type": "text"},
                        "function_code": {"type": "integer"},
                        "register": {"type": "integer"},
                        "device_name": {"type": "keyword"},
                        "mitre_technique": {"type": "keyword"},
                        "mitre_tactic": {"type": "keyword"},
                        "alert_id": {"type": "keyword"},
                        "alert_name": {"type": "keyword"}
                    }
                }
            }
        }

        try:
            async with self.session.put(
                f"{ELASTICSEARCH_URL}/_index_template/vulnot-ot-logs",
                json=template
            ) as response:
                if response.status in [200, 201]:
                    print("[ESCollector] Index template created/updated")
                else:
                    body = await response.text()
                    print(f"[ESCollector] Template warning: {body[:200]}")
        except Exception as e:
            print(f"[ESCollector] Template error (non-fatal): {e}")

    async def disconnect(self):
        """Cleanup connections"""
        if self.redis:
            await self.redis.close()
        if self.session:
            await self.session.close()

    async def send_to_elasticsearch(self, docs: List[Dict]) -> bool:
        """Send batch of documents using bulk API"""
        if not docs:
            return True

        try:
            # Build bulk request body
            bulk_body = ""
            index_name = f"{ELASTICSEARCH_INDEX}-{datetime.utcnow().strftime('%Y.%m.%d')}"

            for doc in docs:
                # Index action
                bulk_body += json.dumps({"index": {"_index": index_name}}) + "\n"
                bulk_body += json.dumps(doc) + "\n"

            async with self.session.post(
                f"{ELASTICSEARCH_URL}/_bulk",
                data=bulk_body,
                headers={"Content-Type": "application/x-ndjson"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("errors"):
                        print(f"[ESCollector] Bulk errors: {result['items'][0]}")
                    else:
                        print(f"[ESCollector] Indexed {len(docs)} documents")
                    return True
                else:
                    body = await response.text()
                    print(f"[ESCollector] Error: HTTP {response.status} - {body[:200]}")
                    return False

        except Exception as e:
            print(f"[ESCollector] Error sending to Elasticsearch: {e}")
            return False

    async def process_log(self, channel: str, data: str) -> Optional[Dict]:
        """Parse and process a log entry"""
        try:
            log_data = json.loads(data)

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
                return {
                    "@timestamp": datetime.utcnow().isoformat(),
                    "channel": channel,
                    "data": log_data,
                    "protocol": "unknown"
                }

            parsed_log = parser.parse(log_data)
            return parsed_log.to_elasticsearch()

        except json.JSONDecodeError:
            print(f"[ESCollector] Invalid JSON: {data[:100]}")
            return None
        except Exception as e:
            print(f"[ESCollector] Error processing log: {e}")
            return None

    async def flush_buffer(self):
        """Flush log buffer to Elasticsearch"""
        if self.log_buffer:
            docs_to_send = self.log_buffer.copy()
            self.log_buffer.clear()
            await self.send_to_elasticsearch(docs_to_send)

    async def subscribe_to_channels(self):
        """Subscribe to Redis pub/sub channels"""
        pubsub = self.redis.pubsub()
        channels = [
            "vulnot:logs:modbus", "vulnot:logs:dnp3", "vulnot:logs:s7comm",
            "vulnot:logs:opcua", "vulnot:logs:process", "vulnot:logs:ids",
            "vulnot:logs:*"
        ]
        await pubsub.psubscribe(*channels)
        print(f"[ESCollector] Subscribed to channels")
        return pubsub

    async def run(self):
        """Main collector loop"""
        await self.connect()
        pubsub = await self.subscribe_to_channels()
        self.running = True
        last_flush = time.time()

        print("[ESCollector] Starting log collection...")

        try:
            async for message in pubsub.listen():
                if message["type"] in ["pmessage", "message"]:
                    channel = message.get("channel", message.get("pattern", "unknown"))
                    data = message.get("data", "{}")

                    parsed = await self.process_log(channel, data)
                    if parsed:
                        self.log_buffer.append(parsed)
                        print(f"[LOG] {parsed.get('protocol', 'unknown')} | {parsed.get('severity', 'INFO')} | {parsed.get('message', '')[:80]}")

                if len(self.log_buffer) >= BATCH_SIZE or (time.time() - last_flush) >= FLUSH_INTERVAL:
                    await self.flush_buffer()
                    last_flush = time.time()

        except asyncio.CancelledError:
            print("[ESCollector] Shutting down...")
            await self.flush_buffer()
        finally:
            await self.disconnect()

# =============================================================================
# MAIN
# =============================================================================

async def main():
    print("=" * 60)
    print("VULNOT Elasticsearch Log Collector")
    print("=" * 60)
    print(f"Elasticsearch URL: {ELASTICSEARCH_URL}")
    print(f"Index Pattern: {ELASTICSEARCH_INDEX}-*")
    print(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Flush Interval: {FLUSH_INTERVAL}s")
    print("=" * 60)

    collector = ElasticsearchCollector()
    await collector.run()

if __name__ == "__main__":
    asyncio.run(main())

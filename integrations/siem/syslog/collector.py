#!/usr/bin/env python3
"""
VULNOT Syslog/CEF Log Collector
Forwards OT security logs via Syslog (RFC 5424, RFC 3164) and CEF formats
over UDP, TCP, or TLS transport.
"""

import os
import json
import ssl
import time
import socket
import asyncio
import redis.asyncio as redis
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

# =============================================================================
# CONFIGURATION
# =============================================================================

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

SYSLOG_HOST = os.getenv("SYSLOG_HOST", "localhost")
SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", "514"))
SYSLOG_TRANSPORT = os.getenv("SYSLOG_TRANSPORT", "udp").lower()  # udp, tcp, tls
SYSLOG_FORMAT = os.getenv("SYSLOG_FORMAT", "rfc5424").lower()  # rfc5424, rfc3164, cef

# TLS settings (for SYSLOG_TRANSPORT=tls)
TLS_CA_CERT = os.getenv("TLS_CA_CERT", "")
TLS_CLIENT_CERT = os.getenv("TLS_CLIENT_CERT", "")
TLS_CLIENT_KEY = os.getenv("TLS_CLIENT_KEY", "")
TLS_VERIFY = os.getenv("TLS_VERIFY", "true").lower() == "true"

# Syslog options
SYSLOG_FACILITY = int(os.getenv("SYSLOG_FACILITY", "16"))  # local0 = 16
SYSLOG_HOSTNAME = os.getenv("SYSLOG_HOSTNAME", socket.gethostname())
SYSLOG_APP_NAME = os.getenv("SYSLOG_APP_NAME", "vulnot")

# Batching
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
FLUSH_INTERVAL = int(os.getenv("FLUSH_INTERVAL", "5"))

# CEF settings
CEF_VENDOR = os.getenv("CEF_VENDOR", "MjolnirSecurity")
CEF_PRODUCT = os.getenv("CEF_PRODUCT", "VULNOT")
CEF_VERSION = os.getenv("CEF_VERSION", "1.0")

# =============================================================================
# LOG MODELS (shared with other collectors)
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


# Syslog severity mapping (RFC 5424 Section 6.2.1)
SYSLOG_SEVERITY_MAP = {
    "DEBUG": 7,
    "INFO": 6,
    "WARNING": 4,
    "ERROR": 3,
    "CRITICAL": 2,
    "ALERT": 1,
}

# CEF severity mapping (0-10 scale)
CEF_SEVERITY_MAP = {
    "DEBUG": 1,
    "INFO": 3,
    "WARNING": 5,
    "ERROR": 7,
    "CRITICAL": 9,
    "ALERT": 10,
}


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


# =============================================================================
# LOG PARSERS
# =============================================================================


class ModbusLogParser:
    """Parse Modbus TCP logs"""

    FUNCTION_CODES = {
        1: "Read Coils", 2: "Read Discrete Inputs",
        3: "Read Holding Registers", 4: "Read Input Registers",
        5: "Write Single Coil", 6: "Write Single Register",
        15: "Write Multiple Coils", 16: "Write Multiple Registers",
        43: "Read Device Identification",
    }
    WRITE_FUNCTIONS = [5, 6, 15, 16]

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        func_code = log_data.get("function_code", 0)
        func_name = cls.FUNCTION_CODES.get(func_code, f"Unknown ({func_code})")
        is_write = func_code in cls.WRITE_FUNCTIONS
        return OTSecurityLog(
            timestamp=log_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            source_ip=log_data.get("source_ip", "unknown"),
            dest_ip=log_data.get("dest_ip", "unknown"),
            source_port=log_data.get("source_port"),
            dest_port=log_data.get("dest_port", 502),
            protocol="modbus",
            action=func_name,
            function_code=func_code,
            register=log_data.get("register"),
            value=log_data.get("value"),
            severity=LogSeverity.WARNING.value if is_write else LogSeverity.INFO.value,
            category=LogCategory.PROTOCOL.value,
            message=f"Modbus {func_name} from {log_data.get('source_ip')} to {log_data.get('dest_ip')}",
            mitre_technique="T0855" if is_write else "T0802",
            mitre_tactic="Impair Process Control" if is_write else "Collection",
            device_name=log_data.get("device_name"),
        )


class DNP3LogParser:
    """Parse DNP3 logs"""

    FUNCTION_CODES = {
        1: "Read", 2: "Write", 3: "Select", 4: "Operate",
        5: "Direct Operate", 6: "Direct Operate No Ack",
        13: "Cold Restart", 14: "Warm Restart",
    }
    CRITICAL_FUNCTIONS = [3, 4, 5, 6, 13, 14]

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        func_code = log_data.get("function_code", 0)
        func_name = cls.FUNCTION_CODES.get(func_code, f"Unknown ({func_code})")
        is_critical = func_code in cls.CRITICAL_FUNCTIONS
        return OTSecurityLog(
            timestamp=log_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            source_ip=log_data.get("source_ip", "unknown"),
            dest_ip=log_data.get("dest_ip", "unknown"),
            source_port=log_data.get("source_port"),
            dest_port=log_data.get("dest_port", 20000),
            protocol="dnp3",
            action=func_name,
            function_code=func_code,
            severity=LogSeverity.ALERT.value if is_critical else LogSeverity.INFO.value,
            category=LogCategory.PROTOCOL.value,
            message=f"DNP3 {func_name} from {log_data.get('source_ip')} to {log_data.get('dest_ip')}",
            mitre_technique="T0855" if is_critical else "T0802",
            mitre_tactic="Impair Process Control" if is_critical else "Collection",
            device_name=log_data.get("device_name"),
        )


class S7CommLogParser:
    """Parse S7comm logs"""

    CRITICAL_ACTIONS = ["cpu_stop", "program_upload", "program_download", "memory_write"]

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        action = log_data.get("action", "unknown")
        is_critical = action.lower() in cls.CRITICAL_ACTIONS
        return OTSecurityLog(
            timestamp=log_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            source_ip=log_data.get("source_ip", "unknown"),
            dest_ip=log_data.get("dest_ip", "unknown"),
            source_port=log_data.get("source_port"),
            dest_port=log_data.get("dest_port", 102),
            protocol="s7comm",
            action=action,
            severity=LogSeverity.CRITICAL.value if is_critical else LogSeverity.INFO.value,
            category=LogCategory.PROTOCOL.value,
            message=f"S7comm {action} from {log_data.get('source_ip')} to {log_data.get('dest_ip')}",
            mitre_technique="T0821" if is_critical else "T0802",
            mitre_tactic="Inhibit Response Function" if is_critical else "Collection",
            device_name=log_data.get("device_name"),
        )


class ProcessLogParser:
    """Parse process/alarm logs"""

    SEVERITY_MAP = {
        "critical": LogSeverity.CRITICAL.value,
        "high": LogSeverity.ALERT.value,
        "warning": LogSeverity.WARNING.value,
        "info": LogSeverity.INFO.value,
    }

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        alarm_type = log_data.get("alarm_type", "info")
        return OTSecurityLog(
            timestamp=log_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            source_ip=log_data.get("source_ip", "process"),
            dest_ip=log_data.get("dest_ip", "scada"),
            protocol="process",
            action=log_data.get("action", "alarm"),
            severity=cls.SEVERITY_MAP.get(alarm_type, LogSeverity.INFO.value),
            category=LogCategory.PROCESS.value,
            message=log_data.get("message", "Process event"),
            alert_id=log_data.get("alarm_id"),
            alert_name=log_data.get("alarm_name"),
            alert_type=alarm_type,
            device_name=log_data.get("device_name"),
            value=log_data.get("value"),
        )


class IDSAlertParser:
    """Parse IDS alert logs"""

    @classmethod
    def parse(cls, log_data: Dict) -> OTSecurityLog:
        return OTSecurityLog(
            timestamp=log_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
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
            raw_data=log_data.get("raw_data"),
        )


# =============================================================================
# SYSLOG FORMATTERS
# =============================================================================


def _compute_priority(facility: int, severity_str: str) -> int:
    """Compute syslog PRI value: facility * 8 + severity"""
    severity = SYSLOG_SEVERITY_MAP.get(severity_str, 6)
    return facility * 8 + severity


def format_rfc5424(log: OTSecurityLog) -> str:
    """Format log as RFC 5424 syslog message"""
    pri = _compute_priority(SYSLOG_FACILITY, log.severity)
    ts = log.timestamp
    hostname = SYSLOG_HOSTNAME
    app_name = SYSLOG_APP_NAME
    proc_id = log.protocol
    msg_id = log.action.replace(" ", "_")[:32]

    # Structured data with OT-specific fields
    sd_parts = [
        f'vulnot@49152 protocol="{log.protocol}" action="{log.action}" '
        f'category="{log.category}" srcIP="{log.source_ip}" dstIP="{log.dest_ip}"'
    ]
    if log.mitre_technique:
        sd_parts[0] += f' mitreTechnique="{log.mitre_technique}"'
    if log.mitre_tactic:
        sd_parts[0] += f' mitreTactic="{log.mitre_tactic}"'
    if log.device_name:
        sd_parts[0] += f' deviceName="{log.device_name}"'
    if log.function_code is not None:
        sd_parts[0] += f' functionCode="{log.function_code}"'

    structured_data = "[" + sd_parts[0] + "]"
    return f"<{pri}>1 {ts} {hostname} {app_name} {proc_id} {msg_id} {structured_data} {log.message}"


def format_rfc3164(log: OTSecurityLog) -> str:
    """Format log as RFC 3164 (BSD) syslog message"""
    pri = _compute_priority(SYSLOG_FACILITY, log.severity)
    ts = datetime.now(timezone.utc).strftime("%b %d %H:%M:%S")
    hostname = SYSLOG_HOSTNAME
    tag = f"{SYSLOG_APP_NAME}[{log.protocol}]"
    return f"<{pri}>{ts} {hostname} {tag}: {log.severity} {log.message} src={log.source_ip} dst={log.dest_ip}"


def format_cef(log: OTSecurityLog) -> str:
    """Format log as ArcSight Common Event Format (CEF)"""
    cef_severity = CEF_SEVERITY_MAP.get(log.severity, 3)
    sig_id = log.function_code if log.function_code is not None else 0
    name = log.action.replace("|", "\\|")
    message = log.message.replace("=", "\\=").replace("\\", "\\\\")

    extension_parts = [
        f"src={log.source_ip}",
        f"dst={log.dest_ip}",
        f"proto={log.protocol}",
        f"cat={log.category}",
        f"msg={message}",
    ]
    if log.source_port:
        extension_parts.append(f"spt={log.source_port}")
    if log.dest_port:
        extension_parts.append(f"dpt={log.dest_port}")
    if log.mitre_technique:
        extension_parts.append(f"cs1={log.mitre_technique}")
        extension_parts.append(f"cs1Label=MITRE_Technique")
    if log.mitre_tactic:
        extension_parts.append(f"cs2={log.mitre_tactic}")
        extension_parts.append(f"cs2Label=MITRE_Tactic")
    if log.device_name:
        extension_parts.append(f"dvchost={log.device_name}")
    extension_parts.append(f"rt={log.timestamp}")

    extension = " ".join(extension_parts)
    return f"CEF:0|{CEF_VENDOR}|{CEF_PRODUCT}|{CEF_VERSION}|{sig_id}|{name}|{cef_severity}|{extension}"


FORMATTERS = {
    "rfc5424": format_rfc5424,
    "rfc3164": format_rfc3164,
    "cef": format_cef,
}

# =============================================================================
# TRANSPORT LAYER
# =============================================================================


class SyslogTransport:
    """Manages UDP, TCP, or TLS transport to a syslog server"""

    def __init__(self):
        self._sock: Optional[socket.socket] = None
        self._ssl_ctx: Optional[ssl.SSLContext] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._reader: Optional[asyncio.StreamReader] = None

    async def connect(self):
        if SYSLOG_TRANSPORT == "udp":
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print(f"[SyslogTransport] UDP socket ready -> {SYSLOG_HOST}:{SYSLOG_PORT}")

        elif SYSLOG_TRANSPORT == "tcp":
            self._reader, self._writer = await asyncio.open_connection(
                SYSLOG_HOST, SYSLOG_PORT
            )
            print(f"[SyslogTransport] TCP connected -> {SYSLOG_HOST}:{SYSLOG_PORT}")

        elif SYSLOG_TRANSPORT == "tls":
            self._ssl_ctx = ssl.create_default_context()
            if TLS_CA_CERT:
                self._ssl_ctx.load_verify_locations(TLS_CA_CERT)
            if TLS_CLIENT_CERT and TLS_CLIENT_KEY:
                self._ssl_ctx.load_cert_chain(TLS_CLIENT_CERT, TLS_CLIENT_KEY)
            if not TLS_VERIFY:
                self._ssl_ctx.check_hostname = False
                self._ssl_ctx.verify_mode = ssl.CERT_NONE

            self._reader, self._writer = await asyncio.open_connection(
                SYSLOG_HOST, SYSLOG_PORT, ssl=self._ssl_ctx
            )
            print(f"[SyslogTransport] TLS connected -> {SYSLOG_HOST}:{SYSLOG_PORT}")

        else:
            raise ValueError(f"Unsupported transport: {SYSLOG_TRANSPORT}")

    async def send(self, message: str):
        encoded = (message + "\n").encode("utf-8")
        if SYSLOG_TRANSPORT == "udp":
            self._sock.sendto(encoded, (SYSLOG_HOST, SYSLOG_PORT))
        elif SYSLOG_TRANSPORT in ("tcp", "tls"):
            if self._writer is None:
                await self.connect()
            self._writer.write(encoded)
            await self._writer.drain()

    async def close(self):
        if self._sock:
            self._sock.close()
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()


# =============================================================================
# SYSLOG COLLECTOR
# =============================================================================


class SyslogCollector:
    """Collects logs from Redis and forwards via syslog/CEF"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.transport = SyslogTransport()
        self.log_buffer: List[str] = []
        self.formatter = FORMATTERS.get(SYSLOG_FORMAT, format_rfc5424)

        self.parsers = {
            "modbus": ModbusLogParser,
            "dnp3": DNP3LogParser,
            "s7comm": S7CommLogParser,
            "process": ProcessLogParser,
            "ids": IDSAlertParser,
        }

        self.stats = {"sent": 0, "errors": 0, "parsed": 0}

    async def connect(self):
        """Connect to Redis and syslog destination"""
        redis_kwargs = {
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "decode_responses": True,
        }
        if REDIS_PASSWORD:
            redis_kwargs["password"] = REDIS_PASSWORD

        self.redis_client = redis.Redis(**redis_kwargs)
        await self.transport.connect()
        print(f"[SyslogCollector] Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()
        await self.transport.close()

    def parse_log(self, channel: str, data: str) -> Optional[OTSecurityLog]:
        """Parse raw Redis message into OTSecurityLog"""
        try:
            log_data = json.loads(data)
        except json.JSONDecodeError:
            print(f"[SyslogCollector] Invalid JSON: {data[:100]}")
            return None

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
            # Generic fallback
            return OTSecurityLog(
                timestamp=datetime.now(timezone.utc).isoformat(),
                source_ip=log_data.get("source_ip", "unknown"),
                dest_ip=log_data.get("dest_ip", "unknown"),
                protocol=log_data.get("protocol", "unknown"),
                action=log_data.get("action", "unknown"),
                severity=LogSeverity.INFO.value,
                category=LogCategory.NETWORK.value,
                message=json.dumps(log_data),
            )

        try:
            return parser.parse(log_data)
        except Exception as e:
            print(f"[SyslogCollector] Parse error: {e}")
            return None

    async def flush_buffer(self):
        """Send all buffered messages to syslog destination"""
        if not self.log_buffer:
            return

        messages = self.log_buffer.copy()
        self.log_buffer.clear()

        for msg in messages:
            try:
                await self.transport.send(msg)
                self.stats["sent"] += 1
            except Exception as e:
                self.stats["errors"] += 1
                print(f"[SyslogCollector] Send error: {e}")
                # Attempt reconnect on next flush
                try:
                    await self.transport.connect()
                except Exception:
                    pass

    async def run(self):
        """Main collector loop"""
        await self.connect()

        pubsub = self.redis_client.pubsub()
        await pubsub.psubscribe("vulnot:logs:*")
        print("[SyslogCollector] Subscribed to vulnot:logs:*")
        print("[SyslogCollector] Starting log collection...")

        last_flush = time.time()

        try:
            async for message in pubsub.listen():
                if message["type"] in ["pmessage", "message"]:
                    channel = message.get("channel", message.get("pattern", "unknown"))
                    data = message.get("data", "{}")

                    parsed = self.parse_log(channel, data)
                    if parsed:
                        self.stats["parsed"] += 1
                        formatted = self.formatter(parsed)
                        self.log_buffer.append(formatted)

                        # Console output for debugging
                        print(f"[LOG] {parsed.protocol} | {parsed.severity} | {parsed.message[:80]}")

                # Flush on batch size or interval
                now = time.time()
                if len(self.log_buffer) >= BATCH_SIZE or (now - last_flush) >= FLUSH_INTERVAL:
                    await self.flush_buffer()
                    last_flush = now

        except asyncio.CancelledError:
            print("[SyslogCollector] Shutting down...")
            await self.flush_buffer()
        finally:
            stats = self.stats
            print(f"[SyslogCollector] Stats: parsed={stats['parsed']} sent={stats['sent']} errors={stats['errors']}")
            await self.disconnect()


# =============================================================================
# MAIN
# =============================================================================


async def main():
    print("=" * 60)
    print("VULNOT Syslog/CEF Log Collector")
    print("=" * 60)
    print(f"Format:    {SYSLOG_FORMAT.upper()}")
    print(f"Transport: {SYSLOG_TRANSPORT.upper()} -> {SYSLOG_HOST}:{SYSLOG_PORT}")
    print(f"Facility:  {SYSLOG_FACILITY} (local{SYSLOG_FACILITY - 16})" if SYSLOG_FACILITY >= 16 else f"Facility: {SYSLOG_FACILITY}")
    print(f"Hostname:  {SYSLOG_HOSTNAME}")
    print(f"App Name:  {SYSLOG_APP_NAME}")
    print(f"Redis:     {REDIS_HOST}:{REDIS_PORT}")
    print(f"Batch:     {BATCH_SIZE} / {FLUSH_INTERVAL}s")
    print("=" * 60)

    collector = SyslogCollector()
    await collector.run()


if __name__ == "__main__":
    asyncio.run(main())

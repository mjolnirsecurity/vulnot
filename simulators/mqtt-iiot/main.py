"""
VULNOT MQTT/IIoT Smart Factory Simulator
Simulates an IIoT environment with smart sensors, edge gateways, and cloud connectivity

Architecture:
- Smart sensors publishing to MQTT broker
- Edge gateway aggregating data
- Cloud connector for remote monitoring
- OPC UA to MQTT bridge
"""

import asyncio
import json
import os
import time
import random
import struct
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

import redis.asyncio as redis

# MQTT imports
try:
    from asyncio_mqtt import Client as MQTTClient
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False
    print("[MQTT] asyncio_mqtt not available, using simplified implementation")


# =============================================================================
# SENSOR CONFIGURATION
# =============================================================================

class SensorType(Enum):
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    VIBRATION = "vibration"
    FLOW = "flow"
    LEVEL = "level"
    POWER = "power"
    HUMIDITY = "humidity"
    CO2 = "co2"


@dataclass
class SmartSensor:
    """IIoT Smart Sensor"""
    id: str
    name: str
    sensor_type: SensorType
    location: str
    unit: str
    
    # Current values
    value: float = 0.0
    battery: float = 100.0
    rssi: int = -45  # WiFi signal strength
    
    # Calibration
    offset: float = 0.0
    scale: float = 1.0
    
    # Thresholds
    low_alarm: float = 0.0
    high_alarm: float = 100.0
    
    # Status
    online: bool = True
    alarm: bool = False
    last_seen: float = field(default_factory=time.time)
    
    # MQTT topic
    @property
    def topic(self) -> str:
        return f"factory/sensors/{self.location}/{self.id}"
    
    def to_mqtt_payload(self) -> dict:
        return {
            "sensor_id": self.id,
            "type": self.sensor_type.value,
            "value": round(self.value, 2),
            "unit": self.unit,
            "battery": round(self.battery, 1),
            "rssi": self.rssi,
            "alarm": self.alarm,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


@dataclass
class EdgeGateway:
    """Edge Gateway aggregating sensor data"""
    id: str
    name: str
    location: str
    
    # Connected sensors
    sensors: List[str] = field(default_factory=list)
    
    # Status
    online: bool = True
    cpu_usage: float = 25.0
    memory_usage: float = 40.0
    disk_usage: float = 30.0
    uptime: int = 0
    
    # Network
    ip_address: str = "10.0.7.10"
    mac_address: str = "00:1A:2B:3C:4D:5E"
    
    # Security (intentionally weak!)
    admin_password: str = "admin123"  # Default credential
    ssh_enabled: bool = True
    telnet_enabled: bool = True  # Legacy protocol
    
    # Firmware
    firmware_version: str = "1.2.3"
    update_available: bool = True


@dataclass
class IIoTState:
    """Complete IIoT environment state"""
    timestamp: float = field(default_factory=time.time)
    
    # Sensors
    sensors: List[SmartSensor] = field(default_factory=list)
    
    # Gateways
    gateways: List[EdgeGateway] = field(default_factory=list)
    
    # MQTT Broker
    broker_connected: bool = True
    messages_per_second: float = 50.0
    total_messages: int = 0
    
    # Cloud status
    cloud_connected: bool = True
    cloud_latency: float = 45.0  # ms
    
    # Alerts
    alerts: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        def sensor_to_dict(s):
            d = asdict(s)
            # Convert enum to string value
            if 'sensor_type' in d and hasattr(d['sensor_type'], 'value'):
                d['sensor_type'] = d['sensor_type'].value
            elif 'sensor_type' in d and isinstance(d['sensor_type'], SensorType):
                d['sensor_type'] = d['sensor_type'].value
            return d

        return {
            "timestamp": self.timestamp,
            "sensors": [sensor_to_dict(s) for s in self.sensors],
            "gateways": [asdict(g) for g in self.gateways],
            "broker_connected": self.broker_connected,
            "messages_per_second": self.messages_per_second,
            "total_messages": self.total_messages,
            "cloud_connected": self.cloud_connected,
            "cloud_latency": self.cloud_latency,
            "alerts": self.alerts,
        }


# =============================================================================
# MQTT TOPICS (Attack Surface)
# =============================================================================

MQTT_TOPICS = {
    # Sensor data (subscribe)
    "factory/sensors/#": "All sensor readings",
    "factory/sensors/+/+": "Specific sensor",
    
    # Commands (publish - VULNERABLE!)
    "factory/control/+/cmd": "Send commands to devices",
    "factory/gateway/+/config": "Gateway configuration",
    "factory/firmware/+/update": "Firmware update trigger",
    
    # System topics
    "$SYS/#": "Broker system info",
    "factory/alerts": "Alert notifications",
    
    # OPC UA bridge
    "opcua/+/read": "OPC UA read requests",
    "opcua/+/write": "OPC UA write requests",
}


# =============================================================================
# SIMULATOR
# =============================================================================

class IIoTSimulator:
    """IIoT Environment Simulator"""
    
    def __init__(self):
        self.state = IIoTState()
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self.simulation_rate = int(os.getenv("SIMULATION_RATE", "1000"))
        self._init_devices()
        
    def _init_devices(self):
        """Initialize sensors and gateways"""
        # Production line sensors
        locations = ["line1", "line2", "line3", "utility"]
        
        sensor_configs = [
            # Line 1 - Assembly
            ("TEMP-L1-01", "Motor Temperature 1", SensorType.TEMPERATURE, "line1", "°C", 45, 85),
            ("TEMP-L1-02", "Motor Temperature 2", SensorType.TEMPERATURE, "line1", "°C", 45, 85),
            ("VIB-L1-01", "Motor Vibration 1", SensorType.VIBRATION, "line1", "mm/s", 0, 10),
            ("FLOW-L1-01", "Coolant Flow", SensorType.FLOW, "line1", "L/min", 5, 50),
            ("PWR-L1-01", "Power Consumption", SensorType.POWER, "line1", "kW", 0, 100),
            
            # Line 2 - Welding
            ("TEMP-L2-01", "Weld Temperature", SensorType.TEMPERATURE, "line2", "°C", 100, 500),
            ("TEMP-L2-02", "Ambient Temperature", SensorType.TEMPERATURE, "line2", "°C", 15, 35),
            ("VIB-L2-01", "Robot Vibration", SensorType.VIBRATION, "line2", "mm/s", 0, 8),
            ("PWR-L2-01", "Welder Power", SensorType.POWER, "line2", "kW", 0, 200),
            
            # Line 3 - Painting
            ("TEMP-L3-01", "Booth Temperature", SensorType.TEMPERATURE, "line3", "°C", 20, 30),
            ("HUM-L3-01", "Booth Humidity", SensorType.HUMIDITY, "line3", "%RH", 40, 60),
            ("PRES-L3-01", "Spray Pressure", SensorType.PRESSURE, "line3", "bar", 2, 8),
            ("FLOW-L3-01", "Paint Flow", SensorType.FLOW, "line3", "mL/min", 50, 200),
            
            # Utility
            ("TEMP-UT-01", "Compressor Temp", SensorType.TEMPERATURE, "utility", "°C", 30, 80),
            ("PRES-UT-01", "Air Pressure", SensorType.PRESSURE, "utility", "bar", 6, 10),
            ("LVL-UT-01", "Tank Level", SensorType.LEVEL, "utility", "%", 10, 90),
            ("CO2-UT-01", "CO2 Level", SensorType.CO2, "utility", "ppm", 400, 1000),
        ]
        
        for config in sensor_configs:
            sensor = SmartSensor(
                id=config[0],
                name=config[1],
                sensor_type=config[2],
                location=config[3],
                unit=config[4],
                low_alarm=config[5],
                high_alarm=config[6],
                value=(config[5] + config[6]) / 2,
            )
            self.state.sensors.append(sensor)
            
        # Edge gateways
        for i, loc in enumerate(locations):
            gateway = EdgeGateway(
                id=f"GW-{loc.upper()}",
                name=f"Edge Gateway {loc.title()}",
                location=loc,
                ip_address=f"10.0.7.{10 + i}",
                sensors=[s.id for s in self.state.sensors if s.location == loc]
            )
            self.state.gateways.append(gateway)
            
    async def connect(self):
        """Connect to Redis"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        print(f"[IIoT] Connected to Redis at {redis_host}:{redis_port}")
        
    async def publish_state(self):
        """Publish state to Redis"""
        if not self.redis:
            return
            
        state_json = json.dumps(self.state.to_dict())
        await self.redis.publish("vulnot:iiot:state", state_json)
        await self.redis.set("vulnot:iiot:current", state_json)
        
        # Publish individual sensor values
        for sensor in self.state.sensors:
            await self.redis.hset(
                f"vulnot:mqtt:sensors",
                sensor.id,
                json.dumps(sensor.to_mqtt_payload())
            )
            
    async def read_commands(self):
        """Read MQTT commands from Redis"""
        if not self.redis:
            return
            
        commands = await self.redis.hgetall("vulnot:mqtt:cmd")
        if commands:
            for topic, payload in commands.items():
                await self.process_command(topic, payload)
            await self.redis.delete("vulnot:mqtt:cmd")
            
    async def process_command(self, topic: str, payload: str):
        """Process incoming MQTT command"""
        print(f"[IIoT] Command: {topic} = {payload}")
        
        try:
            data = json.loads(payload)
        except:
            data = {"value": payload}
            
        # Gateway config (vulnerable!)
        if "gateway" in topic and "config" in topic:
            gw_id = topic.split("/")[2]
            for gw in self.state.gateways:
                if gw.id == gw_id:
                    if "admin_password" in data:
                        gw.admin_password = data["admin_password"]
                        print(f"[IIoT] ⚠️ Gateway {gw_id} password changed!")
                    if "ssh_enabled" in data:
                        gw.ssh_enabled = data["ssh_enabled"]
                    if "telnet_enabled" in data:
                        gw.telnet_enabled = data["telnet_enabled"]
                        
        # Sensor calibration (vulnerable!)
        if "control" in topic and "cmd" in topic:
            sensor_id = topic.split("/")[2]
            for sensor in self.state.sensors:
                if sensor.id == sensor_id:
                    if "offset" in data:
                        sensor.offset = float(data["offset"])
                        print(f"[IIoT] ⚠️ Sensor {sensor_id} offset changed to {sensor.offset}")
                    if "scale" in data:
                        sensor.scale = float(data["scale"])
                        print(f"[IIoT] ⚠️ Sensor {sensor_id} scale changed to {sensor.scale}")
                    if "high_alarm" in data:
                        sensor.high_alarm = float(data["high_alarm"])
                        print(f"[IIoT] ⚠️ Sensor {sensor_id} alarm threshold changed!")
                        
        # Firmware update (vulnerable!)
        if "firmware" in topic and "update" in topic:
            gw_id = topic.split("/")[2]
            url = data.get("url", "")
            print(f"[IIoT] ⚠️ Gateway {gw_id} firmware update from {url}!")
            # In real attack, this could load malicious firmware
            
    def simulate_step(self, dt: float):
        """Simulate one time step"""
        noise = lambda base, pct=2: base * (1 + random.uniform(-pct/100, pct/100))
        
        for sensor in self.state.sensors:
            if not sensor.online:
                continue
                
            # Base simulation by type
            if sensor.sensor_type == SensorType.TEMPERATURE:
                # Slow drift with daily cycle
                hour = (time.time() / 3600) % 24
                base = (sensor.low_alarm + sensor.high_alarm) / 2
                variation = (sensor.high_alarm - sensor.low_alarm) * 0.2
                sensor.value = base + variation * (0.5 + 0.5 * (hour / 24))
                
            elif sensor.sensor_type == SensorType.VIBRATION:
                # Random vibration with occasional spikes
                base = (sensor.low_alarm + sensor.high_alarm) / 3
                if random.random() < 0.02:  # 2% chance of spike
                    sensor.value = base * random.uniform(2, 3)
                else:
                    sensor.value = noise(base, 10)
                    
            elif sensor.sensor_type == SensorType.PRESSURE:
                base = (sensor.low_alarm + sensor.high_alarm) / 2
                sensor.value = noise(base, 3)
                
            elif sensor.sensor_type == SensorType.FLOW:
                base = (sensor.low_alarm + sensor.high_alarm) / 2
                sensor.value = noise(base, 5)
                
            elif sensor.sensor_type == SensorType.LEVEL:
                # Slow fill/drain cycle
                cycle = (time.time() / 600) % 1  # 10 minute cycle
                sensor.value = sensor.low_alarm + (sensor.high_alarm - sensor.low_alarm) * cycle
                
            elif sensor.sensor_type == SensorType.POWER:
                base = sensor.high_alarm * 0.6
                sensor.value = noise(base, 8)
                
            elif sensor.sensor_type == SensorType.HUMIDITY:
                base = (sensor.low_alarm + sensor.high_alarm) / 2
                sensor.value = noise(base, 3)
                
            elif sensor.sensor_type == SensorType.CO2:
                base = (sensor.low_alarm + sensor.high_alarm) / 2
                sensor.value = noise(base, 5)
                
            # Apply calibration (can be manipulated!)
            sensor.value = sensor.value * sensor.scale + sensor.offset
            
            # Check alarms
            sensor.alarm = sensor.value < sensor.low_alarm or sensor.value > sensor.high_alarm
            
            # Battery drain
            sensor.battery = max(0, sensor.battery - 0.0001)
            
            # Signal variation
            sensor.rssi = int(noise(-50, 10))
            
            sensor.last_seen = time.time()
            
        # Gateway simulation
        for gw in self.state.gateways:
            gw.cpu_usage = noise(30, 20)
            gw.memory_usage = noise(45, 10)
            gw.uptime += 1
            
        # Message counter
        self.state.total_messages += len(self.state.sensors)
        self.state.messages_per_second = len(self.state.sensors)
        
        # Cloud latency
        self.state.cloud_latency = noise(50, 30)
        
        # Generate alerts
        self.state.alerts = []
        for sensor in self.state.sensors:
            if sensor.alarm:
                self.state.alerts.append({
                    "sensor_id": sensor.id,
                    "type": "threshold",
                    "message": f"{sensor.name} value {sensor.value:.1f} out of range",
                    "severity": "HIGH"
                })
            if sensor.battery < 20:
                self.state.alerts.append({
                    "sensor_id": sensor.id,
                    "type": "battery",
                    "message": f"{sensor.name} low battery ({sensor.battery:.0f}%)",
                    "severity": "MEDIUM"
                })
                
        self.state.timestamp = time.time()
        
    async def run(self):
        """Main simulation loop"""
        await self.connect()
        self.running = True
        
        print(f"[IIoT] Starting IIoT simulation")
        print(f"[IIoT] {len(self.state.sensors)} sensors, {len(self.state.gateways)} gateways")
        
        while self.running:
            loop_start = time.time()
            
            await self.read_commands()
            self.simulate_step(self.simulation_rate / 1000.0)
            await self.publish_state()
            
            elapsed = time.time() - loop_start
            sleep_time = max(0, (self.simulation_rate / 1000.0) - elapsed)
            await asyncio.sleep(sleep_time)


# =============================================================================
# MQTT BROKER (Simplified)
# =============================================================================

class SimpleMQTTBroker:
    """Simplified MQTT broker for training"""
    
    def __init__(self, simulator: IIoTSimulator):
        self.simulator = simulator
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.clients: Dict[str, asyncio.StreamWriter] = {}
        self.subscriptions: Dict[str, List[str]] = {}
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle MQTT client connection"""
        addr = writer.get_extra_info('peername')
        client_id = f"{addr[0]}:{addr[1]}"
        print(f"[MQTT] Client connected: {client_id}")
        print("[MQTT] ⚠️ NO AUTHENTICATION REQUIRED!")
        
        self.clients[client_id] = writer
        
        try:
            while True:
                # Read MQTT fixed header
                header = await reader.read(2)
                if len(header) < 2:
                    break
                    
                packet_type = (header[0] >> 4) & 0x0F
                remaining_length = header[1]
                
                # Read remaining data
                data = await reader.read(remaining_length) if remaining_length > 0 else b''
                
                # Handle packet types
                if packet_type == 1:  # CONNECT
                    print(f"[MQTT] CONNECT from {client_id}")
                    # Send CONNACK (always accept!)
                    writer.write(bytes([0x20, 0x02, 0x00, 0x00]))
                    await writer.drain()
                    
                elif packet_type == 3:  # PUBLISH
                    # Parse topic
                    topic_len = (data[0] << 8) | data[1]
                    topic = data[2:2+topic_len].decode()
                    payload = data[2+topic_len:]
                    print(f"[MQTT] PUBLISH: {topic} = {payload[:50]}...")
                    
                    # Store command for simulator
                    if self.simulator.redis:
                        await self.simulator.redis.hset(
                            "vulnot:mqtt:cmd",
                            topic,
                            payload.decode('utf-8', errors='ignore')
                        )
                        
                elif packet_type == 8:  # SUBSCRIBE
                    print(f"[MQTT] SUBSCRIBE from {client_id}")
                    # Parse subscription
                    msg_id = (data[0] << 8) | data[1]
                    # Send SUBACK
                    writer.write(bytes([0x90, 0x03, data[0], data[1], 0x00]))
                    await writer.drain()
                    
                elif packet_type == 12:  # PINGREQ
                    writer.write(bytes([0xD0, 0x00]))  # PINGRESP
                    await writer.drain()
                    
                elif packet_type == 14:  # DISCONNECT
                    break
                    
        except Exception as e:
            print(f"[MQTT] Error: {e}")
        finally:
            del self.clients[client_id]
            writer.close()
            await writer.wait_closed()
            print(f"[MQTT] Client disconnected: {client_id}")
            
    async def run(self):
        """Run MQTT broker"""
        server = await asyncio.start_server(
            self.handle_client, '0.0.0.0', self.port
        )
        
        print(f"[MQTT] Broker running on TCP port {self.port}")
        print("[MQTT] ⚠️ INTENTIONALLY VULNERABLE - NO AUTH, NO TLS")
        
        async with server:
            await server.serve_forever()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    simulator = IIoTSimulator()
    broker = SimpleMQTTBroker(simulator)
    
    try:
        await asyncio.gather(
            simulator.run(),
            broker.run()
        )
    except KeyboardInterrupt:
        print("\n[IIoT] Shutting down...")
        simulator.running = False


if __name__ == "__main__":
    asyncio.run(main())

"""
VULNOT OPC UA Industrial Simulator
Simulates an industrial process with OPC UA server

Process: Chemical Batch Reactor
- Reactor vessel with temperature/pressure control
- Feed pumps for raw materials
- Agitator for mixing
- Heating/cooling jacket
- Safety interlocks
"""

import asyncio
import json
import os
import time
import math
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime

import redis.asyncio as redis

# OPC UA imports
try:
    from asyncua import Server, ua
    from asyncua.common.methods import uamethod
    HAS_OPCUA = True
except ImportError:
    HAS_OPCUA = False
    print("[OPC-UA] asyncua not available, using simplified implementation")


# =============================================================================
# REACTOR CONFIGURATION
# =============================================================================

@dataclass
class ReactorState:
    """Chemical batch reactor state"""
    timestamp: float = field(default_factory=time.time)
    
    # Batch Information
    batch_id: str = "BATCH-001"
    batch_status: str = "RUNNING"  # IDLE, CHARGING, REACTING, DISCHARGING, COMPLETE
    batch_step: int = 3
    batch_progress: float = 45.0  # %
    recipe_name: str = "Product-A"
    
    # Reactor Vessel
    reactor_level: float = 65.0  # %
    reactor_temp: float = 85.0  # °C
    reactor_pressure: float = 2.5  # bar
    reactor_ph: float = 7.2
    reactor_density: float = 1.05  # g/mL
    
    # Temperature Control
    temp_setpoint: float = 85.0  # °C
    jacket_temp: float = 90.0  # °C
    jacket_flow: float = 75.0  # %
    heating_on: bool = True
    cooling_on: bool = False
    
    # Pressure Control
    pressure_setpoint: float = 2.5  # bar
    vent_valve: float = 0.0  # % open
    nitrogen_valve: float = 15.0  # % open
    
    # Feed System
    feed_a_flow: float = 25.0  # L/min
    feed_a_total: float = 150.0  # L
    feed_a_valve: float = 50.0  # %
    feed_b_flow: float = 10.0  # L/min
    feed_b_total: float = 60.0  # L
    feed_b_valve: float = 25.0  # %
    catalyst_flow: float = 0.5  # L/min
    catalyst_total: float = 3.0  # L
    
    # Agitator
    agitator_running: bool = True
    agitator_speed: float = 150.0  # RPM
    agitator_speed_setpoint: float = 150.0
    agitator_power: float = 7.5  # kW
    agitator_torque: float = 45.0  # Nm
    
    # Discharge
    discharge_valve: float = 0.0  # %
    discharge_flow: float = 0.0  # L/min
    discharge_total: float = 0.0  # L
    
    # Safety Systems
    high_temp_alarm: bool = False
    high_pressure_alarm: bool = False
    low_level_alarm: bool = False
    high_level_alarm: bool = False
    emergency_vent_open: bool = False
    reactor_interlock: bool = False
    
    # Quality
    conversion: float = 78.5  # %
    yield_percent: float = 92.0  # %
    
    # Utilities
    steam_pressure: float = 4.5  # bar
    cooling_water_temp: float = 25.0  # °C
    nitrogen_pressure: float = 6.0  # bar
    
    # Alarms
    alarms: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# OPC UA NODE STRUCTURE
# =============================================================================

OPCUA_NODES = {
    # Batch Info
    "BatchId": ("batch_id", "String", False),
    "BatchStatus": ("batch_status", "String", False),
    "BatchStep": ("batch_step", "Int32", False),
    "BatchProgress": ("batch_progress", "Float", False),
    "RecipeName": ("recipe_name", "String", False),
    
    # Reactor Measurements
    "ReactorLevel": ("reactor_level", "Float", False),
    "ReactorTemp": ("reactor_temp", "Float", False),
    "ReactorPressure": ("reactor_pressure", "Float", False),
    "ReactorPH": ("reactor_ph", "Float", False),
    
    # Temperature Control
    "TempSetpoint": ("temp_setpoint", "Float", True),
    "JacketTemp": ("jacket_temp", "Float", False),
    "JacketFlow": ("jacket_flow", "Float", True),
    "HeatingOn": ("heating_on", "Boolean", True),
    "CoolingOn": ("cooling_on", "Boolean", True),
    
    # Pressure Control
    "PressureSetpoint": ("pressure_setpoint", "Float", True),
    "VentValve": ("vent_valve", "Float", True),
    "NitrogenValve": ("nitrogen_valve", "Float", True),
    
    # Feed System
    "FeedAFlow": ("feed_a_flow", "Float", False),
    "FeedAValve": ("feed_a_valve", "Float", True),
    "FeedATotal": ("feed_a_total", "Float", False),
    "FeedBFlow": ("feed_b_flow", "Float", False),
    "FeedBValve": ("feed_b_valve", "Float", True),
    "FeedBTotal": ("feed_b_total", "Float", False),
    "CatalystFlow": ("catalyst_flow", "Float", False),
    
    # Agitator
    "AgitatorRunning": ("agitator_running", "Boolean", True),
    "AgitatorSpeed": ("agitator_speed", "Float", False),
    "AgitatorSpeedSetpoint": ("agitator_speed_setpoint", "Float", True),
    "AgitatorPower": ("agitator_power", "Float", False),
    
    # Discharge
    "DischargeValve": ("discharge_valve", "Float", True),
    "DischargeFlow": ("discharge_flow", "Float", False),
    
    # Safety
    "HighTempAlarm": ("high_temp_alarm", "Boolean", False),
    "HighPressureAlarm": ("high_pressure_alarm", "Boolean", False),
    "EmergencyVentOpen": ("emergency_vent_open", "Boolean", True),
    "ReactorInterlock": ("reactor_interlock", "Boolean", False),
}


# =============================================================================
# REACTOR SIMULATOR
# =============================================================================

class ReactorSimulator:
    """Physics-based batch reactor simulator"""
    
    def __init__(self):
        self.state = ReactorState()
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self.simulation_rate = int(os.getenv("SIMULATION_RATE", "100"))
        
    async def connect(self):
        """Connect to Redis"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        print(f"[Reactor] Connected to Redis at {redis_host}:{redis_port}")
        
    async def publish_state(self):
        """Publish state to Redis"""
        if not self.redis:
            return
            
        state_dict = self.state.to_dict()
        state_json = json.dumps(state_dict)
        
        await self.redis.publish("vulnot:reactor:state", state_json)
        await self.redis.set("vulnot:reactor:current", state_json)
        
        # Publish OPC UA node values
        opcua_values = {}
        for node_name, (attr, dtype, writable) in OPCUA_NODES.items():
            value = getattr(self.state, attr)
            if dtype == "Float":
                opcua_values[node_name] = int(value * 100)
            elif dtype == "Boolean":
                opcua_values[node_name] = 1 if value else 0
            elif dtype == "Int32":
                opcua_values[node_name] = int(value)
            else:
                opcua_values[node_name] = str(value)
                
        await self.redis.hset("vulnot:opcua:nodes", mapping=opcua_values)
        
    async def read_control_inputs(self):
        """Read control commands from Redis"""
        if not self.redis:
            return
            
        controls = await self.redis.hgetall("vulnot:opcua:cmd")
        if controls:
            for node_name, value in controls.items():
                if node_name in OPCUA_NODES:
                    attr, dtype, writable = OPCUA_NODES[node_name]
                    if writable:
                        if dtype == "Float":
                            setattr(self.state, attr, float(value) / 100)
                        elif dtype == "Boolean":
                            setattr(self.state, attr, value == "1")
                        elif dtype == "Int32":
                            setattr(self.state, attr, int(value))
                        print(f"[Reactor] {node_name}: {getattr(self.state, attr)}")
            await self.redis.delete("vulnot:opcua:cmd")
    
    def simulate_step(self, dt: float):
        """Simulate one time step"""
        noise = lambda base, pct=0.5: base * (1 + random.uniform(-pct/100, pct/100))
        
        # Temperature control
        temp_error = self.state.temp_setpoint - self.state.reactor_temp
        
        if self.state.heating_on and not self.state.cooling_on:
            # Heating mode
            self.state.jacket_temp = min(120, self.state.jacket_temp + 0.1)
            heat_transfer = (self.state.jacket_temp - self.state.reactor_temp) * 0.05 * (self.state.jacket_flow / 100)
            self.state.reactor_temp += heat_transfer * dt
        elif self.state.cooling_on and not self.state.heating_on:
            # Cooling mode
            self.state.jacket_temp = max(15, self.state.jacket_temp - 0.2)
            heat_transfer = (self.state.jacket_temp - self.state.reactor_temp) * 0.05 * (self.state.jacket_flow / 100)
            self.state.reactor_temp += heat_transfer * dt
        else:
            # Natural heat loss
            self.state.reactor_temp -= 0.01 * dt
            
        # Add reaction heat (exothermic)
        if self.state.batch_status == "REACTING":
            self.state.reactor_temp += 0.02 * dt
            
        self.state.reactor_temp = noise(self.state.reactor_temp, 0.1)
        
        # Pressure control
        # Pressure increases with temperature and decreases with vent
        temp_pressure_effect = (self.state.reactor_temp - 25) * 0.02
        self.state.reactor_pressure = 1.0 + temp_pressure_effect
        
        if self.state.nitrogen_valve > 0:
            self.state.reactor_pressure += self.state.nitrogen_valve * 0.01
        if self.state.vent_valve > 0:
            self.state.reactor_pressure -= self.state.vent_valve * 0.02
            
        self.state.reactor_pressure = max(0.1, noise(self.state.reactor_pressure, 0.5))
        
        # Level changes from feed and discharge
        if self.state.feed_a_valve > 0:
            self.state.feed_a_flow = self.state.feed_a_valve * 0.5
            self.state.feed_a_total += self.state.feed_a_flow * dt / 60
            self.state.reactor_level += self.state.feed_a_flow * dt / 60 * 0.1
        else:
            self.state.feed_a_flow = 0
            
        if self.state.feed_b_valve > 0:
            self.state.feed_b_flow = self.state.feed_b_valve * 0.4
            self.state.feed_b_total += self.state.feed_b_flow * dt / 60
            self.state.reactor_level += self.state.feed_b_flow * dt / 60 * 0.1
        else:
            self.state.feed_b_flow = 0
            
        if self.state.discharge_valve > 0:
            self.state.discharge_flow = self.state.discharge_valve * 1.0
            self.state.discharge_total += self.state.discharge_flow * dt / 60
            self.state.reactor_level -= self.state.discharge_flow * dt / 60 * 0.1
        else:
            self.state.discharge_flow = 0
            
        self.state.reactor_level = max(0, min(100, noise(self.state.reactor_level, 0.2)))
        
        # Agitator
        if self.state.agitator_running:
            self.state.agitator_speed = noise(self.state.agitator_speed_setpoint, 1)
            self.state.agitator_power = (self.state.agitator_speed / 150) * 7.5 * (1 + self.state.reactor_level / 200)
            self.state.agitator_torque = self.state.agitator_power * 60 / (2 * 3.14159 * self.state.agitator_speed / 60)
        else:
            self.state.agitator_speed = max(0, self.state.agitator_speed - 5)
            self.state.agitator_power = 0
            self.state.agitator_torque = 0
            
        # pH changes during reaction
        self.state.reactor_ph = noise(7.0 + math.sin(time.time() / 100) * 0.5, 0.5)
        
        # Batch progress
        if self.state.batch_status == "REACTING":
            self.state.batch_progress = min(100, self.state.batch_progress + 0.05 * dt)
            self.state.conversion = min(99, self.state.conversion + 0.02 * dt)
            
            if self.state.batch_progress >= 100:
                self.state.batch_status = "COMPLETE"
                
        # Safety interlocks
        self.state.high_temp_alarm = self.state.reactor_temp > 95
        self.state.high_pressure_alarm = self.state.reactor_pressure > 4.0
        self.state.low_level_alarm = self.state.reactor_level < 10
        self.state.high_level_alarm = self.state.reactor_level > 95
        
        # Emergency vent on high pressure
        if self.state.reactor_pressure > 5.0:
            self.state.emergency_vent_open = True
            self.state.reactor_interlock = True
            
        # Alarms
        self.state.alarms = []
        if self.state.high_temp_alarm:
            self.state.alarms.append({"level": "HIGH", "message": "High Reactor Temperature", "tag": "TI-101"})
        if self.state.high_pressure_alarm:
            self.state.alarms.append({"level": "HIGH", "message": "High Reactor Pressure", "tag": "PI-101"})
        if self.state.low_level_alarm:
            self.state.alarms.append({"level": "MEDIUM", "message": "Low Reactor Level", "tag": "LI-101"})
        if self.state.high_level_alarm:
            self.state.alarms.append({"level": "HIGH", "message": "High Reactor Level", "tag": "LI-101"})
        if self.state.reactor_interlock:
            self.state.alarms.append({"level": "CRITICAL", "message": "Reactor Safety Interlock Active", "tag": "SIS-001"})
            
        self.state.timestamp = time.time()
        
    async def run(self):
        """Main simulation loop"""
        await self.connect()
        self.running = True
        
        print("[Reactor] Starting batch reactor simulation")
        
        while self.running:
            loop_start = time.time()
            
            await self.read_control_inputs()
            self.simulate_step(self.simulation_rate / 1000.0)
            await self.publish_state()
            
            elapsed = time.time() - loop_start
            sleep_time = max(0, (self.simulation_rate / 1000.0) - elapsed)
            await asyncio.sleep(sleep_time)


# =============================================================================
# OPC UA SERVER
# =============================================================================

class OPCUAServer:
    """OPC UA Server for reactor data"""
    
    def __init__(self, simulator: ReactorSimulator):
        self.simulator = simulator
        self.port = int(os.getenv("OPCUA_PORT", "4840"))
        self.server: Optional[Server] = None
        self.nodes: Dict[str, any] = {}
        
    async def init_server(self):
        """Initialize OPC UA server"""
        if not HAS_OPCUA:
            print("[OPC-UA] Running without asyncua - simplified mode")
            return
            
        self.server = Server()
        await self.server.init()
        
        self.server.set_endpoint(f"opc.tcp://0.0.0.0:{self.port}/vulnot/reactor")
        self.server.set_server_name("VULNOT Batch Reactor")
        
        # Set up namespace
        uri = "http://vulnot.mjolnir-security.com/reactor"
        idx = await self.server.register_namespace(uri)
        
        # Create objects folder
        objects = self.server.nodes.objects
        reactor_obj = await objects.add_object(idx, "BatchReactor")
        
        # Add nodes
        for node_name, (attr, dtype, writable) in OPCUA_NODES.items():
            value = getattr(self.simulator.state, attr)
            
            if dtype == "Float":
                var = await reactor_obj.add_variable(idx, node_name, float(value))
            elif dtype == "Boolean":
                var = await reactor_obj.add_variable(idx, node_name, bool(value))
            elif dtype == "Int32":
                var = await reactor_obj.add_variable(idx, node_name, int(value))
            else:
                var = await reactor_obj.add_variable(idx, node_name, str(value))
                
            if writable:
                await var.set_writable()
                
            self.nodes[node_name] = var
            
        # Add methods
        await reactor_obj.add_method(
            idx, "StartBatch", self.start_batch, [], [ua.VariantType.Boolean]
        )
        await reactor_obj.add_method(
            idx, "StopBatch", self.stop_batch, [], [ua.VariantType.Boolean]
        )
        await reactor_obj.add_method(
            idx, "EmergencyStop", self.emergency_stop, [], [ua.VariantType.Boolean]
        )
        
    @uamethod
    async def start_batch(self, parent):
        """Start batch method"""
        self.simulator.state.batch_status = "CHARGING"
        return True
        
    @uamethod
    async def stop_batch(self, parent):
        """Stop batch method"""
        self.simulator.state.batch_status = "IDLE"
        return True
        
    @uamethod
    async def emergency_stop(self, parent):
        """Emergency stop method"""
        self.simulator.state.agitator_running = False
        self.simulator.state.heating_on = False
        self.simulator.state.feed_a_valve = 0
        self.simulator.state.feed_b_valve = 0
        self.simulator.state.reactor_interlock = True
        return True
        
    async def update_nodes(self):
        """Update OPC UA node values from simulator state"""
        if not self.server or not self.nodes:
            return
            
        for node_name, (attr, dtype, writable) in OPCUA_NODES.items():
            if node_name in self.nodes:
                value = getattr(self.simulator.state, attr)
                # Convert to correct type before writing
                if dtype == "Float":
                    value = float(value)
                elif dtype == "Boolean":
                    value = bool(value)
                elif dtype == "Int32":
                    value = int(value)
                else:
                    value = str(value)
                await self.nodes[node_name].write_value(value)
                
    async def run(self):
        """Run OPC UA server"""
        await self.init_server()
        
        if self.server:
            async with self.server:
                print(f"[OPC-UA] Server running on port {self.port}")
                print(f"[OPC-UA] Endpoint: opc.tcp://0.0.0.0:{self.port}/vulnot/reactor")
                print("[OPC-UA] ⚠️  INTENTIONALLY VULNERABLE - NO AUTHENTICATION")
                
                while True:
                    await self.update_nodes()
                    await asyncio.sleep(0.5)
        else:
            # Fallback TCP server for simplified mode
            await self.run_simple_server()
            
    async def run_simple_server(self):
        """Simple TCP server when asyncua not available"""
        async def handle_client(reader, writer):
            addr = writer.get_extra_info('peername')
            print(f"[OPC-UA] Client connected from {addr}")
            
            try:
                while True:
                    data = await reader.read(1024)
                    if not data:
                        break
                    # Echo state on any request
                    response = json.dumps(self.simulator.state.to_dict())
                    writer.write(response.encode())
                    await writer.drain()
            except:
                pass
            finally:
                writer.close()
                await writer.wait_closed()
                
        server = await asyncio.start_server(handle_client, '0.0.0.0', self.port)
        print(f"[OPC-UA] Simple server on port {self.port}")
        
        async with server:
            await server.serve_forever()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    simulator = ReactorSimulator()
    opcua_server = OPCUAServer(simulator)
    
    try:
        await asyncio.gather(
            simulator.run(),
            opcua_server.run()
        )
    except KeyboardInterrupt:
        print("\n[Reactor] Shutting down...")
        simulator.running = False


if __name__ == "__main__":
    asyncio.run(main())

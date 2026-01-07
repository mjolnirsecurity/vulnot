"""
VULNOT DNP3 Power Grid Substation Simulator
Simulates a power substation with DNP3 outstation capabilities

Substation Components:
- 2 Incoming Feeders (138kV)
- 2 Power Transformers (138kV/13.8kV)
- 4 Outgoing Feeders (13.8kV)
- 8 Circuit Breakers
- Protective Relays
- Voltage/Current Measurements
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

# DNP3 imports - using pydnp3 or custom implementation
try:
    from pydnp3 import opendnp3, openpal, asiopal, asiodnp3
    HAS_PYDNP3 = True
except ImportError:
    HAS_PYDNP3 = False
    print("[DNP3] pydnp3 not available, using simplified TCP implementation")


# =============================================================================
# SUBSTATION CONFIGURATION
# =============================================================================

@dataclass
class BreakerState:
    """Circuit breaker state"""
    name: str
    closed: bool = True
    tripped: bool = False
    lockout: bool = False
    local_remote: str = "REMOTE"  # LOCAL or REMOTE
    
@dataclass 
class TransformerState:
    """Power transformer state"""
    name: str
    tap_position: int = 8  # 1-16, 8 is nominal
    temperature: float = 45.0  # °C
    load_percent: float = 50.0
    cooling_stage: int = 1  # 1-4

@dataclass
class MeasurementPoint:
    """Analog measurement point"""
    name: str
    value: float
    unit: str
    high_limit: float
    low_limit: float
    deadband: float = 0.5

@dataclass
class SubstationState:
    """Complete substation state"""
    timestamp: float = field(default_factory=time.time)
    
    # System frequency
    frequency: float = 60.0
    
    # Incoming Feeder 1 (138kV)
    feeder1_voltage_a: float = 79.67  # kV (138/√3)
    feeder1_voltage_b: float = 79.67
    feeder1_voltage_c: float = 79.67
    feeder1_current_a: float = 250.0  # Amps
    feeder1_current_b: float = 248.0
    feeder1_current_c: float = 252.0
    feeder1_mw: float = 45.0  # MW
    feeder1_mvar: float = 12.0  # MVAR
    
    # Incoming Feeder 2 (138kV) 
    feeder2_voltage_a: float = 79.45
    feeder2_voltage_b: float = 79.50
    feeder2_voltage_c: float = 79.48
    feeder2_current_a: float = 245.0
    feeder2_current_b: float = 243.0
    feeder2_current_c: float = 247.0
    feeder2_mw: float = 43.0
    feeder2_mvar: float = 11.0
    
    # Bus voltages (13.8kV side)
    bus1_voltage_a: float = 7.97  # kV (13.8/√3)
    bus1_voltage_b: float = 7.97
    bus1_voltage_c: float = 7.97
    bus2_voltage_a: float = 7.96
    bus2_voltage_b: float = 7.96
    bus2_voltage_c: float = 7.96
    
    # Transformer 1
    xfmr1_tap: int = 8
    xfmr1_temp: float = 52.0
    xfmr1_load: float = 65.0
    xfmr1_mw: float = 22.0
    xfmr1_mvar: float = 6.0
    
    # Transformer 2
    xfmr2_tap: int = 8
    xfmr2_temp: float = 48.0
    xfmr2_load: float = 58.0
    xfmr2_mw: float = 20.0
    xfmr2_mvar: float = 5.5
    
    # Outgoing Feeders (13.8kV)
    out_feeder1_current: float = 320.0
    out_feeder1_mw: float = 6.5
    out_feeder2_current: float = 285.0
    out_feeder2_mw: float = 5.8
    out_feeder3_current: float = 410.0
    out_feeder3_mw: float = 8.2
    out_feeder4_current: float = 375.0
    out_feeder4_mw: float = 7.5
    
    # Circuit Breaker States (True = Closed)
    cb_52_1: bool = True   # Feeder 1 HV breaker
    cb_52_2: bool = True   # Feeder 2 HV breaker
    cb_52_3: bool = True   # Transformer 1 HV
    cb_52_4: bool = True   # Transformer 2 HV
    cb_52_5: bool = True   # Bus tie breaker
    cb_52_6: bool = True   # Outgoing Feeder 1
    cb_52_7: bool = True   # Outgoing Feeder 2
    cb_52_8: bool = True   # Outgoing Feeder 3
    cb_52_9: bool = True   # Outgoing Feeder 4
    cb_52_10: bool = True  # Transformer 1 LV
    cb_52_11: bool = True  # Transformer 2 LV
    cb_52_12: bool = False # Spare (normally open)
    
    # Disconnect Switch States
    ds_89_1: bool = True
    ds_89_2: bool = True
    ds_89_3: bool = True
    ds_89_4: bool = True
    
    # Protective Relay Status
    relay_50_51_1: bool = False  # Overcurrent relay 1 operated
    relay_50_51_2: bool = False  # Overcurrent relay 2 operated
    relay_87T_1: bool = False    # Transformer differential 1
    relay_87T_2: bool = False    # Transformer differential 2
    relay_21_1: bool = False     # Distance relay 1
    relay_21_2: bool = False     # Distance relay 2
    relay_81: bool = False       # Frequency relay
    relay_27: bool = False       # Undervoltage relay
    relay_59: bool = False       # Overvoltage relay
    
    # Alarms
    alarms: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# DNP3 POINT MAPPING
# =============================================================================

DNP3_BINARY_INPUTS = {
    # Circuit Breakers (index: attribute_name)
    0: ("cb_52_1", "CB 52-1 Feeder 1 HV"),
    1: ("cb_52_2", "CB 52-2 Feeder 2 HV"),
    2: ("cb_52_3", "CB 52-3 XFMR 1 HV"),
    3: ("cb_52_4", "CB 52-4 XFMR 2 HV"),
    4: ("cb_52_5", "CB 52-5 Bus Tie"),
    5: ("cb_52_6", "CB 52-6 Out Feeder 1"),
    6: ("cb_52_7", "CB 52-7 Out Feeder 2"),
    7: ("cb_52_8", "CB 52-8 Out Feeder 3"),
    8: ("cb_52_9", "CB 52-9 Out Feeder 4"),
    9: ("cb_52_10", "CB 52-10 XFMR 1 LV"),
    10: ("cb_52_11", "CB 52-11 XFMR 2 LV"),
    11: ("cb_52_12", "CB 52-12 Spare"),
    # Disconnect Switches
    12: ("ds_89_1", "DS 89-1"),
    13: ("ds_89_2", "DS 89-2"),
    14: ("ds_89_3", "DS 89-3"),
    15: ("ds_89_4", "DS 89-4"),
    # Protective Relays
    16: ("relay_50_51_1", "Relay 50/51-1 OC"),
    17: ("relay_50_51_2", "Relay 50/51-2 OC"),
    18: ("relay_87T_1", "Relay 87T-1 Diff"),
    19: ("relay_87T_2", "Relay 87T-2 Diff"),
    20: ("relay_21_1", "Relay 21-1 Dist"),
    21: ("relay_21_2", "Relay 21-2 Dist"),
    22: ("relay_81", "Relay 81 Freq"),
    23: ("relay_27", "Relay 27 UV"),
    24: ("relay_59", "Relay 59 OV"),
}

DNP3_ANALOG_INPUTS = {
    # Feeder 1 Measurements
    0: ("frequency", "System Frequency", "Hz", 1.0),
    1: ("feeder1_voltage_a", "Feeder 1 Va", "kV", 1.0),
    2: ("feeder1_voltage_b", "Feeder 1 Vb", "kV", 1.0),
    3: ("feeder1_voltage_c", "Feeder 1 Vc", "kV", 1.0),
    4: ("feeder1_current_a", "Feeder 1 Ia", "A", 1.0),
    5: ("feeder1_current_b", "Feeder 1 Ib", "A", 1.0),
    6: ("feeder1_current_c", "Feeder 1 Ic", "A", 1.0),
    7: ("feeder1_mw", "Feeder 1 MW", "MW", 1.0),
    8: ("feeder1_mvar", "Feeder 1 MVAR", "MVAR", 1.0),
    # Feeder 2 Measurements
    9: ("feeder2_voltage_a", "Feeder 2 Va", "kV", 1.0),
    10: ("feeder2_current_a", "Feeder 2 Ia", "A", 1.0),
    11: ("feeder2_mw", "Feeder 2 MW", "MW", 1.0),
    12: ("feeder2_mvar", "Feeder 2 MVAR", "MVAR", 1.0),
    # Bus Voltages
    13: ("bus1_voltage_a", "Bus 1 Va", "kV", 1.0),
    14: ("bus2_voltage_a", "Bus 2 Va", "kV", 1.0),
    # Transformer 1
    15: ("xfmr1_tap", "XFMR 1 Tap", "pos", 1.0),
    16: ("xfmr1_temp", "XFMR 1 Temp", "°C", 1.0),
    17: ("xfmr1_load", "XFMR 1 Load", "%", 1.0),
    18: ("xfmr1_mw", "XFMR 1 MW", "MW", 1.0),
    # Transformer 2
    19: ("xfmr2_tap", "XFMR 2 Tap", "pos", 1.0),
    20: ("xfmr2_temp", "XFMR 2 Temp", "°C", 1.0),
    21: ("xfmr2_load", "XFMR 2 Load", "%", 1.0),
    22: ("xfmr2_mw", "XFMR 2 MW", "MW", 1.0),
    # Outgoing Feeders
    23: ("out_feeder1_current", "Out Fdr 1 I", "A", 1.0),
    24: ("out_feeder1_mw", "Out Fdr 1 MW", "MW", 1.0),
    25: ("out_feeder2_current", "Out Fdr 2 I", "A", 1.0),
    26: ("out_feeder2_mw", "Out Fdr 2 MW", "MW", 1.0),
    27: ("out_feeder3_current", "Out Fdr 3 I", "A", 1.0),
    28: ("out_feeder3_mw", "Out Fdr 3 MW", "MW", 1.0),
    29: ("out_feeder4_current", "Out Fdr 4 I", "A", 1.0),
    30: ("out_feeder4_mw", "Out Fdr 4 MW", "MW", 1.0),
}

DNP3_BINARY_OUTPUTS = {
    # Breaker Controls (index: (attribute, description))
    0: ("cb_52_1", "CB 52-1 Control"),
    1: ("cb_52_2", "CB 52-2 Control"),
    2: ("cb_52_3", "CB 52-3 Control"),
    3: ("cb_52_4", "CB 52-4 Control"),
    4: ("cb_52_5", "CB 52-5 Control"),
    5: ("cb_52_6", "CB 52-6 Control"),
    6: ("cb_52_7", "CB 52-7 Control"),
    7: ("cb_52_8", "CB 52-8 Control"),
    8: ("cb_52_9", "CB 52-9 Control"),
    9: ("cb_52_10", "CB 52-10 Control"),
    10: ("cb_52_11", "CB 52-11 Control"),
    11: ("cb_52_12", "CB 52-12 Control"),
}

DNP3_ANALOG_OUTPUTS = {
    0: ("xfmr1_tap", "XFMR 1 Tap Setpoint"),
    1: ("xfmr2_tap", "XFMR 2 Tap Setpoint"),
}


# =============================================================================
# SUBSTATION SIMULATOR
# =============================================================================

class SubstationSimulator:
    """Physics-based power substation simulator"""
    
    def __init__(self):
        self.state = SubstationState()
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self.simulation_rate = int(os.getenv("SIMULATION_RATE", "100"))
        self.dnp3_address = int(os.getenv("DNP3_ADDRESS", "10"))
        
    async def connect(self):
        """Connect to Redis"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        print(f"[Substation] Connected to Redis at {redis_host}:{redis_port}")
        
    async def publish_state(self):
        """Publish state to Redis"""
        if not self.redis:
            return
            
        state_dict = self.state.to_dict()
        state_json = json.dumps(state_dict)
        
        # Publish for real-time subscribers
        await self.redis.publish("vulnot:substation:state", state_json)
        await self.redis.set("vulnot:substation:current", state_json)
        
        # Publish DNP3 points for protocol simulator
        binary_inputs = {}
        for idx, (attr, desc) in DNP3_BINARY_INPUTS.items():
            binary_inputs[str(idx)] = 1 if getattr(self.state, attr) else 0
            
        analog_inputs = {}
        for idx, (attr, desc, unit, scale) in DNP3_ANALOG_INPUTS.items():
            analog_inputs[str(idx)] = int(getattr(self.state, attr) * scale * 100)
            
        await self.redis.hset(f"vulnot:dnp3:{self.dnp3_address}:bi", mapping=binary_inputs)
        await self.redis.hset(f"vulnot:dnp3:{self.dnp3_address}:ai", mapping=analog_inputs)
        
    async def read_control_inputs(self):
        """Read control commands from Redis"""
        if not self.redis:
            return
            
        # Read binary output commands (breaker controls)
        controls = await self.redis.hgetall(f"vulnot:dnp3:{self.dnp3_address}:bo_cmd")
        if controls:
            for idx_str, value in controls.items():
                idx = int(idx_str)
                if idx in DNP3_BINARY_OUTPUTS:
                    attr, desc = DNP3_BINARY_OUTPUTS[idx]
                    new_val = value == "1"
                    old_val = getattr(self.state, attr)
                    if new_val != old_val:
                        setattr(self.state, attr, new_val)
                        print(f"[Substation] {desc}: {'CLOSE' if new_val else 'OPEN'}")
            # Clear processed commands
            await self.redis.delete(f"vulnot:dnp3:{self.dnp3_address}:bo_cmd")
            
        # Read analog output commands (tap changes)
        ao_controls = await self.redis.hgetall(f"vulnot:dnp3:{self.dnp3_address}:ao_cmd")
        if ao_controls:
            for idx_str, value in ao_controls.items():
                idx = int(idx_str)
                if idx in DNP3_ANALOG_OUTPUTS:
                    attr, desc = DNP3_ANALOG_OUTPUTS[idx]
                    new_val = int(value)
                    print(f"[Substation] {desc}: {new_val}")
                    setattr(self.state, attr, new_val)
            await self.redis.delete(f"vulnot:dnp3:{self.dnp3_address}:ao_cmd")
    
    def simulate_step(self, dt: float):
        """Simulate one time step"""
        noise = lambda base, pct=0.5: base * (1 + random.uniform(-pct/100, pct/100))
        
        # Base load varies with time of day
        hour = (time.time() / 3600) % 24
        load_factor = 0.7 + 0.3 * math.sin((hour - 6) * math.pi / 12)  # Peak at noon
        
        # Frequency varies slightly
        self.state.frequency = noise(60.0 + random.uniform(-0.02, 0.02), 0.01)
        
        # Check for frequency relay
        if self.state.frequency < 59.5 or self.state.frequency > 60.5:
            self.state.relay_81 = True
        else:
            self.state.relay_81 = False
        
        # Calculate power flow based on breaker states
        total_load = 28.0 * load_factor  # Base load in MW
        
        # Feeder 1 power (if connected)
        if self.state.cb_52_1 and self.state.cb_52_3:
            self.state.feeder1_mw = noise(total_load * 0.52, 2)
            self.state.feeder1_mvar = noise(self.state.feeder1_mw * 0.25, 3)
            self.state.feeder1_current_a = noise(self.state.feeder1_mw * 1000 / (138 * 1.732), 1)
            self.state.feeder1_current_b = noise(self.state.feeder1_current_a, 1)
            self.state.feeder1_current_c = noise(self.state.feeder1_current_a, 1)
        else:
            self.state.feeder1_mw = 0
            self.state.feeder1_mvar = 0
            self.state.feeder1_current_a = 0
            self.state.feeder1_current_b = 0
            self.state.feeder1_current_c = 0
            
        # Feeder 2 power (if connected)
        if self.state.cb_52_2 and self.state.cb_52_4:
            self.state.feeder2_mw = noise(total_load * 0.48, 2)
            self.state.feeder2_mvar = noise(self.state.feeder2_mw * 0.25, 3)
            self.state.feeder2_current_a = noise(self.state.feeder2_mw * 1000 / (138 * 1.732), 1)
        else:
            self.state.feeder2_mw = 0
            self.state.feeder2_mvar = 0
            self.state.feeder2_current_a = 0
            
        # Transformer loading
        if self.state.cb_52_10:
            self.state.xfmr1_mw = noise(self.state.feeder1_mw * 0.98, 1)
            self.state.xfmr1_load = (self.state.xfmr1_mw / 30.0) * 100  # 30 MVA rating
            self.state.xfmr1_temp = 35 + self.state.xfmr1_load * 0.4 + noise(0, 5)
        else:
            self.state.xfmr1_mw = 0
            self.state.xfmr1_load = 0
            self.state.xfmr1_temp = max(25, self.state.xfmr1_temp - 0.1)
            
        if self.state.cb_52_11:
            self.state.xfmr2_mw = noise(self.state.feeder2_mw * 0.98, 1)
            self.state.xfmr2_load = (self.state.xfmr2_mw / 30.0) * 100
            self.state.xfmr2_temp = 35 + self.state.xfmr2_load * 0.4 + noise(0, 5)
        else:
            self.state.xfmr2_mw = 0
            self.state.xfmr2_load = 0
            self.state.xfmr2_temp = max(25, self.state.xfmr2_temp - 0.1)
        
        # Bus voltages affected by tap position
        tap_effect = (self.state.xfmr1_tap - 8) * 0.0125  # ±1.25% per tap
        self.state.bus1_voltage_a = noise(7.97 * (1 + tap_effect), 0.3)
        self.state.bus1_voltage_b = noise(self.state.bus1_voltage_a, 0.2)
        self.state.bus1_voltage_c = noise(self.state.bus1_voltage_a, 0.2)
        
        tap_effect2 = (self.state.xfmr2_tap - 8) * 0.0125
        self.state.bus2_voltage_a = noise(7.97 * (1 + tap_effect2), 0.3)
        
        # Outgoing feeder loads (if breakers closed)
        if self.state.cb_52_6:
            self.state.out_feeder1_mw = noise(6.5 * load_factor, 3)
            self.state.out_feeder1_current = self.state.out_feeder1_mw * 1000 / (13.8 * 1.732)
        else:
            self.state.out_feeder1_mw = 0
            self.state.out_feeder1_current = 0
            
        if self.state.cb_52_7:
            self.state.out_feeder2_mw = noise(5.8 * load_factor, 3)
            self.state.out_feeder2_current = self.state.out_feeder2_mw * 1000 / (13.8 * 1.732)
        else:
            self.state.out_feeder2_mw = 0
            self.state.out_feeder2_current = 0
            
        if self.state.cb_52_8:
            self.state.out_feeder3_mw = noise(8.2 * load_factor, 3)
            self.state.out_feeder3_current = self.state.out_feeder3_mw * 1000 / (13.8 * 1.732)
        else:
            self.state.out_feeder3_mw = 0
            self.state.out_feeder3_current = 0
            
        if self.state.cb_52_9:
            self.state.out_feeder4_mw = noise(7.5 * load_factor, 3)
            self.state.out_feeder4_current = self.state.out_feeder4_mw * 1000 / (13.8 * 1.732)
        else:
            self.state.out_feeder4_mw = 0
            self.state.out_feeder4_current = 0
        
        # Check voltage relays
        if self.state.bus1_voltage_a < 7.0:  # Undervoltage
            self.state.relay_27 = True
        else:
            self.state.relay_27 = False
            
        if self.state.bus1_voltage_a > 8.5:  # Overvoltage
            self.state.relay_59 = True
        else:
            self.state.relay_59 = False
        
        # Generate alarms
        self.state.alarms = []
        
        if self.state.xfmr1_temp > 75:
            self.state.alarms.append({"level": "HIGH", "message": "XFMR 1 High Temperature", "tag": "XFMR1-TEMP"})
        if self.state.xfmr2_temp > 75:
            self.state.alarms.append({"level": "HIGH", "message": "XFMR 2 High Temperature", "tag": "XFMR2-TEMP"})
        if self.state.xfmr1_load > 100:
            self.state.alarms.append({"level": "HIGH", "message": "XFMR 1 Overload", "tag": "XFMR1-LOAD"})
        if self.state.relay_27:
            self.state.alarms.append({"level": "HIGH", "message": "Bus Undervoltage", "tag": "27-UV"})
        if self.state.relay_59:
            self.state.alarms.append({"level": "HIGH", "message": "Bus Overvoltage", "tag": "59-OV"})
        if self.state.relay_81:
            self.state.alarms.append({"level": "HIGH", "message": "Frequency Deviation", "tag": "81-FREQ"})
        if not self.state.cb_52_5:  # Bus tie open
            self.state.alarms.append({"level": "MEDIUM", "message": "Bus Tie Open", "tag": "52-5"})
            
        self.state.timestamp = time.time()
        
    async def run(self):
        """Main simulation loop"""
        await self.connect()
        self.running = True
        
        print(f"[Substation] Starting simulation (DNP3 Address: {self.dnp3_address})")
        
        while self.running:
            loop_start = time.time()
            
            await self.read_control_inputs()
            self.simulate_step(self.simulation_rate / 1000.0)
            await self.publish_state()
            
            elapsed = time.time() - loop_start
            sleep_time = max(0, (self.simulation_rate / 1000.0) - elapsed)
            await asyncio.sleep(sleep_time)


# =============================================================================
# DNP3 OUTSTATION (Simplified TCP Implementation)
# =============================================================================

class SimpleDNP3Outstation:
    """Simplified DNP3 outstation over TCP for training purposes"""
    
    DNP3_START = b'\x05\x64'
    
    def __init__(self, simulator: SubstationSimulator):
        self.simulator = simulator
        self.port = int(os.getenv("DNP3_PORT", "20000"))
        self.address = int(os.getenv("DNP3_ADDRESS", "10"))
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming DNP3 client connection"""
        addr = writer.get_extra_info('peername')
        print(f"[DNP3] Client connected from {addr}")
        
        try:
            while True:
                # Read DNP3 frame
                data = await reader.read(292)  # Max DNP3 frame size
                if not data:
                    break
                    
                # Log received data
                print(f"[DNP3] Received {len(data)} bytes from {addr}")
                
                # Parse and respond (simplified)
                response = await self.process_request(data)
                if response:
                    writer.write(response)
                    await writer.drain()
                    
        except Exception as e:
            print(f"[DNP3] Error handling client: {e}")
        finally:
            print(f"[DNP3] Client {addr} disconnected")
            writer.close()
            await writer.wait_closed()
            
    async def process_request(self, data: bytes) -> Optional[bytes]:
        """Process DNP3 request and generate response"""
        if len(data) < 10:
            return None
            
        # Check for DNP3 start bytes
        if data[0:2] != self.DNP3_START:
            return None
            
        # Extract function code (byte 12 in typical request)
        if len(data) > 12:
            func_code = data[12]
            
            # Function code 1 = Read
            if func_code == 0x01:
                return self.build_read_response(data)
                
            # Function code 2 = Write
            elif func_code == 0x02:
                return await self.process_write(data)
                
            # Function code 3 = Select
            elif func_code == 0x03:
                return self.build_select_response(data)
                
            # Function code 4 = Operate
            elif func_code == 0x04:
                return await self.process_operate(data)
                
        return None
        
    def build_read_response(self, request: bytes) -> bytes:
        """Build response to read request"""
        # Simplified response with current values
        state = self.simulator.state
        
        # Build DNP3 response frame
        response = bytearray(self.DNP3_START)
        response.append(0x44)  # Length
        response.append(0x01)  # Control
        response.extend(self.address.to_bytes(2, 'little'))  # Destination
        response.extend((1).to_bytes(2, 'little'))  # Source (master)
        response.extend(b'\x00\x00')  # CRC placeholder
        
        # Application layer
        response.append(0xC0)  # Application control
        response.append(0x81)  # Response function code
        response.extend(b'\x00\x00')  # IIN bytes
        
        # Add some analog input data
        response.append(0x1E)  # Object 30 - Analog Input
        response.append(0x01)  # Variation 1
        response.append(0x00)  # Qualifier
        
        return bytes(response)
        
    async def process_write(self, request: bytes) -> bytes:
        """Process write request"""
        print(f"[DNP3] Write request received")
        # Return success response
        return self.build_response(0x81, b'\x00\x00')
        
    def build_select_response(self, request: bytes) -> bytes:
        """Build select response"""
        return self.build_response(0x81, b'\x00\x00')
        
    async def process_operate(self, request: bytes) -> bytes:
        """Process operate request (control command)"""
        print(f"[DNP3] Operate request received")
        
        # Extract control point and value from request
        # Simplified - in real implementation, parse CROB
        if len(request) > 20:
            point_index = request[15] if len(request) > 15 else 0
            control_code = request[16] if len(request) > 16 else 0
            
            # Process control
            if point_index < len(DNP3_BINARY_OUTPUTS):
                attr, desc = DNP3_BINARY_OUTPUTS[point_index]
                # Trip = 0x41, Close = 0x81
                new_value = control_code == 0x81
                
                # Store command for simulator to process
                if self.simulator.redis:
                    await self.simulator.redis.hset(
                        f"vulnot:dnp3:{self.address}:bo_cmd",
                        str(point_index),
                        "1" if new_value else "0"
                    )
                print(f"[DNP3] Control: {desc} -> {'CLOSE' if new_value else 'TRIP'}")
        
        return self.build_response(0x81, b'\x00\x00')
        
    def build_response(self, func_code: int, data: bytes) -> bytes:
        """Build generic DNP3 response"""
        response = bytearray(self.DNP3_START)
        response.append(len(data) + 10)  # Length
        response.append(0x44)  # Control
        response.extend((1).to_bytes(2, 'little'))  # Destination (master)
        response.extend(self.address.to_bytes(2, 'little'))  # Source
        response.extend(b'\x00\x00')  # CRC
        response.append(0xC0)  # App control
        response.append(func_code)
        response.extend(data)
        return bytes(response)
        
    async def run(self):
        """Start DNP3 server"""
        server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            self.port
        )
        
        print(f"[DNP3] Outstation listening on port {self.port} (Address: {self.address})")
        print(f"[DNP3] ⚠️  INTENTIONALLY VULNERABLE - NO AUTHENTICATION")
        
        async with server:
            await server.serve_forever()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    simulator = SubstationSimulator()
    outstation = SimpleDNP3Outstation(simulator)
    
    try:
        # Run both simulator and DNP3 server
        await asyncio.gather(
            simulator.run(),
            outstation.run()
        )
    except KeyboardInterrupt:
        print("\n[Substation] Shutting down...")
        simulator.running = False


if __name__ == "__main__":
    asyncio.run(main())

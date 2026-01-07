"""
VULNOT BACnet Building Automation Simulator
Simulates a commercial building with HVAC, lighting, and access control

Building: 10-Story Office Building
- 4 HVAC Air Handling Units (AHUs)
- Variable Air Volume (VAV) boxes per floor
- Chiller plant
- Lighting zones
- Access control points
"""

import asyncio
import json
import os
import time
import math
import random
import struct
import socket
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import IntEnum

import redis.asyncio as redis


# =============================================================================
# BACNET CONSTANTS
# =============================================================================

BACNET_PORT = 47808

class BACnetObjectType(IntEnum):
    ANALOG_INPUT = 0
    ANALOG_OUTPUT = 1
    ANALOG_VALUE = 2
    BINARY_INPUT = 3
    BINARY_OUTPUT = 4
    BINARY_VALUE = 5
    DEVICE = 8
    SCHEDULE = 17
    TREND_LOG = 20

class BACnetPropertyId(IntEnum):
    OBJECT_IDENTIFIER = 75
    OBJECT_NAME = 77
    OBJECT_TYPE = 79
    PRESENT_VALUE = 85
    DESCRIPTION = 28
    DEVICE_TYPE = 31
    STATUS_FLAGS = 111
    UNITS = 117


# =============================================================================
# BUILDING STATE
# =============================================================================

@dataclass
class AHUState:
    """Air Handling Unit state"""
    id: int = 1
    name: str = "AHU-1"
    
    # Status
    running: bool = True
    mode: str = "COOLING"  # HEATING, COOLING, ECONOMIZER, OFF
    fault: bool = False
    
    # Supply Air
    supply_temp: float = 55.0  # °F
    supply_temp_setpoint: float = 55.0
    supply_flow: float = 15000.0  # CFM
    supply_pressure: float = 1.5  # in WC
    supply_pressure_setpoint: float = 1.5
    
    # Return Air
    return_temp: float = 72.0  # °F
    return_flow: float = 14500.0  # CFM
    return_humidity: float = 45.0  # %RH
    
    # Mixed Air
    mixed_temp: float = 62.0  # °F
    outside_air_damper: float = 25.0  # %
    return_air_damper: float = 75.0  # %
    
    # Coils
    cooling_valve: float = 45.0  # %
    heating_valve: float = 0.0  # %
    
    # Fan
    supply_fan_speed: float = 75.0  # %
    supply_fan_vfd: float = 45.0  # Hz
    return_fan_speed: float = 70.0  # %
    
    # Filter
    filter_dp: float = 0.8  # in WC
    filter_status: str = "OK"  # OK, DIRTY, REPLACE


@dataclass
class VAVState:
    """Variable Air Volume box state"""
    id: int = 1
    zone: str = "Floor-1-North"
    
    # Zone conditions
    zone_temp: float = 72.0  # °F
    zone_temp_setpoint: float = 72.0
    zone_humidity: float = 45.0  # %RH
    zone_co2: float = 650.0  # ppm
    occupied: bool = True
    
    # VAV Box
    damper_position: float = 65.0  # %
    airflow: float = 450.0  # CFM
    airflow_setpoint: float = 450.0
    discharge_temp: float = 58.0  # °F
    
    # Reheat
    reheat_valve: float = 0.0  # %
    reheat_active: bool = False


@dataclass 
class ChillerState:
    """Chiller plant state"""
    running: bool = True
    mode: str = "AUTO"
    fault: bool = False
    
    # Temperatures
    chilled_water_supply_temp: float = 44.0  # °F
    chilled_water_return_temp: float = 54.0  # °F
    condenser_water_supply_temp: float = 85.0  # °F
    condenser_water_return_temp: float = 95.0  # °F
    
    # Setpoints
    chilled_water_setpoint: float = 44.0
    
    # Flow
    chilled_water_flow: float = 1200.0  # GPM
    condenser_water_flow: float = 1500.0  # GPM
    
    # Power
    compressor_amps: float = 250.0  # A
    power_consumption: float = 180.0  # kW
    
    # Efficiency
    tons: float = 450.0
    kw_per_ton: float = 0.4


@dataclass
class BuildingState:
    """Complete building state"""
    timestamp: float = field(default_factory=time.time)
    
    # Weather
    outside_temp: float = 85.0  # °F
    outside_humidity: float = 60.0  # %RH
    
    # AHUs
    ahus: List[AHUState] = field(default_factory=lambda: [
        AHUState(id=1, name="AHU-1"),
        AHUState(id=2, name="AHU-2"),
        AHUState(id=3, name="AHU-3"),
        AHUState(id=4, name="AHU-4"),
    ])
    
    # VAVs (simplified - 4 per AHU)
    vavs: List[VAVState] = field(default_factory=list)
    
    # Chiller
    chiller: ChillerState = field(default_factory=ChillerState)
    
    # Lighting
    lighting_zones: Dict[str, float] = field(default_factory=lambda: {
        "Lobby": 100.0,
        "Floor-1": 85.0,
        "Floor-2": 85.0,
        "Floor-3": 75.0,
        "Parking": 50.0,
        "Exterior": 100.0,
    })
    
    # Access Control
    access_points: Dict[str, bool] = field(default_factory=lambda: {
        "Main-Entrance": True,
        "Loading-Dock": False,
        "Stairwell-A": True,
        "Stairwell-B": True,
        "Elevator-Lobby": True,
        "Server-Room": True,
    })
    
    # Energy
    total_power: float = 450.0  # kW
    demand_limit: float = 600.0  # kW
    
    # Alarms
    alarms: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "outside_temp": self.outside_temp,
            "outside_humidity": self.outside_humidity,
            "ahus": [asdict(ahu) for ahu in self.ahus],
            "vavs": [asdict(vav) for vav in self.vavs],
            "chiller": asdict(self.chiller),
            "lighting_zones": self.lighting_zones,
            "access_points": self.access_points,
            "total_power": self.total_power,
            "alarms": self.alarms,
        }


# =============================================================================
# BACNET OBJECT DATABASE
# =============================================================================

class BACnetObjectDB:
    """BACnet object database"""
    
    def __init__(self, building: BuildingState):
        self.building = building
        self.objects: Dict[Tuple[int, int], dict] = {}
        self._build_objects()
        
    def _build_objects(self):
        """Build BACnet object database from building state"""
        # Device object
        self.objects[(BACnetObjectType.DEVICE, 1)] = {
            "name": "VULNOT-BAS-1",
            "description": "Building Automation Controller",
            "model": "VULNOT-DDC-4000",
            "vendor": "Mjolnir Security",
        }
        
        obj_id = 1
        
        # AHU objects
        for ahu in self.building.ahus:
            # Supply temp
            self.objects[(BACnetObjectType.ANALOG_INPUT, obj_id)] = {
                "name": f"AHU-{ahu.id}-Supply-Temp",
                "description": f"AHU {ahu.id} Supply Air Temperature",
                "units": "degF",
                "attr": f"ahus[{ahu.id-1}].supply_temp",
            }
            obj_id += 1
            
            # Supply temp setpoint
            self.objects[(BACnetObjectType.ANALOG_VALUE, obj_id)] = {
                "name": f"AHU-{ahu.id}-Supply-Temp-SP",
                "description": f"AHU {ahu.id} Supply Temp Setpoint",
                "units": "degF",
                "attr": f"ahus[{ahu.id-1}].supply_temp_setpoint",
                "writable": True,
            }
            obj_id += 1
            
            # Cooling valve
            self.objects[(BACnetObjectType.ANALOG_OUTPUT, obj_id)] = {
                "name": f"AHU-{ahu.id}-Cooling-Valve",
                "description": f"AHU {ahu.id} Cooling Valve Position",
                "units": "percent",
                "attr": f"ahus[{ahu.id-1}].cooling_valve",
                "writable": True,
            }
            obj_id += 1
            
            # Fan running status
            self.objects[(BACnetObjectType.BINARY_INPUT, obj_id)] = {
                "name": f"AHU-{ahu.id}-Supply-Fan-Status",
                "description": f"AHU {ahu.id} Supply Fan Running",
                "attr": f"ahus[{ahu.id-1}].running",
            }
            obj_id += 1
            
            # Fan command
            self.objects[(BACnetObjectType.BINARY_OUTPUT, obj_id)] = {
                "name": f"AHU-{ahu.id}-Supply-Fan-Cmd",
                "description": f"AHU {ahu.id} Supply Fan Command",
                "attr": f"ahus[{ahu.id-1}].running",
                "writable": True,
            }
            obj_id += 1
            
            # Outside air damper
            self.objects[(BACnetObjectType.ANALOG_OUTPUT, obj_id)] = {
                "name": f"AHU-{ahu.id}-OA-Damper",
                "description": f"AHU {ahu.id} Outside Air Damper",
                "units": "percent",
                "attr": f"ahus[{ahu.id-1}].outside_air_damper",
                "writable": True,
            }
            obj_id += 1
            
        # Chiller objects
        self.objects[(BACnetObjectType.ANALOG_INPUT, obj_id)] = {
            "name": "Chiller-CHWS-Temp",
            "description": "Chilled Water Supply Temperature",
            "units": "degF",
            "attr": "chiller.chilled_water_supply_temp",
        }
        obj_id += 1
        
        self.objects[(BACnetObjectType.ANALOG_VALUE, obj_id)] = {
            "name": "Chiller-CHWS-SP",
            "description": "Chilled Water Setpoint",
            "units": "degF",
            "attr": "chiller.chilled_water_setpoint",
            "writable": True,
        }
        obj_id += 1
        
        self.objects[(BACnetObjectType.BINARY_OUTPUT, obj_id)] = {
            "name": "Chiller-Enable",
            "description": "Chiller Enable Command",
            "attr": "chiller.running",
            "writable": True,
        }
        obj_id += 1
        
        # Lighting
        for zone_name in self.building.lighting_zones.keys():
            self.objects[(BACnetObjectType.ANALOG_OUTPUT, obj_id)] = {
                "name": f"Lighting-{zone_name}",
                "description": f"{zone_name} Lighting Level",
                "units": "percent",
                "zone": zone_name,
                "writable": True,
            }
            obj_id += 1
            
        # Access control
        for point_name in self.building.access_points.keys():
            self.objects[(BACnetObjectType.BINARY_VALUE, obj_id)] = {
                "name": f"Access-{point_name}",
                "description": f"{point_name} Lock Status",
                "point": point_name,
                "writable": True,
            }
            obj_id += 1
            
    def get_object(self, obj_type: int, instance: int) -> Optional[dict]:
        return self.objects.get((obj_type, instance))
        
    def get_value(self, obj_type: int, instance: int) -> Optional[float]:
        obj = self.get_object(obj_type, instance)
        if not obj:
            return None
            
        if "attr" in obj:
            # Navigate nested attributes
            parts = obj["attr"].split(".")
            value = self.building
            for part in parts:
                if "[" in part:
                    name, idx = part.rstrip("]").split("[")
                    value = getattr(value, name)[int(idx)]
                else:
                    value = getattr(value, part)
            return value
        elif "zone" in obj:
            return self.building.lighting_zones.get(obj["zone"], 0)
        elif "point" in obj:
            return 1 if self.building.access_points.get(obj["point"], False) else 0
            
        return None
        
    def set_value(self, obj_type: int, instance: int, value: float) -> bool:
        obj = self.get_object(obj_type, instance)
        if not obj or not obj.get("writable"):
            return False
            
        if "attr" in obj:
            parts = obj["attr"].split(".")
            target = self.building
            for part in parts[:-1]:
                if "[" in part:
                    name, idx = part.rstrip("]").split("[")
                    target = getattr(target, name)[int(idx)]
                else:
                    target = getattr(target, part)
            setattr(target, parts[-1], value)
            return True
        elif "zone" in obj:
            self.building.lighting_zones[obj["zone"]] = value
            return True
        elif "point" in obj:
            self.building.access_points[obj["point"]] = bool(value)
            return True
            
        return False


# =============================================================================
# BUILDING SIMULATOR
# =============================================================================

class BuildingSimulator:
    """Building automation simulator"""
    
    def __init__(self):
        self.state = BuildingState()
        self._init_vavs()
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self.simulation_rate = int(os.getenv("SIMULATION_RATE", "100"))
        
    def _init_vavs(self):
        """Initialize VAV boxes"""
        vav_id = 1
        zones = ["North", "South", "East", "West"]
        for floor in range(1, 11):
            for zone in zones:
                self.state.vavs.append(VAVState(
                    id=vav_id,
                    zone=f"Floor-{floor}-{zone}",
                    zone_temp=random.uniform(70, 74),
                    occupied=(floor < 8),  # Upper floors unoccupied
                ))
                vav_id += 1
                
    async def connect(self):
        """Connect to Redis"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        print(f"[Building] Connected to Redis at {redis_host}:{redis_port}")
        
    async def publish_state(self):
        """Publish state to Redis"""
        if not self.redis:
            return
            
        state_json = json.dumps(self.state.to_dict())
        await self.redis.publish("vulnot:building:state", state_json)
        await self.redis.set("vulnot:building:current", state_json)
        
    async def read_control_inputs(self):
        """Read control commands from Redis"""
        if not self.redis:
            return
            
        controls = await self.redis.hgetall("vulnot:bacnet:cmd")
        if controls:
            for key, value in controls.items():
                obj_type, instance = map(int, key.split(":"))
                # Apply to building state through object DB
            await self.redis.delete("vulnot:bacnet:cmd")
            
    def simulate_step(self, dt: float):
        """Simulate one time step"""
        noise = lambda base, pct=1: base * (1 + random.uniform(-pct/100, pct/100))
        
        # Outside conditions (slow sine wave)
        hour = (time.time() / 3600) % 24
        self.state.outside_temp = 75 + 15 * math.sin((hour - 6) * math.pi / 12)
        self.state.outside_humidity = 50 + 20 * math.sin((hour - 12) * math.pi / 12)
        
        # Simulate each AHU
        for ahu in self.state.ahus:
            if not ahu.running:
                ahu.supply_flow = 0
                ahu.supply_fan_speed = 0
                continue
                
            # Supply air temperature control
            temp_error = ahu.supply_temp_setpoint - ahu.supply_temp
            if temp_error > 0:  # Need to heat
                ahu.cooling_valve = max(0, ahu.cooling_valve - 2)
                ahu.heating_valve = min(100, ahu.heating_valve + 2)
            else:  # Need to cool
                ahu.heating_valve = max(0, ahu.heating_valve - 2)
                ahu.cooling_valve = min(100, ahu.cooling_valve + 2)
                
            # Supply temp responds to valve positions
            if ahu.cooling_valve > 0:
                ahu.supply_temp -= ahu.cooling_valve * 0.01
            if ahu.heating_valve > 0:
                ahu.supply_temp += ahu.heating_valve * 0.01
                
            ahu.supply_temp = noise(max(45, min(85, ahu.supply_temp)), 0.5)
            
            # Economizer - use outside air when favorable
            if self.state.outside_temp < ahu.supply_temp_setpoint + 5:
                ahu.outside_air_damper = min(100, ahu.outside_air_damper + 1)
                ahu.mode = "ECONOMIZER"
            else:
                ahu.outside_air_damper = max(15, ahu.outside_air_damper - 1)
                ahu.mode = "COOLING" if ahu.cooling_valve > ahu.heating_valve else "HEATING"
                
            ahu.return_air_damper = 100 - ahu.outside_air_damper
            
            # Mixed air temp
            ahu.mixed_temp = (
                ahu.return_temp * (ahu.return_air_damper / 100) +
                self.state.outside_temp * (ahu.outside_air_damper / 100)
            )
            
            # Supply pressure control
            pressure_error = ahu.supply_pressure_setpoint - ahu.supply_pressure
            ahu.supply_fan_speed = min(100, max(20, ahu.supply_fan_speed + pressure_error * 5))
            ahu.supply_fan_vfd = ahu.supply_fan_speed * 0.6
            ahu.supply_pressure = noise(ahu.supply_pressure_setpoint, 2)
            ahu.supply_flow = noise(ahu.supply_fan_speed * 200, 1)
            
            # Return conditions
            ahu.return_temp = noise(72, 1)
            ahu.return_humidity = noise(45, 2)
            ahu.return_flow = ahu.supply_flow * 0.97
            ahu.return_fan_speed = ahu.supply_fan_speed * 0.95
            
            # Filter DP increases over time
            ahu.filter_dp = noise(0.5 + (time.time() % 86400) / 86400 * 1.0, 3)
            if ahu.filter_dp > 1.5:
                ahu.filter_status = "DIRTY"
            if ahu.filter_dp > 2.0:
                ahu.filter_status = "REPLACE"
                
        # Simulate VAV boxes
        for vav in self.state.vavs:
            # Zone temp based on occupancy and time
            load = 2.0 if vav.occupied else 0.5
            vav.zone_temp += (load - 1) * 0.01
            
            # VAV damper control
            temp_error = vav.zone_temp - vav.zone_temp_setpoint
            vav.damper_position = min(100, max(10, vav.damper_position + temp_error * 2))
            vav.airflow = vav.damper_position * 7  # Max 700 CFM
            vav.airflow_setpoint = vav.airflow
            
            # CO2 based on occupancy
            if vav.occupied:
                vav.zone_co2 = min(1200, vav.zone_co2 + random.uniform(0, 5))
            else:
                vav.zone_co2 = max(400, vav.zone_co2 - random.uniform(0, 10))
                
            vav.zone_temp = noise(vav.zone_temp, 0.3)
            vav.zone_humidity = noise(45, 2)
            
        # Chiller
        if self.state.chiller.running:
            # Chilled water temp control
            temp_error = self.state.chiller.chilled_water_setpoint - self.state.chiller.chilled_water_supply_temp
            if temp_error > 0:
                self.state.chiller.chilled_water_supply_temp -= 0.1
            else:
                self.state.chiller.chilled_water_supply_temp += 0.05
                
            self.state.chiller.chilled_water_supply_temp = noise(
                max(40, min(50, self.state.chiller.chilled_water_supply_temp)), 0.5
            )
            self.state.chiller.chilled_water_return_temp = self.state.chiller.chilled_water_supply_temp + 10
            
            # Power consumption based on load
            self.state.chiller.tons = sum(
                ahu.cooling_valve * 1.5 for ahu in self.state.ahus
            )
            self.state.chiller.power_consumption = self.state.chiller.tons * self.state.chiller.kw_per_ton
            self.state.chiller.compressor_amps = self.state.chiller.power_consumption * 1.4
            
        # Total building power
        hvac_power = sum(ahu.supply_fan_speed * 0.5 for ahu in self.state.ahus)
        chiller_power = self.state.chiller.power_consumption if self.state.chiller.running else 0
        lighting_power = sum(self.state.lighting_zones.values()) * 0.1
        self.state.total_power = hvac_power + chiller_power + lighting_power + 50  # Base load
        
        # Alarms
        self.state.alarms = []
        for ahu in self.state.ahus:
            if ahu.filter_status == "REPLACE":
                self.state.alarms.append({
                    "level": "MEDIUM",
                    "message": f"AHU-{ahu.id} Filter Requires Replacement",
                    "tag": f"AHU-{ahu.id}-FILTER"
                })
            if ahu.supply_temp > 65:
                self.state.alarms.append({
                    "level": "HIGH",
                    "message": f"AHU-{ahu.id} High Supply Air Temp",
                    "tag": f"AHU-{ahu.id}-SAT"
                })
                
        if self.state.total_power > self.state.demand_limit:
            self.state.alarms.append({
                "level": "HIGH",
                "message": "Building Demand Limit Exceeded",
                "tag": "DEMAND"
            })
            
        self.state.timestamp = time.time()
        
    async def run(self):
        """Main simulation loop"""
        await self.connect()
        self.running = True
        
        print("[Building] Starting building automation simulation")
        print(f"[Building] {len(self.state.ahus)} AHUs, {len(self.state.vavs)} VAVs")
        
        while self.running:
            loop_start = time.time()
            
            await self.read_control_inputs()
            self.simulate_step(self.simulation_rate / 1000.0)
            await self.publish_state()
            
            elapsed = time.time() - loop_start
            sleep_time = max(0, (self.simulation_rate / 1000.0) - elapsed)
            await asyncio.sleep(sleep_time)


# =============================================================================
# BACNET SERVER
# =============================================================================

class BACnetServer:
    """Simplified BACnet/IP server"""
    
    def __init__(self, simulator: BuildingSimulator):
        self.simulator = simulator
        self.port = int(os.getenv("BACNET_PORT", "47808"))
        self.object_db: Optional[BACnetObjectDB] = None
        
    def build_whois_response(self, device_id: int = 1) -> bytes:
        """Build I-Am response"""
        # Simplified BACnet I-Am
        return struct.pack(
            ">BBHHIHH",
            0x81,  # BACnet/IP
            0x0A,  # Original-Unicast-NPDU
            0x00, 0x11,  # Length
            device_id,  # Device instance
            0x00, 0x00  # Padding
        )
        
    def build_read_response(self, obj_type: int, instance: int, prop_id: int) -> bytes:
        """Build ReadProperty response"""
        value = self.object_db.get_value(obj_type, instance) if self.object_db else 0
        
        # Simplified response
        return struct.pack(
            ">BBHHBBf",
            0x81,  # BACnet/IP
            0x0A,  # Original-Unicast-NPDU
            0x00, 0x10,  # Length
            obj_type,
            instance,
            float(value) if value else 0.0
        )
        
    async def handle_packet(self, data: bytes, addr: tuple) -> Optional[bytes]:
        """Handle incoming BACnet packet"""
        if len(data) < 4:
            return None
            
        # Parse BACnet/IP header
        bvlc_type = data[0]
        bvlc_func = data[1]
        
        if bvlc_type != 0x81:  # Not BACnet/IP
            return None
            
        # Log the request
        print(f"[BACnet] Request from {addr}: func={hex(bvlc_func)}")
        
        if bvlc_func == 0x0A:  # Original-Unicast-NPDU
            # Check for Who-Is (simplified)
            if len(data) > 6 and data[6] == 0x10:  # Unconfirmed Who-Is
                print(f"[BACnet] Who-Is from {addr}")
                return self.build_whois_response()
                
            # Check for ReadProperty (simplified)
            if len(data) > 10:
                obj_type = data[7]
                instance = data[8]
                prop_id = data[9] if len(data) > 9 else BACnetPropertyId.PRESENT_VALUE
                print(f"[BACnet] ReadProperty: ({obj_type}, {instance}), prop={prop_id}")
                return self.build_read_response(obj_type, instance, prop_id)
                
        return None
        
    async def run(self):
        """Run BACnet/IP server"""
        self.object_db = BACnetObjectDB(self.simulator.state)
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port))
        sock.setblocking(False)
        
        print(f"[BACnet] Server running on UDP port {self.port}")
        print("[BACnet] ⚠️  INTENTIONALLY VULNERABLE - NO AUTHENTICATION")
        
        loop = asyncio.get_event_loop()
        
        while True:
            try:
                data, addr = await loop.run_in_executor(None, lambda: sock.recvfrom(1500))
                response = await self.handle_packet(data, addr)
                if response:
                    sock.sendto(response, addr)
            except BlockingIOError:
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"[BACnet] Error: {e}")
                await asyncio.sleep(0.1)


# =============================================================================
# MAIN
# =============================================================================

async def main():
    simulator = BuildingSimulator()
    bacnet_server = BACnetServer(simulator)
    
    try:
        await asyncio.gather(
            simulator.run(),
            bacnet_server.run()
        )
    except KeyboardInterrupt:
        print("\n[Building] Shutting down...")
        simulator.running = False


if __name__ == "__main__":
    asyncio.run(main())

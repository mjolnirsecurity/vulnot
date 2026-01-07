"""
VULNOT EtherNet/IP (CIP) Simulator
Simulates a packaging line with Allen-Bradley PLCs

Process: High-Speed Packaging Line
- Bottle filler with 12 heads
- Capper/sealer station
- Labeler with vision inspection
- Case packer
- Palletizer
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
from enum import IntEnum

import redis.asyncio as redis


# =============================================================================
# EtherNet/IP CONSTANTS
# =============================================================================

ENIP_PORT = 44818

class CIPService(IntEnum):
    GET_ATTRIBUTE_ALL = 0x01
    GET_ATTRIBUTE_SINGLE = 0x0E
    SET_ATTRIBUTE_SINGLE = 0x10
    RESET = 0x05
    START = 0x06
    STOP = 0x07
    FORWARD_OPEN = 0x54
    FORWARD_CLOSE = 0x4E

class CIPClass(IntEnum):
    IDENTITY = 0x01
    MESSAGE_ROUTER = 0x02
    ASSEMBLY = 0x04
    CONNECTION = 0x06
    CONNECTION_MANAGER = 0x06


# =============================================================================
# PACKAGING LINE STATE
# =============================================================================

@dataclass
class FillerState:
    """12-head bottle filler"""
    running: bool = True
    speed: float = 350.0  # bottles per minute
    speed_setpoint: float = 350.0
    
    # Fill parameters
    fill_volume: float = 500.0  # mL
    fill_volume_setpoint: float = 500.0
    fill_tolerance: float = 2.0  # %
    
    # Heads status (12 heads)
    heads_enabled: List[bool] = field(default_factory=lambda: [True] * 12)
    head_pressures: List[float] = field(default_factory=lambda: [2.5] * 12)
    
    # Counters
    bottles_filled: int = 0
    bottles_rejected: int = 0
    fill_efficiency: float = 99.2
    
    # Faults
    low_product_alarm: bool = False
    overfill_alarm: bool = False
    head_fault: bool = False


@dataclass
class CapperState:
    """Capper/sealer station"""
    running: bool = True
    speed: float = 350.0
    
    # Torque
    torque_setpoint: float = 15.0  # in-lb
    torque_actual: float = 14.8
    torque_min: float = 12.0
    torque_max: float = 18.0
    
    # Cap feed
    cap_hopper_level: float = 75.0  # %
    cap_feed_running: bool = True
    
    # Counters
    bottles_capped: int = 0
    caps_rejected: int = 0
    
    # Faults
    cap_jam: bool = False
    low_caps_alarm: bool = False
    torque_fault: bool = False


@dataclass
class LabelerState:
    """Label applicator with vision"""
    running: bool = True
    speed: float = 350.0
    
    # Label application
    label_position: float = 0.0  # mm from bottom
    label_position_setpoint: float = 25.0
    label_skew: float = 0.0  # degrees
    label_skew_tolerance: float = 2.0
    
    # Vision system
    vision_enabled: bool = True
    vision_pass_rate: float = 99.5
    barcode_grade: str = "A"
    
    # Label roll
    labels_remaining: int = 5000
    label_roll_diameter: float = 250.0  # mm
    
    # Counters
    bottles_labeled: int = 0
    labels_rejected: int = 0
    
    # Faults
    label_jam: bool = False
    vision_fault: bool = False
    low_labels_alarm: bool = False


@dataclass
class CasePackerState:
    """Case packer"""
    running: bool = True
    speed: float = 30.0  # cases per minute
    
    # Configuration
    bottles_per_case: int = 12
    case_pattern: str = "3x4"
    
    # Current state
    bottles_in_case: int = 0
    case_forming: bool = False
    
    # Counters
    cases_packed: int = 0
    cases_rejected: int = 0
    
    # Cardboard
    blanks_remaining: int = 500
    tape_remaining: float = 90.0  # %
    
    # Faults
    case_jam: bool = False
    low_blanks_alarm: bool = False


@dataclass
class PalletizerState:
    """Robot palletizer"""
    running: bool = True
    mode: str = "AUTO"  # AUTO, MANUAL, FAULT
    
    # Robot
    robot_position: List[float] = field(default_factory=lambda: [0.0, 0.0, 500.0])  # X, Y, Z mm
    robot_speed: float = 100.0  # %
    gripper_closed: bool = False
    
    # Pallet
    pallet_pattern: str = "5x4x5"  # L x W x H
    cases_on_pallet: int = 0
    cases_per_layer: int = 20
    layers_per_pallet: int = 5
    current_layer: int = 1
    
    # Counters
    pallets_completed: int = 0
    
    # Conveyor
    infeed_conveyor: bool = True
    outfeed_conveyor: bool = True
    pallet_present: bool = True
    
    # Faults
    robot_fault: bool = False
    no_pallet_alarm: bool = False


@dataclass
class PackagingLineState:
    """Complete packaging line state"""
    timestamp: float = field(default_factory=time.time)
    
    # Line status
    line_running: bool = True
    line_mode: str = "AUTO"  # AUTO, MANUAL, E-STOP, FAULT
    line_speed: float = 350.0  # BPM
    line_efficiency: float = 95.0  # OEE %
    
    # Stations
    filler: FillerState = field(default_factory=FillerState)
    capper: CapperState = field(default_factory=CapperState)
    labeler: LabelerState = field(default_factory=LabelerState)
    case_packer: CasePackerState = field(default_factory=CasePackerState)
    palletizer: PalletizerState = field(default_factory=PalletizerState)
    
    # Conveyors
    conveyor_speeds: Dict[str, float] = field(default_factory=lambda: {
        "infeed": 100.0,
        "filler_to_capper": 100.0,
        "capper_to_labeler": 100.0,
        "labeler_to_packer": 100.0,
        "packer_to_palletizer": 100.0,
    })
    
    # Utilities
    compressed_air: float = 90.0  # PSI
    vacuum_pressure: float = -12.0  # inHg
    
    # Production
    shift_target: int = 50000
    shift_produced: int = 0
    shift_start: float = field(default_factory=time.time)
    
    # Alarms
    alarms: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "line_running": self.line_running,
            "line_mode": self.line_mode,
            "line_speed": self.line_speed,
            "line_efficiency": self.line_efficiency,
            "filler": asdict(self.filler),
            "capper": asdict(self.capper),
            "labeler": asdict(self.labeler),
            "case_packer": asdict(self.case_packer),
            "palletizer": asdict(self.palletizer),
            "conveyor_speeds": self.conveyor_speeds,
            "compressed_air": self.compressed_air,
            "vacuum_pressure": self.vacuum_pressure,
            "shift_target": self.shift_target,
            "shift_produced": self.shift_produced,
            "alarms": self.alarms,
        }


# =============================================================================
# CIP TAG DATABASE
# =============================================================================

CIP_TAGS = {
    # Line control
    "Line:Running": ("line_running", "BOOL", True),
    "Line:Mode": ("line_mode", "STRING", False),
    "Line:Speed": ("line_speed", "REAL", True),
    "Line:Efficiency": ("line_efficiency", "REAL", False),
    
    # Filler
    "Filler:Running": ("filler.running", "BOOL", True),
    "Filler:Speed": ("filler.speed", "REAL", True),
    "Filler:SpeedSP": ("filler.speed_setpoint", "REAL", True),
    "Filler:FillVolume": ("filler.fill_volume", "REAL", False),
    "Filler:FillVolumeSP": ("filler.fill_volume_setpoint", "REAL", True),
    "Filler:BottlesFilled": ("filler.bottles_filled", "DINT", False),
    "Filler:BottlesRejected": ("filler.bottles_rejected", "DINT", False),
    "Filler:HeadFault": ("filler.head_fault", "BOOL", False),
    
    # Capper
    "Capper:Running": ("capper.running", "BOOL", True),
    "Capper:TorqueSP": ("capper.torque_setpoint", "REAL", True),
    "Capper:TorqueActual": ("capper.torque_actual", "REAL", False),
    "Capper:HopperLevel": ("capper.cap_hopper_level", "REAL", False),
    "Capper:CapJam": ("capper.cap_jam", "BOOL", False),
    
    # Labeler
    "Labeler:Running": ("labeler.running", "BOOL", True),
    "Labeler:VisionEnabled": ("labeler.vision_enabled", "BOOL", True),
    "Labeler:VisionPassRate": ("labeler.vision_pass_rate", "REAL", False),
    "Labeler:LabelsRemaining": ("labeler.labels_remaining", "DINT", False),
    "Labeler:LabelJam": ("labeler.label_jam", "BOOL", False),
    
    # Case Packer
    "CasePacker:Running": ("case_packer.running", "BOOL", True),
    "CasePacker:CasesPacked": ("case_packer.cases_packed", "DINT", False),
    "CasePacker:BlanksRemaining": ("case_packer.blanks_remaining", "DINT", False),
    "CasePacker:CaseJam": ("case_packer.case_jam", "BOOL", False),
    
    # Palletizer
    "Palletizer:Running": ("palletizer.running", "BOOL", True),
    "Palletizer:Mode": ("palletizer.mode", "STRING", True),
    "Palletizer:RobotSpeed": ("palletizer.robot_speed", "REAL", True),
    "Palletizer:CasesOnPallet": ("palletizer.cases_on_pallet", "DINT", False),
    "Palletizer:PalletsCompleted": ("palletizer.pallets_completed", "DINT", False),
    "Palletizer:RobotFault": ("palletizer.robot_fault", "BOOL", False),
    
    # Production
    "Production:ShiftTarget": ("shift_target", "DINT", True),
    "Production:ShiftProduced": ("shift_produced", "DINT", False),
    
    # Utilities
    "Utility:CompressedAir": ("compressed_air", "REAL", False),
    "Utility:Vacuum": ("vacuum_pressure", "REAL", False),
}


# =============================================================================
# PACKAGING LINE SIMULATOR
# =============================================================================

class PackagingSimulator:
    """Packaging line simulator"""
    
    def __init__(self):
        self.state = PackagingLineState()
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self.simulation_rate = int(os.getenv("SIMULATION_RATE", "100"))
        
    async def connect(self):
        """Connect to Redis"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        print(f"[Packaging] Connected to Redis at {redis_host}:{redis_port}")
        
    async def publish_state(self):
        """Publish state to Redis"""
        if not self.redis:
            return
            
        state_json = json.dumps(self.state.to_dict())
        await self.redis.publish("vulnot:packaging:state", state_json)
        await self.redis.set("vulnot:packaging:current", state_json)
        
        # Publish CIP tag values
        tag_values = {}
        for tag_name, (attr_path, dtype, writable) in CIP_TAGS.items():
            value = self._get_attr_path(attr_path)
            tag_values[tag_name] = str(value)
        await self.redis.hset("vulnot:enip:tags", mapping=tag_values)
        
    def _get_attr_path(self, path: str):
        """Get attribute value from dotted path"""
        parts = path.split(".")
        value = self.state
        for part in parts:
            value = getattr(value, part)
        return value
        
    def _set_attr_path(self, path: str, value):
        """Set attribute value from dotted path"""
        parts = path.split(".")
        obj = self.state
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
        
    async def read_control_inputs(self):
        """Read control commands from Redis"""
        if not self.redis:
            return
            
        controls = await self.redis.hgetall("vulnot:enip:cmd")
        if controls:
            for tag_name, value in controls.items():
                if tag_name in CIP_TAGS:
                    attr_path, dtype, writable = CIP_TAGS[tag_name]
                    if writable:
                        if dtype == "BOOL":
                            self._set_attr_path(attr_path, value == "1" or value.lower() == "true")
                        elif dtype == "REAL":
                            self._set_attr_path(attr_path, float(value))
                        elif dtype == "DINT":
                            self._set_attr_path(attr_path, int(value))
                        elif dtype == "STRING":
                            self._set_attr_path(attr_path, value)
                        print(f"[Packaging] {tag_name} = {value}")
            await self.redis.delete("vulnot:enip:cmd")
            
    def simulate_step(self, dt: float):
        """Simulate one time step"""
        noise = lambda base, pct=1: base * (1 + random.uniform(-pct/100, pct/100))
        
        if not self.state.line_running or self.state.line_mode != "AUTO":
            return
            
        # Filler simulation
        if self.state.filler.running:
            bottles_this_step = (self.state.filler.speed / 60.0) * dt
            self.state.filler.bottles_filled += int(bottles_this_step)
            
            # Random rejects
            if random.random() < 0.002:
                self.state.filler.bottles_rejected += 1
                
            # Head pressures fluctuate
            for i in range(12):
                self.state.filler.head_pressures[i] = noise(2.5, 3)
                
            # Occasional head fault
            if random.random() < 0.0001:
                self.state.filler.head_fault = True
                self.state.filler.heads_enabled[random.randint(0, 11)] = False
                
            self.state.filler.fill_volume = noise(self.state.filler.fill_volume_setpoint, 0.5)
            self.state.filler.speed = noise(self.state.filler.speed_setpoint, 1)
            
        # Capper simulation
        if self.state.capper.running:
            self.state.capper.bottles_capped = self.state.filler.bottles_filled - self.state.filler.bottles_rejected
            self.state.capper.torque_actual = noise(self.state.capper.torque_setpoint, 5)
            
            # Cap hopper depletes
            self.state.capper.cap_hopper_level = max(0, self.state.capper.cap_hopper_level - 0.001)
            if self.state.capper.cap_hopper_level < 20:
                self.state.capper.low_caps_alarm = True
                
            # Torque fault if out of range
            if (self.state.capper.torque_actual < self.state.capper.torque_min or
                self.state.capper.torque_actual > self.state.capper.torque_max):
                self.state.capper.torque_fault = True
                
        # Labeler simulation
        if self.state.labeler.running:
            self.state.labeler.bottles_labeled = self.state.capper.bottles_capped - self.state.capper.caps_rejected
            
            # Labels deplete
            self.state.labeler.labels_remaining = max(0, self.state.labeler.labels_remaining - int(bottles_this_step))
            if self.state.labeler.labels_remaining < 500:
                self.state.labeler.low_labels_alarm = True
                
            # Vision rejects
            if self.state.labeler.vision_enabled and random.random() < 0.005:
                self.state.labeler.labels_rejected += 1
                
            self.state.labeler.label_position = noise(self.state.labeler.label_position_setpoint, 2)
            self.state.labeler.label_skew = random.uniform(-1, 1)
            
        # Case packer simulation
        if self.state.case_packer.running:
            good_bottles = (self.state.labeler.bottles_labeled - 
                          self.state.labeler.labels_rejected)
            self.state.case_packer.cases_packed = good_bottles // self.state.case_packer.bottles_per_case
            
            # Blanks deplete
            self.state.case_packer.blanks_remaining = max(0, 
                self.state.case_packer.blanks_remaining - int(self.state.case_packer.cases_packed * 0.001))
            if self.state.case_packer.blanks_remaining < 50:
                self.state.case_packer.low_blanks_alarm = True
                
        # Palletizer simulation
        if self.state.palletizer.running:
            self.state.palletizer.cases_on_pallet = (
                self.state.case_packer.cases_packed % 
                (self.state.palletizer.cases_per_layer * self.state.palletizer.layers_per_pallet)
            )
            self.state.palletizer.current_layer = (
                self.state.palletizer.cases_on_pallet // self.state.palletizer.cases_per_layer
            ) + 1
            self.state.palletizer.pallets_completed = (
                self.state.case_packer.cases_packed // 
                (self.state.palletizer.cases_per_layer * self.state.palletizer.layers_per_pallet)
            )
            
            # Robot position animation
            self.state.palletizer.robot_position[0] = 500 + 200 * random.random()
            self.state.palletizer.robot_position[1] = 500 + 200 * random.random()
            self.state.palletizer.robot_position[2] = 200 + self.state.palletizer.current_layer * 150
            
        # Update production totals
        self.state.shift_produced = self.state.filler.bottles_filled - self.state.filler.bottles_rejected
        
        # Calculate OEE
        elapsed_hours = (time.time() - self.state.shift_start) / 3600
        if elapsed_hours > 0:
            expected = self.state.line_speed * 60 * elapsed_hours
            if expected > 0:
                self.state.line_efficiency = min(100, (self.state.shift_produced / expected) * 100)
                
        # Utilities
        self.state.compressed_air = noise(90, 2)
        self.state.vacuum_pressure = noise(-12, 3)
        
        # Alarms
        self.state.alarms = []
        if self.state.filler.head_fault:
            self.state.alarms.append({"level": "HIGH", "message": "Filler Head Fault", "tag": "FILLER"})
        if self.state.capper.low_caps_alarm:
            self.state.alarms.append({"level": "MEDIUM", "message": "Low Cap Level", "tag": "CAPPER"})
        if self.state.capper.torque_fault:
            self.state.alarms.append({"level": "HIGH", "message": "Capper Torque Fault", "tag": "CAPPER"})
        if self.state.labeler.low_labels_alarm:
            self.state.alarms.append({"level": "MEDIUM", "message": "Low Label Level", "tag": "LABELER"})
        if self.state.case_packer.low_blanks_alarm:
            self.state.alarms.append({"level": "MEDIUM", "message": "Low Case Blanks", "tag": "CASEPACKER"})
        if self.state.palletizer.robot_fault:
            self.state.alarms.append({"level": "CRITICAL", "message": "Palletizer Robot Fault", "tag": "PALLETIZER"})
            
        self.state.timestamp = time.time()
        
    async def run(self):
        """Main simulation loop"""
        await self.connect()
        self.running = True
        
        print("[Packaging] Starting packaging line simulation")
        
        while self.running:
            loop_start = time.time()
            
            await self.read_control_inputs()
            self.simulate_step(self.simulation_rate / 1000.0)
            await self.publish_state()
            
            elapsed = time.time() - loop_start
            sleep_time = max(0, (self.simulation_rate / 1000.0) - elapsed)
            await asyncio.sleep(sleep_time)


# =============================================================================
# ETHERNET/IP SERVER
# =============================================================================

class EtherNetIPServer:
    """Simplified EtherNet/IP server"""
    
    def __init__(self, simulator: PackagingSimulator):
        self.simulator = simulator
        self.port = int(os.getenv("ENIP_PORT", "44818"))
        self.sessions: Dict[int, dict] = {}
        self.next_session = 1
        
    def build_list_identity_response(self) -> bytes:
        """Build ListIdentity response"""
        # EtherNet/IP encapsulation header
        identity = b"VULNOT-PAK-01\x00"  # Device name
        
        response = struct.pack(
            "<HHIIII",
            0x0063,  # Command: ListIdentity
            len(identity),  # Length
            0,  # Session handle
            0,  # Status
            0,  # Sender context
        ) + identity
        
        return response
        
    def build_register_session_response(self, session_handle: int) -> bytes:
        """Build RegisterSession response"""
        return struct.pack(
            "<HHIIII HH",
            0x0065,  # Command: RegisterSession
            4,  # Length
            session_handle,  # Session handle
            0,  # Status
            0, 0,  # Sender context
            1, 0,  # Protocol version
        )
        
    def build_read_tag_response(self, tag_name: str) -> bytes:
        """Build read tag response"""
        if tag_name in CIP_TAGS:
            attr_path, dtype, _ = CIP_TAGS[tag_name]
            value = self.simulator._get_attr_path(attr_path)
            
            if dtype == "BOOL":
                data = struct.pack("<B", 1 if value else 0)
                type_code = 0x00C1
            elif dtype == "REAL":
                data = struct.pack("<f", float(value))
                type_code = 0x00CA
            elif dtype == "DINT":
                data = struct.pack("<i", int(value))
                type_code = 0x00C4
            else:
                data = value.encode()[:40]
                type_code = 0x00D0
        else:
            data = b'\x00\x00\x00\x00'
            type_code = 0x00CA
            
        # CIP response
        return struct.pack("<HH", type_code, len(data)) + data
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle EtherNet/IP client connection"""
        addr = writer.get_extra_info('peername')
        print(f"[EtherNet/IP] Client connected from {addr}")
        
        session_handle = 0
        
        try:
            while True:
                # Read encapsulation header (24 bytes)
                header = await reader.read(24)
                if len(header) < 24:
                    break
                    
                command, length, session, status = struct.unpack("<HHII", header[:12])
                
                # Read data if any
                data = b''
                if length > 0:
                    data = await reader.read(length)
                    
                print(f"[EtherNet/IP] Command: {hex(command)}, Session: {session}")
                
                response = b''
                
                if command == 0x0063:  # ListIdentity
                    response = self.build_list_identity_response()
                    
                elif command == 0x0065:  # RegisterSession
                    session_handle = self.next_session
                    self.next_session += 1
                    self.sessions[session_handle] = {"addr": addr}
                    response = self.build_register_session_response(session_handle)
                    
                elif command == 0x0066:  # UnregisterSession
                    if session_handle in self.sessions:
                        del self.sessions[session_handle]
                    break
                    
                elif command == 0x006F:  # SendRRData (Read/Write tags)
                    # Parse CIP request (simplified)
                    if len(data) > 20:
                        # Extract tag name (very simplified)
                        tag_data = data[20:].decode('ascii', errors='ignore').split('\x00')[0]
                        if tag_data:
                            response = self.build_read_tag_response(tag_data)
                            
                if response:
                    writer.write(response)
                    await writer.drain()
                    
        except Exception as e:
            print(f"[EtherNet/IP] Error: {e}")
        finally:
            if session_handle in self.sessions:
                del self.sessions[session_handle]
            writer.close()
            await writer.wait_closed()
            print(f"[EtherNet/IP] Client disconnected: {addr}")
            
    async def run(self):
        """Run EtherNet/IP server"""
        server = await asyncio.start_server(
            self.handle_client, '0.0.0.0', self.port
        )
        
        print(f"[EtherNet/IP] Server running on TCP port {self.port}")
        print("[EtherNet/IP] ⚠️  INTENTIONALLY VULNERABLE - NO AUTHENTICATION")
        
        async with server:
            await server.serve_forever()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    simulator = PackagingSimulator()
    enip_server = EtherNetIPServer(simulator)
    
    try:
        await asyncio.gather(
            simulator.run(),
            enip_server.run()
        )
    except KeyboardInterrupt:
        print("\n[Packaging] Shutting down...")
        simulator.running = False


if __name__ == "__main__":
    asyncio.run(main())

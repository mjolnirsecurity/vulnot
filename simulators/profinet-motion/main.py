"""
VULNOT PROFINET Motion Control Simulator
Simulates a CNC machining center with servo drives and motion control

System: 5-Axis CNC Machining Center
- Siemens S120 Drive System
- SINUMERIK CNC Controller
- Linear axes (X, Y, Z)
- Rotary axes (A, C)
- Spindle drive
- Tool magazine
"""

import asyncio
import json
import os
import time
import math
import random
import struct
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import IntEnum

import redis.asyncio as redis


# =============================================================================
# PROFINET CONSTANTS
# =============================================================================

PROFINET_PORT = 34964  # PROFINET RT

class ProfinetFrameID(IntEnum):
    PTCP_SYNC = 0x0080
    PTCP_FOLLOWUP = 0x0081
    RTC1 = 0x8000
    RTC2 = 0x8001
    RTC3 = 0xC000
    DCP_HELLO = 0xFEFC
    DCP_GET_SET = 0xFEFD
    DCP_IDENTIFY = 0xFEFE
    DCP_IDENTIFY_RESP = 0xFEFF

class DriveState(IntEnum):
    NOT_READY = 0
    SWITCH_ON_DISABLED = 1
    READY_TO_SWITCH_ON = 2
    SWITCHED_ON = 3
    OPERATION_ENABLED = 4
    QUICK_STOP = 5
    FAULT_REACTION = 6
    FAULT = 7


# =============================================================================
# MOTION CONTROL STATE
# =============================================================================

@dataclass
class ServoAxis:
    """Servo axis state"""
    id: str
    name: str
    
    # Position
    actual_position: float = 0.0  # mm or degrees
    command_position: float = 0.0
    position_error: float = 0.0
    
    # Velocity
    actual_velocity: float = 0.0  # mm/s or deg/s
    command_velocity: float = 0.0
    max_velocity: float = 10000.0
    
    # Torque
    actual_torque: float = 0.0  # %
    torque_limit: float = 100.0
    
    # Status
    state: DriveState = DriveState.OPERATION_ENABLED
    homed: bool = True
    in_position: bool = True
    moving: bool = False
    
    # Limits
    positive_limit: float = 500.0
    negative_limit: float = -500.0
    positive_limit_switch: bool = False
    negative_limit_switch: bool = False
    
    # Drive parameters
    acceleration: float = 5000.0  # mm/s²
    deceleration: float = 5000.0
    jerk: float = 50000.0
    
    # Temperature
    motor_temp: float = 45.0  # °C
    drive_temp: float = 40.0
    
    # Faults
    fault_code: int = 0
    warning_code: int = 0


@dataclass
class Spindle:
    """Spindle drive state"""
    running: bool = False
    
    # Speed
    actual_speed: float = 0.0  # RPM
    command_speed: float = 0.0
    max_speed: float = 24000.0
    
    # Power/Torque
    actual_power: float = 0.0  # kW
    actual_torque: float = 0.0  # %
    
    # Tool
    tool_number: int = 1
    tool_offset: float = 0.0
    
    # Temperature
    bearing_temp: float = 35.0
    motor_temp: float = 50.0
    
    # Status
    oriented: bool = True
    clamped: bool = True
    at_speed: bool = False


@dataclass
class ToolMagazine:
    """Tool magazine state"""
    capacity: int = 60
    current_pocket: int = 1
    tools: Dict[int, dict] = field(default_factory=dict)
    
    # Status
    door_open: bool = False
    rotating: bool = False
    tool_change_active: bool = False
    
    def __post_init__(self):
        # Initialize with some tools
        for i in range(1, 21):
            self.tools[i] = {
                "id": f"T{i}",
                "type": random.choice(["endmill", "drill", "tap", "facemill"]),
                "diameter": random.uniform(3, 50),
                "length": random.uniform(50, 200),
                "life_remaining": random.uniform(50, 100),
            }


@dataclass
class CNCProgram:
    """CNC program state"""
    name: str = "O0001"
    running: bool = False
    paused: bool = False
    
    # Position
    current_line: int = 0
    total_lines: int = 500
    
    # Mode
    mode: str = "AUTO"  # AUTO, MDI, JOG, REF
    
    # Feedrate
    feedrate: float = 1000.0  # mm/min
    feedrate_override: float = 100.0  # %
    rapid_override: float = 100.0  # %
    
    # Coordinates
    work_offset: str = "G54"
    absolute_mode: bool = True


@dataclass
class CNCState:
    """Complete CNC machine state"""
    timestamp: float = field(default_factory=time.time)
    
    # Machine info
    machine_id: str = "CNC-001"
    machine_type: str = "5-Axis VMC"
    controller: str = "SINUMERIK 840D"
    
    # Axes
    axes: Dict[str, ServoAxis] = field(default_factory=lambda: {
        "X": ServoAxis(id="X", name="X-Axis", max_velocity=30000, positive_limit=800, negative_limit=0),
        "Y": ServoAxis(id="Y", name="Y-Axis", max_velocity=30000, positive_limit=500, negative_limit=0),
        "Z": ServoAxis(id="Z", name="Z-Axis", max_velocity=20000, positive_limit=0, negative_limit=-500),
        "A": ServoAxis(id="A", name="A-Axis (Tilt)", max_velocity=3600, positive_limit=120, negative_limit=-120),
        "C": ServoAxis(id="C", name="C-Axis (Rotate)", max_velocity=7200, positive_limit=99999, negative_limit=-99999),
    })
    
    # Spindle
    spindle: Spindle = field(default_factory=Spindle)
    
    # Tool magazine
    magazine: ToolMagazine = field(default_factory=ToolMagazine)
    
    # Program
    program: CNCProgram = field(default_factory=CNCProgram)
    
    # Safety
    estop: bool = False
    safety_door_open: bool = False
    coolant_on: bool = False
    chip_conveyor_on: bool = False
    
    # Alarms
    alarms: List[dict] = field(default_factory=list)
    
    # Cycle info
    cycle_time: float = 0.0
    parts_count: int = 0
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "controller": self.controller,
            "axes": {k: asdict(v) for k, v in self.axes.items()},
            "spindle": asdict(self.spindle),
            "magazine": {
                "capacity": self.magazine.capacity,
                "current_pocket": self.magazine.current_pocket,
                "tool_count": len(self.magazine.tools),
                "door_open": self.magazine.door_open,
            },
            "program": asdict(self.program),
            "estop": self.estop,
            "safety_door_open": self.safety_door_open,
            "coolant_on": self.coolant_on,
            "alarms": self.alarms,
            "cycle_time": self.cycle_time,
            "parts_count": self.parts_count,
        }


# =============================================================================
# PROFINET CYCLIC DATA (Attack Surface)
# =============================================================================

# Input data from drives (read by controller)
PROFINET_INPUTS = {
    0x0000: ("X_ActualPosition", "REAL"),
    0x0004: ("X_ActualVelocity", "REAL"),
    0x0008: ("X_ActualTorque", "INT"),
    0x000A: ("X_StatusWord", "UINT"),
    0x0010: ("Y_ActualPosition", "REAL"),
    0x0014: ("Y_ActualVelocity", "REAL"),
    0x0018: ("Y_ActualTorque", "INT"),
    0x001A: ("Y_StatusWord", "UINT"),
    0x0020: ("Z_ActualPosition", "REAL"),
    0x0024: ("Z_ActualVelocity", "REAL"),
    0x0028: ("Z_ActualTorque", "INT"),
    0x002A: ("Z_StatusWord", "UINT"),
    0x0030: ("Spindle_ActualSpeed", "REAL"),
    0x0034: ("Spindle_ActualTorque", "INT"),
    0x0036: ("Spindle_StatusWord", "UINT"),
}

# Output data to drives (written by controller) - VULNERABLE!
PROFINET_OUTPUTS = {
    0x0100: ("X_CommandPosition", "REAL", True),
    0x0104: ("X_CommandVelocity", "REAL", True),
    0x0108: ("X_ControlWord", "UINT", True),
    0x0110: ("Y_CommandPosition", "REAL", True),
    0x0114: ("Y_CommandVelocity", "REAL", True),
    0x0118: ("Y_ControlWord", "UINT", True),
    0x0120: ("Z_CommandPosition", "REAL", True),
    0x0124: ("Z_CommandVelocity", "REAL", True),
    0x0128: ("Z_ControlWord", "UINT", True),
    0x0130: ("Spindle_CommandSpeed", "REAL", True),
    0x0134: ("Spindle_ControlWord", "UINT", True),
}


# =============================================================================
# CNC SIMULATOR
# =============================================================================

class CNCSimulator:
    """CNC Machine Simulator"""
    
    def __init__(self):
        self.state = CNCState()
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self.simulation_rate = int(os.getenv("SIMULATION_RATE", "50"))  # 50ms for motion
        self._motion_profile: List[Tuple[str, float]] = []
        
    async def connect(self):
        """Connect to Redis"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        print(f"[CNC] Connected to Redis at {redis_host}:{redis_port}")
        
    async def publish_state(self):
        """Publish state to Redis"""
        if not self.redis:
            return
            
        state_json = json.dumps(self.state.to_dict())
        await self.redis.publish("vulnot:cnc:state", state_json)
        await self.redis.set("vulnot:cnc:current", state_json)
        
        # Publish PROFINET I/O data
        io_data = {}
        for addr, (name, dtype) in PROFINET_INPUTS.items():
            value = self._get_io_value(name)
            io_data[f"0x{addr:04X}:{name}"] = str(value)
        await self.redis.hset("vulnot:profinet:io", mapping=io_data)
        
    def _get_io_value(self, name: str):
        """Get value for PROFINET I/O point"""
        parts = name.split("_")
        if len(parts) < 2:
            return 0
            
        axis_or_spindle = parts[0]
        param = "_".join(parts[1:])
        
        if axis_or_spindle in self.state.axes:
            axis = self.state.axes[axis_or_spindle]
            if param == "ActualPosition":
                return axis.actual_position
            elif param == "ActualVelocity":
                return axis.actual_velocity
            elif param == "ActualTorque":
                return int(axis.actual_torque * 10)
            elif param == "StatusWord":
                return self._build_status_word(axis)
        elif axis_or_spindle == "Spindle":
            if param == "ActualSpeed":
                return self.state.spindle.actual_speed
            elif param == "ActualTorque":
                return int(self.state.spindle.actual_torque * 10)
            elif param == "StatusWord":
                return 0x0637 if self.state.spindle.running else 0x0231
                
        return 0
        
    def _build_status_word(self, axis: ServoAxis) -> int:
        """Build drive status word"""
        status = 0
        if axis.state == DriveState.OPERATION_ENABLED:
            status |= 0x0637  # Ready to operate
        if axis.in_position:
            status |= 0x0400
        if axis.moving:
            status |= 0x0800
        if axis.positive_limit_switch:
            status |= 0x4000
        if axis.negative_limit_switch:
            status |= 0x8000
        return status
        
    async def read_commands(self):
        """Read control commands from Redis"""
        if not self.redis:
            return
            
        commands = await self.redis.hgetall("vulnot:profinet:cmd")
        if commands:
            for key, value in commands.items():
                await self._process_command(key, value)
            await self.redis.delete("vulnot:profinet:cmd")
            
    async def _process_command(self, key: str, value: str):
        """Process PROFINET command"""
        print(f"[CNC] Command: {key} = {value}")
        
        try:
            # Parse address and apply
            if "CommandPosition" in key:
                axis_id = key.split("_")[0]
                if axis_id in self.state.axes:
                    self.state.axes[axis_id].command_position = float(value)
                    print(f"[CNC] ⚠️ Axis {axis_id} position command changed to {value}")
                    
            elif "CommandVelocity" in key:
                axis_id = key.split("_")[0]
                if axis_id in self.state.axes:
                    self.state.axes[axis_id].command_velocity = float(value)
                    print(f"[CNC] ⚠️ Axis {axis_id} velocity changed to {value}")
                    
            elif "ControlWord" in key:
                axis_id = key.split("_")[0]
                control = int(value)
                if control & 0x0080:  # Fault reset
                    print(f"[CNC] ⚠️ Fault reset on {axis_id}")
                if control & 0x000F == 0x000F:  # Enable
                    print(f"[CNC] ⚠️ Drive {axis_id} enabled")
                if control & 0x000F == 0x0000:  # Disable
                    print(f"[CNC] ⚠️ Drive {axis_id} DISABLED!")
                    if axis_id in self.state.axes:
                        self.state.axes[axis_id].state = DriveState.SWITCH_ON_DISABLED
                        
            elif "Spindle_CommandSpeed" in key:
                self.state.spindle.command_speed = float(value)
                print(f"[CNC] ⚠️ Spindle speed command: {value} RPM")
                
            elif "estop" in key.lower():
                self.state.estop = value.lower() == "true"
                print(f"[CNC] ⚠️ E-STOP: {self.state.estop}")
                
        except Exception as e:
            print(f"[CNC] Command error: {e}")
            
    def simulate_step(self, dt: float):
        """Simulate one time step"""
        noise = lambda base, pct=0.5: base * (1 + random.uniform(-pct/100, pct/100))
        
        if self.state.estop:
            # E-stop active - all motion stops
            for axis in self.state.axes.values():
                axis.actual_velocity = 0
                axis.moving = False
                axis.state = DriveState.QUICK_STOP
            self.state.spindle.running = False
            self.state.spindle.actual_speed = max(0, self.state.spindle.actual_speed - 500)
            return
            
        # Simulate each axis
        for axis in self.state.axes.values():
            if axis.state != DriveState.OPERATION_ENABLED:
                continue
                
            # Position control simulation
            error = axis.command_position - axis.actual_position
            axis.position_error = error
            
            if abs(error) > 0.001:
                # Calculate velocity based on error (simplified P controller)
                target_vel = min(axis.max_velocity, abs(error) * 100)
                target_vel = math.copysign(target_vel, error)
                
                # Ramp velocity
                vel_diff = target_vel - axis.actual_velocity
                max_accel = axis.acceleration * dt
                if abs(vel_diff) > max_accel:
                    vel_diff = math.copysign(max_accel, vel_diff)
                axis.actual_velocity += vel_diff
                
                # Update position
                axis.actual_position += axis.actual_velocity * dt / 1000
                axis.moving = True
                axis.in_position = False
                
                # Torque proportional to acceleration
                axis.actual_torque = abs(vel_diff / max_accel) * 50 + random.uniform(5, 15)
            else:
                axis.actual_velocity = 0
                axis.moving = False
                axis.in_position = True
                axis.actual_torque = random.uniform(2, 8)
                
            # Check limits
            if axis.actual_position >= axis.positive_limit:
                axis.positive_limit_switch = True
                axis.actual_position = axis.positive_limit
            else:
                axis.positive_limit_switch = False
                
            if axis.actual_position <= axis.negative_limit:
                axis.negative_limit_switch = True
                axis.actual_position = axis.negative_limit
            else:
                axis.negative_limit_switch = False
                
            # Temperature simulation
            axis.motor_temp = 45 + axis.actual_torque * 0.3 + random.uniform(-1, 1)
            axis.drive_temp = 40 + axis.actual_torque * 0.2 + random.uniform(-1, 1)
            
        # Spindle simulation
        if self.state.spindle.command_speed > 0:
            speed_error = self.state.spindle.command_speed - self.state.spindle.actual_speed
            ramp_rate = 2000  # RPM/s
            
            if abs(speed_error) > 10:
                self.state.spindle.actual_speed += math.copysign(min(abs(speed_error), ramp_rate * dt), speed_error)
                self.state.spindle.at_speed = False
            else:
                self.state.spindle.actual_speed = noise(self.state.spindle.command_speed, 0.2)
                self.state.spindle.at_speed = True
                
            self.state.spindle.running = True
            self.state.spindle.actual_torque = random.uniform(10, 30)
            self.state.spindle.actual_power = self.state.spindle.actual_speed * self.state.spindle.actual_torque / 10000
        else:
            self.state.spindle.actual_speed = max(0, self.state.spindle.actual_speed - 1000 * dt)
            self.state.spindle.running = self.state.spindle.actual_speed > 10
            self.state.spindle.at_speed = False
            
        # Program simulation
        if self.state.program.running and not self.state.program.paused:
            self.state.program.current_line += 1
            if self.state.program.current_line >= self.state.program.total_lines:
                self.state.program.current_line = 0
                self.state.parts_count += 1
                
            self.state.cycle_time += dt
            
            # Generate random motion commands
            if random.random() < 0.1:
                axis = random.choice(list(self.state.axes.keys()))
                target = random.uniform(
                    self.state.axes[axis].negative_limit * 0.8,
                    self.state.axes[axis].positive_limit * 0.8
                )
                self.state.axes[axis].command_position = target
                
        # Alarms
        self.state.alarms = []
        for axis in self.state.axes.values():
            if axis.motor_temp > 80:
                self.state.alarms.append({
                    "code": 2001,
                    "message": f"{axis.name} motor overtemperature",
                    "severity": "HIGH"
                })
            if axis.state == DriveState.FAULT:
                self.state.alarms.append({
                    "code": 1000 + ord(axis.id),
                    "message": f"{axis.name} drive fault",
                    "severity": "CRITICAL"
                })
                
        self.state.timestamp = time.time()
        
    async def run(self):
        """Main simulation loop"""
        await self.connect()
        self.running = True
        
        # Start program running
        self.state.program.running = True
        
        print(f"[CNC] Starting CNC motion simulation")
        print(f"[CNC] {len(self.state.axes)} axes, {self.state.magazine.capacity} tool magazine")
        
        while self.running:
            loop_start = time.time()
            
            await self.read_commands()
            self.simulate_step(self.simulation_rate / 1000.0)
            await self.publish_state()
            
            elapsed = time.time() - loop_start
            sleep_time = max(0, (self.simulation_rate / 1000.0) - elapsed)
            await asyncio.sleep(sleep_time)


# =============================================================================
# PROFINET SERVER
# =============================================================================

class ProfinetServer:
    """Simplified PROFINET server"""
    
    def __init__(self, simulator: CNCSimulator):
        self.simulator = simulator
        self.port = int(os.getenv("PROFINET_PORT", "34964"))
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle PROFINET client"""
        addr = writer.get_extra_info('peername')
        print(f"[PROFINET] Client connected: {addr}")
        print("[PROFINET] ⚠️ NO AUTHENTICATION - DIRECT DRIVE ACCESS!")
        
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                    
                # Parse PROFINET frame (simplified)
                if len(data) >= 4:
                    frame_id = struct.unpack(">H", data[0:2])[0]
                    
                    if frame_id == ProfinetFrameID.DCP_IDENTIFY:
                        print(f"[PROFINET] DCP Identify from {addr}")
                        # Send identity response
                        response = self._build_dcp_response()
                        writer.write(response)
                        await writer.drain()
                        
                    elif frame_id >= 0x8000:  # RT data
                        print(f"[PROFINET] RT data frame from {addr}")
                        # Process cyclic data
                        await self._process_rt_data(data[2:])
                        
        except Exception as e:
            print(f"[PROFINET] Error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            print(f"[PROFINET] Client disconnected: {addr}")
            
    def _build_dcp_response(self) -> bytes:
        """Build DCP identity response"""
        # Simplified response
        device_name = b"VULNOT-CNC-001"
        return struct.pack(">HH", ProfinetFrameID.DCP_IDENTIFY_RESP, len(device_name)) + device_name
        
    async def _process_rt_data(self, data: bytes):
        """Process PROFINET RT data"""
        # Would parse and apply to simulator
        if len(data) >= 8 and self.simulator.redis:
            # Extract command from data and write to Redis
            pass
            
    async def run(self):
        """Run PROFINET server"""
        server = await asyncio.start_server(
            self.handle_client, '0.0.0.0', self.port
        )
        
        print(f"[PROFINET] Server running on port {self.port}")
        print("[PROFINET] ⚠️ INTENTIONALLY VULNERABLE - NO SECURITY")
        
        async with server:
            await server.serve_forever()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    simulator = CNCSimulator()
    profinet_server = ProfinetServer(simulator)
    
    try:
        await asyncio.gather(
            simulator.run(),
            profinet_server.run()
        )
    except KeyboardInterrupt:
        print("\n[CNC] Shutting down...")
        simulator.running = False


if __name__ == "__main__":
    asyncio.run(main())

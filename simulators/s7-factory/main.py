"""
VULNOT S7comm Manufacturing Factory Simulator
Simulates a Siemens S7-1200/1500 PLC controlling an assembly line

Factory Components:
- Conveyor System (3 zones)
- 2 Pick & Place Robots
- Quality Inspection Station
- Packaging Station
- Production Counters
"""

import asyncio
import json
import os
import time
import random
import struct
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from enum import IntEnum

import redis.asyncio as redis

# S7 protocol implementation
try:
    import snap7
    from snap7.util import set_bool, get_bool, set_int, get_int, set_real, get_real
    HAS_SNAP7 = True
except ImportError:
    HAS_SNAP7 = False
    print("[S7] snap7 not available, using simplified implementation")


# =============================================================================
# FACTORY CONFIGURATION
# =============================================================================

class RobotState(IntEnum):
    IDLE = 0
    PICKING = 1
    PLACING = 2
    MOVING = 3
    ERROR = 4
    MAINTENANCE = 5

class ConveyorState(IntEnum):
    STOPPED = 0
    RUNNING = 1
    FAULT = 2
    
class ProductType(IntEnum):
    NONE = 0
    TYPE_A = 1
    TYPE_B = 2
    TYPE_C = 3


@dataclass
class FactoryState:
    """Complete factory production line state"""
    timestamp: float = field(default_factory=time.time)
    
    # Production Counters
    parts_produced: int = 0
    parts_good: int = 0
    parts_rejected: int = 0
    current_shift: int = 1  # 1, 2, or 3
    shift_target: int = 500
    
    # Conveyor Zone 1 (Infeed)
    conv1_running: bool = True
    conv1_speed: float = 75.0  # %
    conv1_motor_current: float = 12.5  # Amps
    conv1_parts_count: int = 0
    conv1_jam_sensor: bool = False
    
    # Conveyor Zone 2 (Assembly)
    conv2_running: bool = True
    conv2_speed: float = 50.0
    conv2_motor_current: float = 15.2
    conv2_parts_count: int = 0
    conv2_part_present: bool = False
    
    # Conveyor Zone 3 (Outfeed)
    conv3_running: bool = True
    conv3_speed: float = 75.0
    conv3_motor_current: float = 11.8
    conv3_parts_count: int = 0
    
    # Robot 1 (Pick & Place - Zone 1 to Zone 2)
    robot1_state: int = 0  # RobotState enum
    robot1_position_x: float = 0.0  # mm
    robot1_position_y: float = 0.0
    robot1_position_z: float = 500.0
    robot1_gripper_closed: bool = False
    robot1_cycle_time: float = 4.5  # seconds
    robot1_parts_handled: int = 0
    robot1_servo_temp: float = 42.0  # °C
    robot1_error_code: int = 0
    
    # Robot 2 (Pick & Place - Zone 2 to Zone 3)
    robot2_state: int = 0
    robot2_position_x: float = 0.0
    robot2_position_y: float = 0.0
    robot2_position_z: float = 500.0
    robot2_gripper_closed: bool = False
    robot2_cycle_time: float = 4.2
    robot2_parts_handled: int = 0
    robot2_servo_temp: float = 45.0
    robot2_error_code: int = 0
    
    # Quality Inspection Station
    qc_camera_ready: bool = True
    qc_light_on: bool = True
    qc_last_result: int = 1  # 0=fail, 1=pass
    qc_inspection_count: int = 0
    qc_pass_rate: float = 98.5  # %
    
    # Packaging Station
    pkg_box_present: bool = True
    pkg_parts_in_box: int = 0
    pkg_box_capacity: int = 24
    pkg_boxes_completed: int = 0
    pkg_seal_ready: bool = True
    
    # Environmental
    ambient_temp: float = 22.5
    humidity: float = 45.0
    compressed_air_pressure: float = 6.5  # bar
    
    # Safety
    e_stop_pressed: bool = False
    safety_gate_closed: bool = True
    light_curtain_clear: bool = True
    
    # Alarms
    alarms: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# S7 DATA BLOCK MAPPING
# =============================================================================

# DB1 - Production Data (Read/Write)
DB1_MAPPING = {
    0: ("conv1_speed", "REAL", "Conveyor 1 Speed %"),
    4: ("conv2_speed", "REAL", "Conveyor 2 Speed %"),
    8: ("conv3_speed", "REAL", "Conveyor 3 Speed %"),
    12: ("shift_target", "INT", "Shift Target"),
    14: ("current_shift", "INT", "Current Shift"),
    16: ("robot1_cycle_time", "REAL", "Robot 1 Cycle Time"),
    20: ("robot2_cycle_time", "REAL", "Robot 2 Cycle Time"),
}

# DB2 - Production Counters (Read Only)
DB2_MAPPING = {
    0: ("parts_produced", "DINT", "Total Parts Produced"),
    4: ("parts_good", "DINT", "Good Parts"),
    8: ("parts_rejected", "DINT", "Rejected Parts"),
    12: ("robot1_parts_handled", "DINT", "Robot 1 Parts"),
    16: ("robot2_parts_handled", "DINT", "Robot 2 Parts"),
    20: ("pkg_boxes_completed", "INT", "Boxes Completed"),
}

# DB3 - Status Bits
DB3_MAPPING = {
    0: {  # Byte 0
        0: ("conv1_running", "Conveyor 1 Running"),
        1: ("conv2_running", "Conveyor 2 Running"),
        2: ("conv3_running", "Conveyor 3 Running"),
        3: ("conv1_jam_sensor", "Conveyor 1 Jam"),
        4: ("conv2_part_present", "Part at Station 2"),
        5: ("robot1_gripper_closed", "Robot 1 Gripper"),
        6: ("robot2_gripper_closed", "Robot 2 Gripper"),
        7: ("qc_camera_ready", "QC Camera Ready"),
    },
    1: {  # Byte 1
        0: ("e_stop_pressed", "E-Stop"),
        1: ("safety_gate_closed", "Safety Gate"),
        2: ("light_curtain_clear", "Light Curtain"),
        3: ("pkg_box_present", "Box Present"),
        4: ("pkg_seal_ready", "Seal Ready"),
    },
}

# DB4 - Analog Values
DB4_MAPPING = {
    0: ("conv1_motor_current", "REAL", "Conv 1 Current"),
    4: ("conv2_motor_current", "REAL", "Conv 2 Current"),
    8: ("conv3_motor_current", "REAL", "Conv 3 Current"),
    12: ("robot1_servo_temp", "REAL", "Robot 1 Temp"),
    16: ("robot2_servo_temp", "REAL", "Robot 2 Temp"),
    20: ("ambient_temp", "REAL", "Ambient Temp"),
    24: ("compressed_air_pressure", "REAL", "Air Pressure"),
    28: ("qc_pass_rate", "REAL", "QC Pass Rate"),
}


# =============================================================================
# FACTORY SIMULATOR
# =============================================================================

class FactorySimulator:
    """Physics-based manufacturing line simulator"""
    
    def __init__(self):
        self.state = FactoryState()
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self.simulation_rate = int(os.getenv("SIMULATION_RATE", "100"))
        self.plc_rack = int(os.getenv("S7_RACK", "0"))
        self.plc_slot = int(os.getenv("S7_SLOT", "1"))
        
        # Simulation timing
        self.last_part_time = time.time()
        self.robot1_cycle_start = 0
        self.robot2_cycle_start = 0
        
    async def connect(self):
        """Connect to Redis"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        print(f"[Factory] Connected to Redis at {redis_host}:{redis_port}")
        
    async def publish_state(self):
        """Publish state to Redis"""
        if not self.redis:
            return
            
        state_dict = self.state.to_dict()
        state_json = json.dumps(state_dict)
        
        await self.redis.publish("vulnot:factory:state", state_json)
        await self.redis.set("vulnot:factory:current", state_json)
        
        # Publish S7 data blocks for protocol simulator
        # DB1 - Setpoints
        db1_data = {}
        for offset, (attr, dtype, desc) in DB1_MAPPING.items():
            value = getattr(self.state, attr)
            if dtype == "REAL":
                db1_data[str(offset)] = int(value * 100)  # Scale for storage
            else:
                db1_data[str(offset)] = int(value)
        await self.redis.hset("vulnot:s7:db1", mapping=db1_data)
        
        # DB2 - Counters
        db2_data = {}
        for offset, (attr, dtype, desc) in DB2_MAPPING.items():
            db2_data[str(offset)] = int(getattr(self.state, attr))
        await self.redis.hset("vulnot:s7:db2", mapping=db2_data)
        
        # DB4 - Analogs
        db4_data = {}
        for offset, (attr, dtype, desc) in DB4_MAPPING.items():
            db4_data[str(offset)] = int(getattr(self.state, attr) * 100)
        await self.redis.hset("vulnot:s7:db4", mapping=db4_data)
        
    async def read_control_inputs(self):
        """Read control commands from Redis"""
        if not self.redis:
            return
            
        # Read DB1 write commands
        controls = await self.redis.hgetall("vulnot:s7:db1_cmd")
        if controls:
            for offset_str, value in controls.items():
                offset = int(offset_str)
                if offset in DB1_MAPPING:
                    attr, dtype, desc = DB1_MAPPING[offset]
                    if dtype == "REAL":
                        new_val = float(value) / 100
                    else:
                        new_val = int(value)
                    setattr(self.state, attr, new_val)
                    print(f"[Factory] {desc}: {new_val}")
            await self.redis.delete("vulnot:s7:db1_cmd")
            
        # Read bit commands for conveyors/controls
        bit_cmds = await self.redis.hgetall("vulnot:s7:bits_cmd")
        if bit_cmds:
            for key, value in bit_cmds.items():
                if key == "conv1":
                    self.state.conv1_running = value == "1"
                elif key == "conv2":
                    self.state.conv2_running = value == "1"
                elif key == "conv3":
                    self.state.conv3_running = value == "1"
                elif key == "estop":
                    self.state.e_stop_pressed = value == "1"
            await self.redis.delete("vulnot:s7:bits_cmd")
    
    def simulate_step(self, dt: float):
        """Simulate one time step"""
        noise = lambda base, pct=1: base * (1 + random.uniform(-pct/100, pct/100))
        now = time.time()
        
        # Check E-Stop
        if self.state.e_stop_pressed:
            self.state.conv1_running = False
            self.state.conv2_running = False
            self.state.conv3_running = False
            self.state.robot1_state = RobotState.IDLE
            self.state.robot2_state = RobotState.IDLE
            return
            
        # Check safety
        if not self.state.safety_gate_closed or not self.state.light_curtain_clear:
            self.state.robot1_state = RobotState.IDLE
            self.state.robot2_state = RobotState.IDLE
            return
        
        # Conveyor motor currents based on speed and load
        if self.state.conv1_running:
            base_current = 8 + (self.state.conv1_speed / 100) * 8
            self.state.conv1_motor_current = noise(base_current, 5)
        else:
            self.state.conv1_motor_current = 0
            
        if self.state.conv2_running:
            base_current = 10 + (self.state.conv2_speed / 100) * 10
            self.state.conv2_motor_current = noise(base_current, 5)
        else:
            self.state.conv2_motor_current = 0
            
        if self.state.conv3_running:
            base_current = 8 + (self.state.conv3_speed / 100) * 8
            self.state.conv3_motor_current = noise(base_current, 5)
        else:
            self.state.conv3_motor_current = 0
        
        # Part flow simulation
        # New parts arrive based on conveyor 1 speed
        if self.state.conv1_running:
            part_interval = 10 / (self.state.conv1_speed / 100 + 0.1)  # seconds
            if now - self.last_part_time > part_interval:
                self.state.conv1_parts_count += 1
                self.last_part_time = now
                
                # Robot 1 picks part
                if self.state.robot1_state == RobotState.IDLE:
                    self.state.robot1_state = RobotState.PICKING
                    self.robot1_cycle_start = now
        
        # Robot 1 cycle
        if self.state.robot1_state == RobotState.PICKING:
            elapsed = now - self.robot1_cycle_start
            if elapsed < self.state.robot1_cycle_time * 0.3:
                # Moving to pick position
                self.state.robot1_position_z = 500 - (elapsed / (self.state.robot1_cycle_time * 0.3)) * 400
            elif elapsed < self.state.robot1_cycle_time * 0.4:
                # Gripping
                self.state.robot1_gripper_closed = True
                self.state.robot1_position_z = 100
            elif elapsed < self.state.robot1_cycle_time * 0.7:
                # Moving to place
                self.state.robot1_state = RobotState.MOVING
                self.state.robot1_position_x = 500
            elif elapsed < self.state.robot1_cycle_time:
                # Placing
                self.state.robot1_state = RobotState.PLACING
                self.state.robot1_gripper_closed = False
                self.state.conv2_part_present = True
            else:
                # Cycle complete
                self.state.robot1_state = RobotState.IDLE
                self.state.robot1_parts_handled += 1
                self.state.robot1_position_x = 0
                self.state.robot1_position_z = 500
        
        # Robot 2 picks from station 2 after QC
        if self.state.conv2_part_present and self.state.robot2_state == RobotState.IDLE:
            # Simulate QC
            self.state.qc_inspection_count += 1
            passed = random.random() < (self.state.qc_pass_rate / 100)
            self.state.qc_last_result = 1 if passed else 0
            
            if passed:
                self.state.robot2_state = RobotState.PICKING
                self.robot2_cycle_start = now
            else:
                # Reject part
                self.state.parts_rejected += 1
                self.state.conv2_part_present = False
        
        # Robot 2 cycle (simplified)
        if self.state.robot2_state == RobotState.PICKING:
            elapsed = now - self.robot2_cycle_start
            if elapsed >= self.state.robot2_cycle_time:
                self.state.robot2_state = RobotState.IDLE
                self.state.robot2_parts_handled += 1
                self.state.conv2_part_present = False
                
                # Add to packaging
                self.state.pkg_parts_in_box += 1
                self.state.parts_good += 1
                self.state.parts_produced += 1
                
                # Box full?
                if self.state.pkg_parts_in_box >= self.state.pkg_box_capacity:
                    self.state.pkg_boxes_completed += 1
                    self.state.pkg_parts_in_box = 0
        
        # Robot temperatures
        if self.state.robot1_state != RobotState.IDLE:
            self.state.robot1_servo_temp = min(75, self.state.robot1_servo_temp + 0.01)
        else:
            self.state.robot1_servo_temp = max(35, self.state.robot1_servo_temp - 0.005)
            
        if self.state.robot2_state != RobotState.IDLE:
            self.state.robot2_servo_temp = min(75, self.state.robot2_servo_temp + 0.01)
        else:
            self.state.robot2_servo_temp = max(35, self.state.robot2_servo_temp - 0.005)
        
        # Environmental
        self.state.ambient_temp = noise(22.5, 2)
        self.state.humidity = noise(45, 5)
        self.state.compressed_air_pressure = noise(6.5, 3)
        
        # Update QC pass rate (rolling average)
        if self.state.qc_inspection_count > 0:
            self.state.qc_pass_rate = (self.state.parts_good / max(1, self.state.parts_produced)) * 100
        
        # Alarms
        self.state.alarms = []
        
        if self.state.robot1_servo_temp > 65:
            self.state.alarms.append({"level": "MEDIUM", "message": "Robot 1 High Temperature", "tag": "R1-TEMP"})
        if self.state.robot2_servo_temp > 65:
            self.state.alarms.append({"level": "MEDIUM", "message": "Robot 2 High Temperature", "tag": "R2-TEMP"})
        if self.state.compressed_air_pressure < 5.5:
            self.state.alarms.append({"level": "HIGH", "message": "Low Air Pressure", "tag": "AIR-PRESS"})
        if self.state.conv1_jam_sensor:
            self.state.alarms.append({"level": "HIGH", "message": "Conveyor 1 Jam Detected", "tag": "CONV1-JAM"})
        if self.state.parts_produced > 0 and self.state.qc_pass_rate < 95:
            self.state.alarms.append({"level": "MEDIUM", "message": "QC Pass Rate Below Target", "tag": "QC-RATE"})
        if self.state.e_stop_pressed:
            self.state.alarms.append({"level": "HIGH", "message": "Emergency Stop Active", "tag": "E-STOP"})
            
        self.state.timestamp = time.time()
        
    async def run(self):
        """Main simulation loop"""
        await self.connect()
        self.running = True
        
        print(f"[Factory] Starting manufacturing simulation")
        
        while self.running:
            loop_start = time.time()
            
            await self.read_control_inputs()
            self.simulate_step(self.simulation_rate / 1000.0)
            await self.publish_state()
            
            elapsed = time.time() - loop_start
            sleep_time = max(0, (self.simulation_rate / 1000.0) - elapsed)
            await asyncio.sleep(sleep_time)


# =============================================================================
# S7COMM SERVER (Simplified)
# =============================================================================

class SimpleS7Server:
    """Simplified S7comm server for training"""
    
    TPKT_HEADER = b'\x03\x00'
    COTP_CONNECT = 0xE0
    COTP_DATA = 0xF0
    S7_PROTOCOL_ID = 0x32
    
    def __init__(self, simulator: FactorySimulator):
        self.simulator = simulator
        self.port = int(os.getenv("S7_PORT", "102"))
        
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle S7 client connection"""
        addr = writer.get_extra_info('peername')
        print(f"[S7] Client connected from {addr}")
        
        try:
            while True:
                # Read TPKT header (4 bytes)
                tpkt = await reader.read(4)
                if not tpkt or len(tpkt) < 4:
                    break
                    
                # Get length from TPKT
                length = struct.unpack('>H', tpkt[2:4])[0]
                
                # Read rest of packet
                data = await reader.read(length - 4)
                if not data:
                    break
                    
                print(f"[S7] Received {len(data) + 4} bytes")
                
                # Process and respond
                response = await self.process_request(tpkt + data)
                if response:
                    writer.write(response)
                    await writer.drain()
                    
        except Exception as e:
            print(f"[S7] Error: {e}")
        finally:
            print(f"[S7] Client {addr} disconnected")
            writer.close()
            await writer.wait_closed()
            
    async def process_request(self, data: bytes) -> Optional[bytes]:
        """Process S7 request"""
        if len(data) < 7:
            return None
            
        # COTP type is at byte 5
        cotp_type = data[5]
        
        if cotp_type == self.COTP_CONNECT:
            # Connection request - send confirm
            return self.build_connect_confirm()
            
        elif cotp_type == self.COTP_DATA:
            # Data packet - check for S7 protocol
            if len(data) > 10 and data[7] == self.S7_PROTOCOL_ID:
                return await self.process_s7_pdu(data)
                
        return None
        
    def build_connect_confirm(self) -> bytes:
        """Build COTP connection confirm"""
        cotp = bytes([
            0x11,  # Length
            0xD0,  # CC (Connection Confirm)
            0x00, 0x01,  # Dest ref
            0x00, 0x01,  # Src ref
            0x00,  # Class
            0xC0, 0x01, 0x0A,  # TPDU size
            0xC1, 0x02, 0x01, 0x00,  # Src TSAP
            0xC2, 0x02, 0x01, 0x02,  # Dst TSAP
        ])
        
        tpkt = self.TPKT_HEADER + struct.pack('>H', len(cotp) + 4)
        return tpkt + cotp
        
    async def process_s7_pdu(self, data: bytes) -> Optional[bytes]:
        """Process S7 protocol PDU"""
        # S7 header starts at byte 7
        s7_data = data[7:]
        
        if len(s7_data) < 10:
            return None
            
        # PDU type at byte 1 (after protocol ID)
        pdu_type = s7_data[1]
        
        # Function code at byte 7
        func_code = s7_data[7] if len(s7_data) > 7 else 0
        
        if pdu_type == 0x01:  # Job request
            if func_code == 0x04:  # Read
                return await self.handle_read(s7_data)
            elif func_code == 0x05:  # Write
                return await self.handle_write(s7_data)
            elif func_code == 0xF0:  # Setup communication
                return self.handle_setup()
                
        return None
        
    def handle_setup(self) -> bytes:
        """Handle setup communication request"""
        # Build setup response
        s7_response = bytes([
            0x32,  # Protocol ID
            0x03,  # Ack data
            0x00, 0x00,  # Reserved
            0x00, 0x00,  # PDU ref
            0x00, 0x02,  # Param length
            0x00, 0x00,  # Data length
            0x00,  # Error class
            0x00,  # Error code
            0xF0,  # Function
            0x00,  # Reserved
            0x00, 0x01,  # Max AMQ calling
            0x00, 0x01,  # Max AMQ called
            0x01, 0xE0,  # PDU length (480)
        ])
        
        cotp = bytes([0x02, 0xF0, 0x80])  # COTP data header
        tpkt = self.TPKT_HEADER + struct.pack('>H', len(cotp) + len(s7_response) + 4)
        
        return tpkt + cotp + s7_response
        
    async def handle_read(self, s7_data: bytes) -> bytes:
        """Handle read request"""
        # Parse read request to get DB number and offset
        # Simplified - return current values from simulator
        
        state = self.simulator.state
        
        # Build response with some analog values
        data_values = struct.pack('>f', state.conv1_speed)
        data_values += struct.pack('>f', state.conv2_speed)
        data_values += struct.pack('>f', state.robot1_servo_temp)
        data_values += struct.pack('>i', state.parts_produced)
        
        s7_response = bytes([
            0x32,  # Protocol ID
            0x03,  # Ack data
            0x00, 0x00,  # Reserved
            0x00, 0x00,  # PDU ref
            0x00, 0x02,  # Param length
            0x00, len(data_values) + 4,  # Data length
            0x00, 0x00,  # Error
            0x04,  # Read function
            0x01,  # Item count
            0xFF,  # Return code (success)
            0x04,  # Transport size (REAL)
            0x00, len(data_values),  # Length
        ]) + data_values
        
        cotp = bytes([0x02, 0xF0, 0x80])
        tpkt = self.TPKT_HEADER + struct.pack('>H', len(cotp) + len(s7_response) + 4)
        
        return tpkt + cotp + s7_response
        
    async def handle_write(self, s7_data: bytes) -> bytes:
        """Handle write request"""
        print(f"[S7] Write request received")
        
        # Parse write data and apply to simulator
        # Simplified - would need proper parsing in production
        
        if len(s7_data) > 20:
            # Extract value (simplified)
            try:
                value = struct.unpack('>f', s7_data[17:21])[0]
                # Apply to conveyor speed as example
                if self.simulator.redis:
                    await self.simulator.redis.hset(
                        "vulnot:s7:db1_cmd",
                        "0",  # Offset for conv1_speed
                        str(int(value * 100))
                    )
                print(f"[S7] Write value: {value}")
            except:
                pass
        
        # Build success response
        s7_response = bytes([
            0x32, 0x03, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x02, 0x00, 0x01,
            0x00, 0x00,  # No error
            0x05,  # Write function
            0x01,  # Item count
            0xFF,  # Success
        ])
        
        cotp = bytes([0x02, 0xF0, 0x80])
        tpkt = self.TPKT_HEADER + struct.pack('>H', len(cotp) + len(s7_response) + 4)
        
        return tpkt + cotp + s7_response
        
    async def run(self):
        """Start S7 server"""
        server = await asyncio.start_server(
            self.handle_client,
            '0.0.0.0',
            self.port
        )
        
        print(f"[S7] Server listening on port {self.port}")
        print(f"[S7] ⚠️  INTENTIONALLY VULNERABLE - NO AUTHENTICATION")
        
        async with server:
            await server.serve_forever()


# =============================================================================
# MAIN
# =============================================================================

async def main():
    simulator = FactorySimulator()
    s7_server = SimpleS7Server(simulator)
    
    try:
        await asyncio.gather(
            simulator.run(),
            s7_server.run()
        )
    except KeyboardInterrupt:
        print("\n[Factory] Shutting down...")
        simulator.running = False


if __name__ == "__main__":
    asyncio.run(main())

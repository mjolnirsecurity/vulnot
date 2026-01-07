"""
VULNOT Modbus PLC Simulator
Intentionally vulnerable Modbus TCP server for OT security training

Vulnerabilities included:
- No authentication (Modbus has none by default)
- All function codes enabled
- No rate limiting
- Broadcast writes allowed
- Register values directly control process
"""

import asyncio
import os
import struct
from typing import Dict, Optional
import redis.asyncio as redis
from pymodbus.server import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.transaction import ModbusSocketFramer


# =============================================================================
# PLC CONFIGURATION
# =============================================================================

PLC_CONFIGS = {
    1: {  # PLC-INTAKE
        "name": "PLC-INTAKE",
        "description": "Raw Water Intake & Pumping",
        "holding_registers": {
            0: {"name": "Intake Level", "unit": "%", "scale": 100, "tag": "LIT-101"},
            1: {"name": "Raw Water Flow", "unit": "GPM", "scale": 1, "tag": "FIT-101"},
            2: {"name": "Pump P101 Speed", "unit": "%", "scale": 100, "tag": "SIC-101"},
            3: {"name": "Pump P102 Speed", "unit": "%", "scale": 100, "tag": "SIC-102"},
            4: {"name": "Intake Pressure", "unit": "PSI", "scale": 100, "tag": "PIT-101"},
            5: {"name": "Raw Turbidity", "unit": "NTU", "scale": 100, "tag": "AIT-101"},
            6: {"name": "Raw pH", "unit": "pH", "scale": 100, "tag": "AIT-102"},
            7: {"name": "Temperature", "unit": "°C", "scale": 100, "tag": "TIT-101"},
        },
        "coils": {
            0: {"name": "Pump P101 Run", "tag": "HS-101"},
            1: {"name": "Pump P102 Run", "tag": "HS-102"},
            2: {"name": "Intake Valve Open", "tag": "XV-101"},
            3: {"name": "Emergency Stop", "tag": "ES-101"},
        },
        "control_mapping": {
            "COIL0": "pump_p101",
            "COIL1": "pump_p102",
            "HR2": "pump_p101_speed",
            "HR3": "pump_p102_speed",
        }
    },
    2: {  # PLC-TREATMENT
        "name": "PLC-TREATMENT",
        "description": "Water Treatment Process",
        "holding_registers": {
            0: {"name": "Flash Mix Level", "unit": "%", "scale": 100, "tag": "LIT-102"},
            1: {"name": "Floc Basin Level", "unit": "%", "scale": 100, "tag": "LIT-103"},
            2: {"name": "Sed Basin Level", "unit": "%", "scale": 100, "tag": "LIT-104"},
            3: {"name": "Chlorine Contact Level", "unit": "%", "scale": 100, "tag": "LIT-105"},
            4: {"name": "Chlorine Flow", "unit": "GPH", "scale": 100, "tag": "FIT-105"},
            5: {"name": "Alum Flow", "unit": "GPH", "scale": 100, "tag": "FIT-106"},
            6: {"name": "Treated pH", "unit": "pH", "scale": 100, "tag": "AIT-105"},
            7: {"name": "Chlorine Residual", "unit": "mg/L", "scale": 100, "tag": "AIT-106"},
            8: {"name": "Filtered Turbidity", "unit": "NTU", "scale": 1000, "tag": "AIT-104"},
            9: {"name": "Chemical Valve Position", "unit": "%", "scale": 100, "tag": "FCV-105"},
        },
        "coils": {
            0: {"name": "Transfer Pump P201 Run", "tag": "HS-201"},
            1: {"name": "Transfer Pump P202 Run", "tag": "HS-202"},
            2: {"name": "Chlorine Pump Run", "tag": "HS-203"},
            3: {"name": "Alum Pump Run", "tag": "HS-204"},
            4: {"name": "Mixer M101 Run", "tag": "HS-205"},
            5: {"name": "Emergency Stop", "tag": "ES-201"},
        },
        "control_mapping": {
            "HR4": "chlorine_dose",
            "HR5": "alum_dose",
            "HR9": "valve_v105",
        }
    },
    3: {  # PLC-DISTRIBUTION
        "name": "PLC-DISTRIBUTION", 
        "description": "Clearwell & Distribution",
        "holding_registers": {
            0: {"name": "Clearwell Level", "unit": "%", "scale": 100, "tag": "LIT-106"},
            1: {"name": "Distribution Flow", "unit": "GPM", "scale": 1, "tag": "FIT-301"},
            2: {"name": "Distribution Pressure", "unit": "PSI", "scale": 100, "tag": "PIT-301"},
            3: {"name": "Pump P301 Speed", "unit": "%", "scale": 100, "tag": "SIC-301"},
            4: {"name": "Pump P302 Speed", "unit": "%", "scale": 100, "tag": "SIC-302"},
            5: {"name": "Treated Flow", "unit": "GPM", "scale": 1, "tag": "FIT-106"},
            6: {"name": "Filter DP", "unit": "PSI", "scale": 100, "tag": "PDT-104"},
            7: {"name": "Distribution Valve Position", "unit": "%", "scale": 100, "tag": "FCV-301"},
        },
        "coils": {
            0: {"name": "Dist Pump P301 Run", "tag": "HS-301"},
            1: {"name": "Dist Pump P302 Run", "tag": "HS-302"},
            2: {"name": "Distribution Valve Open", "tag": "XV-301"},
            3: {"name": "Backwash Valve Open", "tag": "XV-104"},
            4: {"name": "Emergency Stop", "tag": "ES-301"},
        },
        "control_mapping": {
            "COIL0": "pump_p301",
            "COIL1": "pump_p302",
            "HR3": "pump_p301_speed",
            "HR4": "pump_p302_speed",
            "HR7": "valve_v103",
        }
    }
}


# =============================================================================
# CUSTOM DATA BLOCKS WITH REDIS SYNC
# =============================================================================

class RedisBackedDataBlock(ModbusSequentialDataBlock):
    """Modbus data block backed by Redis for real-time process sync"""
    
    def __init__(self, address: int, values: list, redis_client: redis.Redis, 
                 plc_id: int, block_type: str, config: dict):
        super().__init__(address, values)
        self.redis = redis_client
        self.plc_id = plc_id
        self.block_type = block_type  # 'hr' or 'coil'
        self.config = config
        self.control_mapping = config.get("control_mapping", {})
        
    async def sync_from_redis(self):
        """Pull latest values from Redis (called periodically)"""
        key = f"vulnot:plc:{self.plc_id}:registers"
        try:
            data = await self.redis.hgetall(key)
            if data:
                for k, v in data.items():
                    if self.block_type == 'hr' and k.startswith('HR'):
                        idx = int(k[2:])
                        if 0 <= idx < len(self.values):
                            self.values[idx] = int(v)
                    elif self.block_type == 'coil' and k.startswith('COIL'):
                        idx = int(k[4:])
                        if 0 <= idx < len(self.values):
                            self.values[idx] = int(v)
        except Exception as e:
            print(f"[PLC-{self.plc_id}] Redis sync error: {e}")
            
    async def push_control_to_redis(self, address: int, value: int):
        """Push control changes to Redis for process engine"""
        key = f"vulnot:plc:{self.plc_id}:controls"
        
        if self.block_type == 'hr':
            reg_key = f"HR{address}"
        else:
            reg_key = f"COIL{address}"
            
        if reg_key in self.control_mapping:
            control_name = self.control_mapping[reg_key]
            await self.redis.hset(key, control_name, str(value))
            print(f"[PLC-{self.plc_id}] Control write: {control_name} = {value}")
            
    def setValues(self, address: int, values: list):
        """Override to capture writes and push to Redis"""
        super().setValues(address, values)
        
        # Log the write (this is intentionally verbose for training visibility)
        if self.block_type == 'hr':
            for i, v in enumerate(values):
                reg_info = self.config.get("holding_registers", {}).get(address + i, {})
                tag = reg_info.get("tag", f"HR{address + i}")
                name = reg_info.get("name", "Unknown")
                print(f"[PLC-{self.plc_id}] WRITE HR[{address + i}] ({tag} - {name}) = {v}")
        else:
            for i, v in enumerate(values):
                coil_info = self.config.get("coils", {}).get(address + i, {})
                tag = coil_info.get("tag", f"COIL{address + i}")
                name = coil_info.get("name", "Unknown")
                print(f"[PLC-{self.plc_id}] WRITE COIL[{address + i}] ({tag} - {name}) = {v}")
                
        # Async push to Redis (fire and forget)
        for i, v in enumerate(values):
            asyncio.create_task(self.push_control_to_redis(address + i, v))


# =============================================================================
# PLC SERVER
# =============================================================================

class ModbusPLCServer:
    """Modbus TCP server simulating a PLC"""
    
    def __init__(self):
        self.plc_id = int(os.getenv("PLC_ID", "1"))
        self.plc_name = os.getenv("PLC_NAME", f"PLC-{self.plc_id}")
        self.modbus_port = int(os.getenv("MODBUS_PORT", "502"))
        self.unit_id = int(os.getenv("UNIT_ID", str(self.plc_id)))
        
        self.config = PLC_CONFIGS.get(self.plc_id, PLC_CONFIGS[1])
        
        self.redis: Optional[redis.Redis] = None
        self.server = None
        self.context = None
        self.hr_block = None
        self.coil_block = None
        
    async def connect_redis(self):
        """Connect to Redis"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        print(f"[{self.plc_name}] Connected to Redis at {redis_host}:{redis_port}")
        
    def create_datastore(self):
        """Create Modbus datastore with Redis-backed blocks"""
        # Initialize with zeros, will be populated from Redis
        num_holding_registers = 100
        num_coils = 32
        num_discrete_inputs = 32
        num_input_registers = 100
        
        # Create Redis-backed data blocks
        self.hr_block = RedisBackedDataBlock(
            0, [0] * num_holding_registers,
            self.redis, self.plc_id, 'hr', self.config
        )
        
        self.coil_block = RedisBackedDataBlock(
            0, [0] * num_coils,
            self.redis, self.plc_id, 'coil', self.config
        )
        
        # Standard blocks for discrete inputs and input registers
        di_block = ModbusSequentialDataBlock(0, [0] * num_discrete_inputs)
        ir_block = ModbusSequentialDataBlock(0, [0] * num_input_registers)
        
        # Create slave context
        store = ModbusSlaveContext(
            di=di_block,      # Discrete Inputs (read-only bits)
            co=self.coil_block,  # Coils (read-write bits)
            hr=self.hr_block,    # Holding Registers (read-write words)
            ir=ir_block,      # Input Registers (read-only words)
        )
        
        # Create server context (single slave)
        self.context = ModbusServerContext(slaves={self.unit_id: store}, single=False)
        
        return self.context
        
    async def sync_loop(self):
        """Periodically sync data from Redis"""
        while True:
            try:
                await self.hr_block.sync_from_redis()
                await self.coil_block.sync_from_redis()
            except Exception as e:
                print(f"[{self.plc_name}] Sync error: {e}")
            await asyncio.sleep(0.1)  # 100ms sync rate
            
    async def run(self):
        """Start the Modbus server"""
        await self.connect_redis()

        # Create datastore
        context = self.create_datastore()

        # Device identification (for Modbus device info function code 43)
        identity = ModbusDeviceIdentification()
        identity[0x00] = "VULNOT"  # Vendor Name
        identity[0x01] = self.config["name"]  # Product Code
        identity[0x02] = "1.0.0"  # Major Minor Revision
        identity[0x03] = "https://vulnot.io"  # Vendor URL
        identity[0x04] = self.config["description"]  # Product Name
        identity[0x05] = "Water Treatment PLC"  # Model Name
        identity[0x06] = "VULNOT Training Platform"  # User Application Name

        print(f"[{self.plc_name}] Starting Modbus TCP server on port {self.modbus_port}")
        print(f"[{self.plc_name}] Unit ID: {self.unit_id}")
        print(f"[{self.plc_name}] Description: {self.config['description']}")
        print(f"[{self.plc_name}] Holding Registers: {len(self.config.get('holding_registers', {}))}")
        print(f"[{self.plc_name}] Coils: {len(self.config.get('coils', {}))}")
        print(f"[{self.plc_name}] INTENTIONALLY VULNERABLE - NO AUTHENTICATION")

        # Start sync loop
        asyncio.create_task(self.sync_loop())

        # Start Modbus server
        await StartAsyncTcpServer(
            context=context,
            identity=identity,
            address=("0.0.0.0", self.modbus_port),
            framer=ModbusSocketFramer,
        )


async def main():
    server = ModbusPLCServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

"""
VULNOT Modbus TCP Server
Simulates a vulnerable PLC controlling water treatment equipment
"""

import asyncio
import json
import logging
import os
import signal
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.server import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vulnot.modbus")

redis_client: Optional[redis.Redis] = None


class WaterTreatmentDataStore:
    """Custom data store for water treatment PLC simulation"""
    
    def __init__(self):
        self.holding_registers = ModbusSequentialDataBlock(0, [0] * 100)
        self.input_registers = ModbusSequentialDataBlock(0, [0] * 100)
        self.coils = ModbusSequentialDataBlock(0, [False] * 100)
        self.discrete_inputs = ModbusSequentialDataBlock(0, [False] * 100)
        self._set_initial_values()
        
    def _set_initial_values(self):
        """Set default process values"""
        # Tank levels (scaled 0-10000 = 0-100%)
        self.holding_registers.setValues(1, [7500, 6000, 4500, 8000, 9000, 7000])
        # Pump speeds
        self.holding_registers.setValues(11, [7500, 6000, 0, 8000, 2500])
        # Valve positions  
        self.holding_registers.setValues(21, [10000, 7500, 0, 0])
        # Setpoints (pH x100, chlorine x100, etc.)
        self.holding_registers.setValues(31, [720, 200, 400, 450, 650, 350])
        # Sensor values (input registers)
        self.input_registers.setValues(1, [720, 50, 200, 185, 450, 650])
        # Pump flows
        self.input_registers.setValues(11, [150, 120, 0, 200, 5])
        # Pump run status (coils)
        self.coils.setValues(1, [True, True, False, True, True])
        # Valve open status
        self.coils.setValues(11, [True, True, False, False])
        # System enable and auto mode
        self.coils.setValues(21, [True, True, False, False, False])
        # Pump running discrete inputs
        self.discrete_inputs.setValues(1, [True, True, False, True, True])
        
    def get_context(self) -> ModbusSlaveContext:
        return ModbusSlaveContext(
            di=self.discrete_inputs,
            co=self.coils,
            hr=self.holding_registers,
            ir=self.input_registers
        )


class ModbusServer:
    """VULNOT Modbus TCP Server"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 502, unit_id: int = 1):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.data_store = WaterTreatmentDataStore()
        self.running = False
        
        self.context = ModbusServerContext(
            slaves={unit_id: self.data_store.get_context()},
            single=False
        )
        
        self.identity = ModbusDeviceIdentification()
        self.identity.VendorName = "VULNOT Industries"
        self.identity.ProductCode = "WTP-1000"
        self.identity.ProductName = "Water Treatment PLC"
        self.identity.ModelName = "WTP Controller"
        self.identity.MajorMinorRevision = "1.0.0"
        
    async def start(self):
        self.running = True
        logger.info(f"Starting VULNOT Modbus Server on {self.host}:{self.port}")
        logger.info(f"Unit ID: {self.unit_id}")
        logger.info("WARNING: No authentication enabled (intentionally vulnerable)")
        
        asyncio.create_task(self._redis_sync_loop())
        
        await StartAsyncTcpServer(
            context=self.context,
            identity=self.identity,
            address=(self.host, self.port)
        )
        
    async def _redis_sync_loop(self):
        global redis_client
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        try:
            redis_client = redis.from_url(redis_url)
            await redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            return
            
        while self.running:
            try:
                await self._publish_state()
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Redis sync error: {e}")
                await asyncio.sleep(1)
                
    async def _publish_state(self):
        if not redis_client:
            return
            
        slave = self.context[self.unit_id]
        
        state = {
            "timestamp": datetime.utcnow().isoformat(),
            "tanks": {
                "raw_water": slave.getValues(3, 0, 1)[0] / 100,
                "settling": slave.getValues(3, 1, 1)[0] / 100,
                "filter": slave.getValues(3, 2, 1)[0] / 100,
                "chlorine": slave.getValues(3, 3, 1)[0] / 100,
                "clear_well": slave.getValues(3, 4, 1)[0] / 100,
                "distribution": slave.getValues(3, 5, 1)[0] / 100,
            },
            "sensors": {
                "ph": slave.getValues(4, 0, 1)[0] / 100,
                "turbidity": slave.getValues(4, 1, 1)[0] / 100,
                "chlorine": slave.getValues(4, 2, 1)[0] / 100,
                "temperature": slave.getValues(4, 3, 1)[0] / 10,
                "flow_rate": slave.getValues(4, 4, 1)[0],
                "pressure": slave.getValues(4, 5, 1)[0] / 10,
            },
            "pumps": {
                "intake": {"running": bool(slave.getValues(1, 0, 1)[0]), "speed": slave.getValues(3, 10, 1)[0] / 100},
                "transfer1": {"running": bool(slave.getValues(1, 1, 1)[0]), "speed": slave.getValues(3, 11, 1)[0] / 100},
                "transfer2": {"running": bool(slave.getValues(1, 2, 1)[0]), "speed": slave.getValues(3, 12, 1)[0] / 100},
                "distribution": {"running": bool(slave.getValues(1, 3, 1)[0]), "speed": slave.getValues(3, 13, 1)[0] / 100},
                "chemical": {"running": bool(slave.getValues(1, 4, 1)[0]), "speed": slave.getValues(3, 14, 1)[0] / 100},
            },
            "valves": {
                "inlet": slave.getValues(3, 20, 1)[0] / 100,
                "outlet": slave.getValues(3, 21, 1)[0] / 100,
                "bypass": slave.getValues(3, 22, 1)[0] / 100,
                "drain": slave.getValues(3, 23, 1)[0] / 100,
            }
        }
        
        await redis_client.publish("vulnot:process", json.dumps(state))
        
    def stop(self):
        self.running = False


async def main():
    host = os.getenv("MODBUS_HOST", "0.0.0.0")
    port = int(os.getenv("MODBUS_PORT", "502"))
    unit_id = int(os.getenv("UNIT_ID", "1"))
    
    server = ModbusServer(host=host, port=port, unit_id=unit_id)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    asyncio.run(main())

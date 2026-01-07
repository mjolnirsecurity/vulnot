"""
Water Treatment Process Simulator
Physics-based simulation of water treatment dynamics
"""

import asyncio
import json
import logging
import math
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

import redis.asyncio as redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vulnot.process")


@dataclass
class Tank:
    """Water storage tank model"""
    name: str
    capacity: float  # gallons
    level: float = 50.0  # percentage
    inflow: float = 0.0  # GPM
    outflow: float = 0.0  # GPM
    
    def update(self, dt: float):
        """Update tank level based on flows"""
        net_flow = self.inflow - self.outflow
        volume_change = net_flow * dt / 60  # Convert GPM to gallons
        level_change = (volume_change / self.capacity) * 100
        self.level = max(0, min(100, self.level + level_change))
        return self.level


@dataclass  
class Pump:
    """Pump model"""
    name: str
    running: bool = False
    speed: float = 0.0  # 0-100%
    max_flow: float = 200.0  # GPM
    
    @property
    def flow(self) -> float:
        if not self.running:
            return 0.0
        return self.max_flow * (self.speed / 100)


@dataclass
class Valve:
    """Control valve model"""
    name: str
    position: float = 0.0  # 0-100%
    max_flow: float = 500.0  # GPM
    
    def get_flow(self, upstream_pressure: float) -> float:
        cv = self.position / 100
        return self.max_flow * cv * math.sqrt(upstream_pressure / 100)


@dataclass
class WaterQuality:
    """Water quality parameters"""
    ph: float = 7.0
    turbidity: float = 1.0  # NTU
    chlorine: float = 0.0  # mg/L
    temperature: float = 20.0  # Celsius
    
    def add_chlorine(self, amount: float, volume: float):
        """Add chlorine to water"""
        if volume > 0:
            self.chlorine += amount / volume * 1000
            
    def decay_chlorine(self, dt: float, temp: float):
        """Chlorine decay over time"""
        k = 0.1 * (1 + 0.02 * (temp - 20))  # Temperature-dependent decay
        self.chlorine *= math.exp(-k * dt / 3600)


class WaterTreatmentSimulator:
    """
    Complete water treatment plant simulation
    
    Process Flow:
    Raw Water -> Intake -> Settling -> Filtration -> Chlorination -> Clear Well -> Distribution
    """
    
    def __init__(self):
        # Tanks
        self.tanks = {
            "raw_water": Tank("Raw Water Tank", capacity=10000, level=75),
            "settling": Tank("Settling Tank", capacity=20000, level=60),
            "filter": Tank("Filter Tank", capacity=15000, level=45),
            "chlorine": Tank("Chlorine Contact", capacity=5000, level=80),
            "clear_well": Tank("Clear Well", capacity=50000, level=90),
            "distribution": Tank("Distribution Tank", capacity=100000, level=70),
        }
        
        # Pumps
        self.pumps = {
            "intake": Pump("Intake Pump", running=True, speed=75, max_flow=200),
            "transfer1": Pump("Transfer Pump 1", running=True, speed=60, max_flow=150),
            "transfer2": Pump("Transfer Pump 2", running=False, speed=0, max_flow=150),
            "distribution": Pump("Distribution Pump", running=True, speed=80, max_flow=300),
            "chemical": Pump("Chemical Pump", running=True, speed=25, max_flow=10),
        }
        
        # Valves
        self.valves = {
            "inlet": Valve("Inlet Valve", position=100, max_flow=500),
            "outlet": Valve("Outlet Valve", position=75, max_flow=400),
            "bypass": Valve("Bypass Valve", position=0, max_flow=200),
            "drain": Valve("Drain Valve", position=0, max_flow=100),
        }
        
        # Water quality
        self.quality = WaterQuality(ph=7.2, turbidity=0.5, chlorine=2.0, temperature=18.5)
        
        # Process variables
        self.flow_rate = 450.0  # GPM
        self.pressure = 65.0  # PSI
        
        # Simulation settings
        self.dt = 1.0  # Time step in seconds
        self.speed_multiplier = 1.0
        self.running = False
        
        # Redis connection
        self.redis: Optional[redis.Redis] = None
        
    async def connect_redis(self):
        """Connect to Redis"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis = redis.from_url(redis_url)
            await self.redis.ping()
            logger.info("Process simulator connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            
    async def run(self):
        """Main simulation loop"""
        self.running = True
        await self.connect_redis()
        
        logger.info("Starting Water Treatment Process Simulator")
        logger.info(f"Simulation speed: {self.speed_multiplier}x")
        
        while self.running:
            try:
                # Update process
                self._update_process()
                
                # Add some realistic noise
                self._add_noise()
                
                # Check for alarms
                alarms = self._check_alarms()
                
                # Publish state
                await self._publish_state()
                
                # Publish alarms
                if alarms:
                    await self._publish_alarms(alarms)
                
                # Wait for next cycle
                await asyncio.sleep(self.dt / self.speed_multiplier)
                
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                await asyncio.sleep(1)
                
    def _update_process(self):
        """Update all process elements"""
        # Calculate flows
        intake_flow = self.pumps["intake"].flow
        transfer_flow = self.pumps["transfer1"].flow + self.pumps["transfer2"].flow
        dist_flow = self.pumps["distribution"].flow
        chem_flow = self.pumps["chemical"].flow
        
        # Update tank levels
        self.tanks["raw_water"].inflow = intake_flow * (self.valves["inlet"].position / 100)
        self.tanks["raw_water"].outflow = transfer_flow * 0.5
        self.tanks["raw_water"].update(self.dt)
        
        self.tanks["settling"].inflow = self.tanks["raw_water"].outflow
        self.tanks["settling"].outflow = transfer_flow * 0.5
        self.tanks["settling"].update(self.dt)
        
        self.tanks["filter"].inflow = self.tanks["settling"].outflow
        self.tanks["filter"].outflow = transfer_flow * 0.5
        self.tanks["filter"].update(self.dt)
        
        self.tanks["chlorine"].inflow = self.tanks["filter"].outflow
        self.tanks["chlorine"].outflow = dist_flow * 0.3
        self.tanks["chlorine"].update(self.dt)
        
        self.tanks["clear_well"].inflow = self.tanks["chlorine"].outflow
        self.tanks["clear_well"].outflow = dist_flow * 0.5
        self.tanks["clear_well"].update(self.dt)
        
        self.tanks["distribution"].inflow = self.tanks["clear_well"].outflow
        self.tanks["distribution"].outflow = dist_flow * (self.valves["outlet"].position / 100)
        self.tanks["distribution"].update(self.dt)
        
        # Update water quality
        self.quality.add_chlorine(chem_flow * self.dt / 60, 1000)
        self.quality.decay_chlorine(self.dt, self.quality.temperature)
        
        # Settling reduces turbidity
        if self.tanks["settling"].level > 20:
            self.quality.turbidity *= 0.999
            
        # Update overall flow and pressure
        self.flow_rate = dist_flow * (self.valves["outlet"].position / 100)
        self.pressure = 50 + (self.tanks["distribution"].level / 100) * 30
        
    def _add_noise(self):
        """Add realistic sensor noise"""
        self.quality.ph += random.gauss(0, 0.01)
        self.quality.ph = max(6.0, min(9.0, self.quality.ph))
        
        self.quality.turbidity += random.gauss(0, 0.02)
        self.quality.turbidity = max(0, min(10, self.quality.turbidity))
        
        self.quality.chlorine += random.gauss(0, 0.01)
        self.quality.chlorine = max(0, min(5, self.quality.chlorine))
        
        self.quality.temperature += random.gauss(0, 0.05)
        
        self.flow_rate += random.gauss(0, 2)
        self.pressure += random.gauss(0, 0.5)
        
    def _check_alarms(self) -> list:
        """Check for alarm conditions"""
        alarms = []
        
        # pH alarms
        if self.quality.ph < 6.5:
            alarms.append({"tag": "ph", "type": "low", "value": self.quality.ph, "limit": 6.5, "priority": "high"})
        elif self.quality.ph > 8.5:
            alarms.append({"tag": "ph", "type": "high", "value": self.quality.ph, "limit": 8.5, "priority": "high"})
            
        # Chlorine alarms
        if self.quality.chlorine < 0.2:
            alarms.append({"tag": "chlorine", "type": "low", "value": self.quality.chlorine, "limit": 0.2, "priority": "critical"})
        elif self.quality.chlorine > 4.0:
            alarms.append({"tag": "chlorine", "type": "high", "value": self.quality.chlorine, "limit": 4.0, "priority": "high"})
            
        # Tank level alarms
        for name, tank in self.tanks.items():
            if tank.level < 10:
                alarms.append({"tag": f"{name}_level", "type": "low", "value": tank.level, "limit": 10, "priority": "high"})
            elif tank.level > 95:
                alarms.append({"tag": f"{name}_level", "type": "high", "value": tank.level, "limit": 95, "priority": "medium"})
                
        return alarms
        
    async def _publish_state(self):
        """Publish current state to Redis"""
        if not self.redis:
            return
            
        state = {
            "timestamp": datetime.utcnow().isoformat(),
            "tanks": {name: {"level": t.level, "inflow": t.inflow, "outflow": t.outflow} 
                     for name, t in self.tanks.items()},
            "pumps": {name: {"running": p.running, "speed": p.speed, "flow": p.flow} 
                     for name, p in self.pumps.items()},
            "valves": {name: {"position": v.position} for name, v in self.valves.items()},
            "quality": {
                "ph": round(self.quality.ph, 2),
                "turbidity": round(self.quality.turbidity, 2),
                "chlorine": round(self.quality.chlorine, 2),
                "temperature": round(self.quality.temperature, 1),
            },
            "process": {
                "flow_rate": round(self.flow_rate, 1),
                "pressure": round(self.pressure, 1),
            }
        }
        
        await self.redis.publish("vulnot:process", json.dumps(state))
        
    async def _publish_alarms(self, alarms: list):
        """Publish alarms to Redis"""
        if not self.redis:
            return
            
        for alarm in alarms:
            alarm["timestamp"] = datetime.utcnow().isoformat()
            alarm["id"] = f"ALM-{hash(alarm['tag'] + alarm['type']) % 10000:04d}"
            await self.redis.publish("vulnot:alarms", json.dumps(alarm))
            
    def stop(self):
        self.running = False


async def main():
    simulator = WaterTreatmentSimulator()
    
    try:
        await simulator.run()
    except KeyboardInterrupt:
        simulator.stop()


if __name__ == "__main__":
    asyncio.run(main())

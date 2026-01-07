"""
VULNOT Water Treatment Process Simulation Engine
Simulates a complete water treatment plant with realistic physics

Process Flow:
1. Raw Water Intake → Intake Basin (T-101)
2. Coagulation/Flocculation → Flash Mix Tank (T-102) + Floc Basin (T-103)
3. Sedimentation → Sedimentation Basin (T-104)
4. Filtration → Filter Units (F-101, F-102)
5. Disinfection → Chlorine Contact Tank (T-105)
6. Storage → Clearwell (T-106)
7. Distribution → Distribution Pumps (P-301, P-302)
"""

import asyncio
import json
import os
import time
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional
from datetime import datetime

import redis.asyncio as redis
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import ASYNCHRONOUS


# =============================================================================
# PROCESS CONFIGURATION
# =============================================================================

@dataclass
class TankConfig:
    name: str
    capacity: float  # gallons
    min_level: float = 0.0
    max_level: float = 100.0
    initial_level: float = 50.0

@dataclass
class PumpConfig:
    name: str
    max_flow: float  # GPM
    initial_state: bool = False

@dataclass
class ProcessConfig:
    """Water treatment plant configuration"""
    # Tanks
    intake_basin: TankConfig = field(default_factory=lambda: TankConfig("T-101 Intake Basin", 500000, initial_level=60))
    flash_mix: TankConfig = field(default_factory=lambda: TankConfig("T-102 Flash Mix", 50000, initial_level=45))
    floc_basin: TankConfig = field(default_factory=lambda: TankConfig("T-103 Flocculation", 200000, initial_level=55))
    sed_basin: TankConfig = field(default_factory=lambda: TankConfig("T-104 Sedimentation", 500000, initial_level=70))
    chlorine_contact: TankConfig = field(default_factory=lambda: TankConfig("T-105 Chlorine Contact", 100000, initial_level=65))
    clearwell: TankConfig = field(default_factory=lambda: TankConfig("T-106 Clearwell", 1000000, initial_level=75))
    
    # Flow rates (GPM)
    raw_water_flow: float = 2000.0
    treatment_flow: float = 1800.0
    distribution_demand: float = 1500.0


# =============================================================================
# PROCESS STATE
# =============================================================================

@dataclass
class ProcessState:
    """Real-time process state"""
    timestamp: float = field(default_factory=time.time)
    
    # Tank Levels (%)
    intake_level: float = 60.0
    flash_mix_level: float = 45.0
    floc_level: float = 55.0
    sed_level: float = 70.0
    chlorine_contact_level: float = 65.0
    clearwell_level: float = 75.0
    
    # Pump States (bool) and Speeds (%)
    pump_p101_running: bool = True   # Raw water pump 1
    pump_p101_speed: float = 75.0
    pump_p102_running: bool = False  # Raw water pump 2 (backup)
    pump_p102_speed: float = 0.0
    pump_p201_running: bool = True   # High service pump 1
    pump_p201_speed: float = 80.0
    pump_p202_running: bool = True   # High service pump 2
    pump_p202_speed: float = 80.0
    pump_p301_running: bool = True   # Distribution pump 1
    pump_p301_speed: float = 70.0
    pump_p302_running: bool = False  # Distribution pump 2
    pump_p302_speed: float = 0.0
    
    # Valve Positions (% open)
    valve_v101: float = 100.0  # Intake valve
    valve_v102: float = 75.0   # Treatment inlet
    valve_v103: float = 80.0   # Distribution outlet
    valve_v104: float = 0.0    # Bypass valve
    valve_v105: float = 50.0   # Chemical injection
    
    # Chemical Dosing
    chlorine_dose: float = 2.5      # mg/L target
    chlorine_flow: float = 15.0     # GPH actual
    alum_dose: float = 25.0         # mg/L target
    alum_flow: float = 8.0          # GPH actual
    fluoride_dose: float = 0.7      # mg/L target
    fluoride_flow: float = 3.0      # GPH actual
    
    # Water Quality Parameters
    raw_turbidity: float = 12.5     # NTU
    filtered_turbidity: float = 0.15 # NTU
    ph_raw: float = 7.2
    ph_treated: float = 7.4
    chlorine_residual: float = 1.8  # mg/L
    temperature: float = 18.5       # °C
    conductivity: float = 450.0     # µS/cm
    
    # Flow Rates (GPM)
    raw_water_flow: float = 1850.0
    treated_flow: float = 1750.0
    distribution_flow: float = 1650.0
    backwash_flow: float = 0.0
    
    # Pressures (PSI)
    intake_pressure: float = 25.0
    filter_inlet_pressure: float = 18.0
    filter_outlet_pressure: float = 12.0
    distribution_pressure: float = 65.0
    
    # Filter Status
    filter_1_status: str = "ONLINE"
    filter_1_runtime: float = 18.5   # hours since backwash
    filter_2_status: str = "ONLINE"
    filter_2_runtime: float = 12.3
    filter_dp: float = 4.5           # Differential pressure
    
    # Alarms
    alarms: list = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)


# =============================================================================
# SIMULATION ENGINE
# =============================================================================

class WaterTreatmentSimulator:
    """Physics-based water treatment plant simulator"""
    
    def __init__(self):
        self.state = ProcessState()
        self.config = ProcessConfig()
        self.redis: Optional[redis.Redis] = None
        self.influx_client: Optional[InfluxDBClient] = None
        self.influx_write_api = None
        self.running = False
        self.simulation_rate = int(os.getenv("SIMULATION_RATE", "100"))  # ms
        
    async def connect(self):
        """Connect to Redis and InfluxDB"""
        # Redis connection
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # InfluxDB connection
        influx_url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        influx_token = os.getenv("INFLUXDB_TOKEN", "vulnot-super-secret-token")
        influx_org = os.getenv("INFLUXDB_ORG", "mjolnir")
        
        self.influx_client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
        self.influx_write_api = self.influx_client.write_api(write_options=ASYNCHRONOUS)
        
        print(f"[ProcessEngine] Connected to Redis at {redis_host}:{redis_port}")
        print(f"[ProcessEngine] Connected to InfluxDB at {influx_url}")
        
    async def disconnect(self):
        """Disconnect from services"""
        if self.redis:
            await self.redis.close()
        if self.influx_client:
            self.influx_client.close()
            
    async def publish_state(self):
        """Publish current state to Redis"""
        if not self.redis:
            return
            
        state_dict = self.state.to_dict()
        state_json = json.dumps(state_dict)
        
        # Publish to channel for real-time subscribers
        await self.redis.publish("vulnot:process:state", state_json)
        
        # Store current state for new subscribers
        await self.redis.set("vulnot:process:current", state_json)
        
        # Store individual values for Modbus PLCs to read
        await self.redis.hset("vulnot:plc:1:registers", mapping={
            "HR0": int(self.state.intake_level * 100),      # Intake level (scaled)
            "HR1": int(self.state.raw_water_flow),          # Raw water flow
            "HR2": int(self.state.pump_p101_speed * 100),   # Pump 1 speed
            "HR3": int(self.state.pump_p102_speed * 100),   # Pump 2 speed
            "HR4": int(self.state.intake_pressure * 100),   # Intake pressure
            "HR5": int(self.state.raw_turbidity * 100),     # Raw turbidity
            "HR6": int(self.state.ph_raw * 100),            # Raw pH
            "HR7": int(self.state.temperature * 100),       # Temperature
            "COIL0": 1 if self.state.pump_p101_running else 0,
            "COIL1": 1 if self.state.pump_p102_running else 0,
        })
        
        await self.redis.hset("vulnot:plc:2:registers", mapping={
            "HR0": int(self.state.flash_mix_level * 100),
            "HR1": int(self.state.floc_level * 100),
            "HR2": int(self.state.sed_level * 100),
            "HR3": int(self.state.chlorine_contact_level * 100),
            "HR4": int(self.state.chlorine_flow * 100),
            "HR5": int(self.state.alum_flow * 100),
            "HR6": int(self.state.ph_treated * 100),
            "HR7": int(self.state.chlorine_residual * 100),
            "HR8": int(self.state.filtered_turbidity * 1000),
            "HR9": int(self.state.valve_v105 * 100),
            "COIL0": 1 if self.state.pump_p201_running else 0,
            "COIL1": 1 if self.state.pump_p202_running else 0,
        })
        
        await self.redis.hset("vulnot:plc:3:registers", mapping={
            "HR0": int(self.state.clearwell_level * 100),
            "HR1": int(self.state.distribution_flow),
            "HR2": int(self.state.distribution_pressure * 100),
            "HR3": int(self.state.pump_p301_speed * 100),
            "HR4": int(self.state.pump_p302_speed * 100),
            "HR5": int(self.state.treated_flow),
            "HR6": int(self.state.filter_dp * 100),
            "HR7": int(self.state.valve_v103 * 100),
            "COIL0": 1 if self.state.pump_p301_running else 0,
            "COIL1": 1 if self.state.pump_p302_running else 0,
        })
        
    async def write_to_historian(self):
        """Write process data to InfluxDB historian"""
        if not self.influx_write_api:
            return
            
        bucket = os.getenv("INFLUXDB_BUCKET", "process_data")
        
        points = [
            Point("tank_level").tag("tank", "intake").field("value", self.state.intake_level),
            Point("tank_level").tag("tank", "flash_mix").field("value", self.state.flash_mix_level),
            Point("tank_level").tag("tank", "floc").field("value", self.state.floc_level),
            Point("tank_level").tag("tank", "sed").field("value", self.state.sed_level),
            Point("tank_level").tag("tank", "chlorine_contact").field("value", self.state.chlorine_contact_level),
            Point("tank_level").tag("tank", "clearwell").field("value", self.state.clearwell_level),
            
            Point("flow_rate").tag("location", "raw_water").field("value", self.state.raw_water_flow),
            Point("flow_rate").tag("location", "treated").field("value", self.state.treated_flow),
            Point("flow_rate").tag("location", "distribution").field("value", self.state.distribution_flow),
            
            Point("water_quality").tag("parameter", "ph_raw").field("value", self.state.ph_raw),
            Point("water_quality").tag("parameter", "ph_treated").field("value", self.state.ph_treated),
            Point("water_quality").tag("parameter", "turbidity_raw").field("value", self.state.raw_turbidity),
            Point("water_quality").tag("parameter", "turbidity_filtered").field("value", self.state.filtered_turbidity),
            Point("water_quality").tag("parameter", "chlorine_residual").field("value", self.state.chlorine_residual),
            
            Point("pressure").tag("location", "intake").field("value", self.state.intake_pressure),
            Point("pressure").tag("location", "distribution").field("value", self.state.distribution_pressure),
            
            Point("pump_status").tag("pump", "P101").field("running", self.state.pump_p101_running).field("speed", self.state.pump_p101_speed),
            Point("pump_status").tag("pump", "P201").field("running", self.state.pump_p201_running).field("speed", self.state.pump_p201_speed),
            Point("pump_status").tag("pump", "P301").field("running", self.state.pump_p301_running).field("speed", self.state.pump_p301_speed),
        ]
        
        self.influx_write_api.write(bucket=bucket, record=points)
        
    async def read_control_inputs(self):
        """Read control inputs from Redis (set by Modbus writes)"""
        if not self.redis:
            return
            
        # Check for control inputs from PLC 1
        plc1_controls = await self.redis.hgetall("vulnot:plc:1:controls")
        if plc1_controls:
            if "pump_p101" in plc1_controls:
                self.state.pump_p101_running = plc1_controls["pump_p101"] == "1"
            if "pump_p102" in plc1_controls:
                self.state.pump_p102_running = plc1_controls["pump_p102"] == "1"
            if "pump_p101_speed" in plc1_controls:
                self.state.pump_p101_speed = float(plc1_controls["pump_p101_speed"])
                
        # Check for control inputs from PLC 2
        plc2_controls = await self.redis.hgetall("vulnot:plc:2:controls")
        if plc2_controls:
            if "chlorine_dose" in plc2_controls:
                self.state.chlorine_dose = float(plc2_controls["chlorine_dose"])
            if "alum_dose" in plc2_controls:
                self.state.alum_dose = float(plc2_controls["alum_dose"])
            if "valve_v105" in plc2_controls:
                self.state.valve_v105 = float(plc2_controls["valve_v105"])
                
        # Check for control inputs from PLC 3
        plc3_controls = await self.redis.hgetall("vulnot:plc:3:controls")
        if plc3_controls:
            if "pump_p301" in plc3_controls:
                self.state.pump_p301_running = plc3_controls["pump_p301"] == "1"
            if "pump_p302" in plc3_controls:
                self.state.pump_p302_running = plc3_controls["pump_p302"] == "1"
            if "pump_p301_speed" in plc3_controls:
                self.state.pump_p301_speed = float(plc3_controls["pump_p301_speed"])
                
    def simulate_step(self, dt: float):
        """
        Simulate one time step of the process
        dt: time step in seconds
        """
        # Add some realistic noise to measurements
        noise = lambda base, pct=0.5: base * (1 + random.uniform(-pct/100, pct/100))
        
        # =================================================================
        # CALCULATE FLOWS
        # =================================================================
        
        # Raw water flow based on pump states and speeds
        raw_flow = 0.0
        if self.state.pump_p101_running:
            raw_flow += 1200 * (self.state.pump_p101_speed / 100)
        if self.state.pump_p102_running:
            raw_flow += 1200 * (self.state.pump_p102_speed / 100)
        raw_flow *= (self.state.valve_v101 / 100)
        self.state.raw_water_flow = noise(raw_flow, 1.0)
        
        # Distribution flow based on pumps and demand
        dist_flow = 0.0
        if self.state.pump_p301_running:
            dist_flow += 1000 * (self.state.pump_p301_speed / 100)
        if self.state.pump_p302_running:
            dist_flow += 1000 * (self.state.pump_p302_speed / 100)
        dist_flow *= (self.state.valve_v103 / 100)
        # Add demand variation (time of day simulation)
        demand_factor = 0.8 + 0.4 * abs(math.sin(time.time() / 3600))  # Varies 0.8-1.2
        self.state.distribution_flow = noise(min(dist_flow, self.config.distribution_demand * demand_factor), 2.0)
        
        # Treatment flow (limited by filter capacity)
        self.state.treated_flow = noise(min(self.state.raw_water_flow * 0.95, 2000), 1.0)
        
        # =================================================================
        # TANK LEVEL DYNAMICS
        # =================================================================
        
        # Intake Basin: fills from raw water, drains to flash mix
        intake_in = self.state.raw_water_flow * dt / 60  # gallons
        intake_out = self.state.treated_flow * 0.3 * dt / 60
        self.state.intake_level += (intake_in - intake_out) / 5000  # Scale to %
        self.state.intake_level = max(0, min(100, self.state.intake_level))
        
        # Flash Mix Tank
        flash_in = intake_out
        flash_out = flash_in * 0.98
        self.state.flash_mix_level += (flash_in - flash_out) / 500
        self.state.flash_mix_level = max(0, min(100, noise(self.state.flash_mix_level, 0.5)))
        
        # Flocculation Basin
        floc_in = flash_out
        floc_out = floc_in * 0.97
        self.state.floc_level += (floc_in - floc_out) / 2000
        self.state.floc_level = max(0, min(100, noise(self.state.floc_level, 0.3)))
        
        # Sedimentation Basin
        sed_in = floc_out
        sed_out = sed_in * 0.95
        self.state.sed_level += (sed_in - sed_out) / 5000
        self.state.sed_level = max(0, min(100, noise(self.state.sed_level, 0.2)))
        
        # Chlorine Contact Tank
        contact_in = sed_out
        contact_out = contact_in * 0.99
        self.state.chlorine_contact_level += (contact_in - contact_out) / 1000
        self.state.chlorine_contact_level = max(0, min(100, noise(self.state.chlorine_contact_level, 0.5)))
        
        # Clearwell
        clearwell_in = contact_out
        clearwell_out = self.state.distribution_flow * dt / 60
        self.state.clearwell_level += (clearwell_in - clearwell_out) / 10000
        self.state.clearwell_level = max(0, min(100, noise(self.state.clearwell_level, 0.3)))
        
        # =================================================================
        # WATER QUALITY SIMULATION
        # =================================================================
        
        # Raw water turbidity varies naturally
        self.state.raw_turbidity = noise(12 + 5 * math.sin(time.time() / 7200), 5)
        
        # Filtered turbidity depends on filter runtime and raw turbidity
        filter_efficiency = 0.99 - (self.state.filter_1_runtime / 100)  # Degrades over time
        self.state.filtered_turbidity = noise(self.state.raw_turbidity * (1 - filter_efficiency), 10)
        self.state.filtered_turbidity = max(0.05, min(1.0, self.state.filtered_turbidity))
        
        # pH changes with chemical dosing
        self.state.ph_raw = noise(7.2, 1)
        ph_adjustment = (self.state.alum_dose - 25) * 0.01  # Alum affects pH
        self.state.ph_treated = noise(self.state.ph_raw + ph_adjustment + 0.2, 0.5)
        
        # Chlorine residual depends on dose and contact time
        chlorine_decay = 0.1 * (self.state.chlorine_contact_level / 100)
        self.state.chlorine_residual = noise(self.state.chlorine_dose - chlorine_decay, 3)
        self.state.chlorine_residual = max(0.2, min(4.0, self.state.chlorine_residual))
        
        # Chemical flows track setpoints with some lag
        self.state.chlorine_flow += (self.state.chlorine_dose * 6 - self.state.chlorine_flow) * 0.1
        self.state.alum_flow += (self.state.alum_dose * 0.32 - self.state.alum_flow) * 0.1
        
        # Temperature varies slowly
        self.state.temperature = noise(18.5 + 2 * math.sin(time.time() / 86400), 0.5)
        
        # =================================================================
        # PRESSURES
        # =================================================================
        
        self.state.intake_pressure = noise(25 + (self.state.intake_level - 50) * 0.1, 2)
        self.state.filter_inlet_pressure = noise(18 - self.state.filter_dp * 0.5, 2)
        self.state.filter_outlet_pressure = noise(12, 2)
        
        # Distribution pressure depends on pump output and demand
        base_pressure = 45 + (self.state.pump_p301_speed + self.state.pump_p302_speed) * 0.2
        demand_drop = (self.state.distribution_flow / 2000) * 15
        self.state.distribution_pressure = noise(base_pressure - demand_drop, 1)
        
        # Filter differential pressure increases with runtime
        self.state.filter_dp = 2.0 + self.state.filter_1_runtime * 0.15
        self.state.filter_1_runtime += dt / 3600  # hours
        self.state.filter_2_runtime += dt / 3600
        
        # =================================================================
        # ALARMS
        # =================================================================
        
        self.state.alarms = []
        
        if self.state.clearwell_level < 20:
            self.state.alarms.append({"level": "HIGH", "message": "Clearwell level critically low", "tag": "LIT-106"})
        elif self.state.clearwell_level < 35:
            self.state.alarms.append({"level": "MEDIUM", "message": "Clearwell level low", "tag": "LIT-106"})
            
        if self.state.clearwell_level > 95:
            self.state.alarms.append({"level": "HIGH", "message": "Clearwell level critically high", "tag": "LIT-106"})
            
        if self.state.chlorine_residual < 0.5:
            self.state.alarms.append({"level": "HIGH", "message": "Chlorine residual below minimum", "tag": "AIT-105"})
            
        if self.state.chlorine_residual > 3.5:
            self.state.alarms.append({"level": "MEDIUM", "message": "Chlorine residual high", "tag": "AIT-105"})
            
        if self.state.filtered_turbidity > 0.5:
            self.state.alarms.append({"level": "HIGH", "message": "Filtered turbidity exceeds limit", "tag": "AIT-104"})
            
        if self.state.filter_dp > 8:
            self.state.alarms.append({"level": "MEDIUM", "message": "Filter differential pressure high - backwash needed", "tag": "PDT-104"})
            
        if self.state.distribution_pressure < 40:
            self.state.alarms.append({"level": "HIGH", "message": "Distribution pressure low", "tag": "PIT-301"})
            
        if self.state.distribution_pressure > 85:
            self.state.alarms.append({"level": "MEDIUM", "message": "Distribution pressure high", "tag": "PIT-301"})
            
        self.state.timestamp = time.time()
        
    async def run(self):
        """Main simulation loop"""
        await self.connect()
        self.running = True
        
        print(f"[ProcessEngine] Starting simulation at {self.simulation_rate}ms rate")
        
        last_historian_write = time.time()
        
        while self.running:
            loop_start = time.time()
            
            # Read control inputs from Modbus writes
            await self.read_control_inputs()
            
            # Simulate one step
            dt = self.simulation_rate / 1000.0
            self.simulate_step(dt)
            
            # Publish state to Redis
            await self.publish_state()
            
            # Write to historian every 5 seconds
            if time.time() - last_historian_write >= 5:
                await self.write_to_historian()
                last_historian_write = time.time()
            
            # Maintain consistent loop rate
            elapsed = time.time() - loop_start
            sleep_time = max(0, (self.simulation_rate / 1000.0) - elapsed)
            await asyncio.sleep(sleep_time)
            
        await self.disconnect()
        
    def stop(self):
        """Stop the simulation"""
        self.running = False


import math

async def main():
    simulator = WaterTreatmentSimulator()
    
    try:
        await simulator.run()
    except KeyboardInterrupt:
        print("\n[ProcessEngine] Shutting down...")
        simulator.stop()
    except Exception as e:
        print(f"[ProcessEngine] Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

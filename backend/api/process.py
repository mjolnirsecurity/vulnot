"""Process Data API Routes"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ProcessValue(BaseModel):
    tag: str
    value: float
    unit: str
    timestamp: datetime
    quality: str = "good"

class SetpointCommand(BaseModel):
    tag: str
    value: float

# In-memory process state (in production, this comes from Redis/simulator)
process_state = {
    "tanks": {
        "raw_water_tank": {"level": 75.0, "capacity": 1000, "unit": "gallons"},
        "settling_tank": {"level": 60.0, "capacity": 2000, "unit": "gallons"},
        "filter_tank": {"level": 45.0, "capacity": 1500, "unit": "gallons"},
        "chlorine_tank": {"level": 80.0, "capacity": 500, "unit": "gallons"},
        "clear_well": {"level": 90.0, "capacity": 5000, "unit": "gallons"},
        "distribution_tank": {"level": 70.0, "capacity": 10000, "unit": "gallons"},
    },
    "pumps": {
        "intake_pump": {"running": True, "speed": 75.0, "flow": 150.0},
        "transfer_pump_1": {"running": True, "speed": 60.0, "flow": 120.0},
        "transfer_pump_2": {"running": False, "speed": 0.0, "flow": 0.0},
        "distribution_pump": {"running": True, "speed": 80.0, "flow": 200.0},
        "chemical_pump": {"running": True, "speed": 25.0, "flow": 5.0},
    },
    "valves": {
        "inlet_valve": {"position": 100.0, "status": "open"},
        "outlet_valve": {"position": 75.0, "status": "throttled"},
        "bypass_valve": {"position": 0.0, "status": "closed"},
        "drain_valve": {"position": 0.0, "status": "closed"},
    },
    "sensors": {
        "ph": {"value": 7.2, "unit": "pH", "min": 6.5, "max": 8.5},
        "turbidity": {"value": 0.5, "unit": "NTU", "min": 0, "max": 4.0},
        "chlorine": {"value": 2.0, "unit": "mg/L", "min": 0.2, "max": 4.0},
        "temperature": {"value": 18.5, "unit": "°C", "min": 0, "max": 35},
        "flow_rate": {"value": 450.0, "unit": "GPM", "min": 0, "max": 1000},
        "pressure": {"value": 65.0, "unit": "PSI", "min": 0, "max": 150},
    }
}

@router.get("/state")
async def get_process_state() -> Dict:
    """Get complete process state"""
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "data": process_state
    }

@router.get("/tanks")
async def get_tanks() -> Dict:
    """Get all tank levels"""
    return process_state["tanks"]

@router.get("/tanks/{tank_id}")
async def get_tank(tank_id: str) -> Dict:
    """Get specific tank data"""
    if tank_id not in process_state["tanks"]:
        raise HTTPException(status_code=404, detail=f"Tank {tank_id} not found")
    return process_state["tanks"][tank_id]

@router.get("/pumps")
async def get_pumps() -> Dict:
    """Get all pump status"""
    return process_state["pumps"]

@router.post("/pumps/{pump_id}/start")
async def start_pump(pump_id: str) -> Dict:
    """Start a pump"""
    if pump_id not in process_state["pumps"]:
        raise HTTPException(status_code=404, detail=f"Pump {pump_id} not found")
    process_state["pumps"][pump_id]["running"] = True
    return {"status": "started", "pump": pump_id}

@router.post("/pumps/{pump_id}/stop")
async def stop_pump(pump_id: str) -> Dict:
    """Stop a pump"""
    if pump_id not in process_state["pumps"]:
        raise HTTPException(status_code=404, detail=f"Pump {pump_id} not found")
    process_state["pumps"][pump_id]["running"] = False
    process_state["pumps"][pump_id]["speed"] = 0.0
    process_state["pumps"][pump_id]["flow"] = 0.0
    return {"status": "stopped", "pump": pump_id}

@router.get("/sensors")
async def get_sensors() -> Dict:
    """Get all sensor readings"""
    return process_state["sensors"]

@router.get("/valves")
async def get_valves() -> Dict:
    """Get all valve positions"""
    return process_state["valves"]

@router.post("/valves/{valve_id}/set")
async def set_valve(valve_id: str, position: float) -> Dict:
    """Set valve position (0-100%)"""
    if valve_id not in process_state["valves"]:
        raise HTTPException(status_code=404, detail=f"Valve {valve_id} not found")
    if not 0 <= position <= 100:
        raise HTTPException(status_code=400, detail="Position must be 0-100")
    process_state["valves"][valve_id]["position"] = position
    if position == 0:
        process_state["valves"][valve_id]["status"] = "closed"
    elif position == 100:
        process_state["valves"][valve_id]["status"] = "open"
    else:
        process_state["valves"][valve_id]["status"] = "throttled"
    return {"status": "set", "valve": valve_id, "position": position}

@router.get("/trends/{tag}")
async def get_trend_data(tag: str, hours: int = 1) -> Dict:
    """Get historical trend data for a tag"""
    # In production, this would query InfluxDB
    return {
        "tag": tag,
        "hours": hours,
        "data": [],
        "message": "Historical data from InfluxDB"
    }

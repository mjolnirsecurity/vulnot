"""System Status API Routes"""
from fastapi import APIRouter
from typing import Dict
from datetime import datetime

router = APIRouter()

@router.get("/status")
async def get_system_status() -> Dict:
    """Get overall system status"""
    return {
        "status": "running",
        "scenario": "water_treatment",
        "uptime": "2h 34m",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "modbus_simulator": "running",
            "process_simulator": "running",
            "historian": "connected",
            "redis": "connected"
        }
    }

@router.get("/scenarios")
async def get_available_scenarios() -> Dict:
    """Get list of available training scenarios"""
    return {
        "scenarios": [
            {
                "id": "water_treatment",
                "name": "Water Treatment Facility",
                "description": "Municipal water treatment plant with Modbus PLCs",
                "difficulty": "beginner",
                "protocols": ["modbus_tcp"],
                "status": "active"
            }
        ]
    }

@router.post("/scenarios/{scenario_id}/reset")
async def reset_scenario(scenario_id: str) -> Dict:
    """Reset a scenario to initial state"""
    return {
        "status": "reset",
        "scenario": scenario_id,
        "message": "Scenario reset to initial state"
    }

@router.get("/connections")
async def get_connections() -> Dict:
    """Get active connections info"""
    return {
        "websocket_clients": 0,
        "modbus_connections": 0
    }

"""Alarm Management API Routes"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

router = APIRouter()

class AlarmPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlarmState(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    CLEARED = "cleared"

class Alarm(BaseModel):
    id: str
    timestamp: datetime
    priority: AlarmPriority
    state: AlarmState
    tag: str
    message: str
    value: Optional[float] = None
    limit: Optional[float] = None

# Active alarms (in production, this would be in Redis)
active_alarms: List[Dict] = [
    {
        "id": "ALM-001",
        "timestamp": datetime.utcnow().isoformat(),
        "priority": "high",
        "state": "active",
        "tag": "chlorine",
        "message": "Chlorine level approaching high limit",
        "value": 3.8,
        "limit": 4.0
    },
    {
        "id": "ALM-002",
        "timestamp": datetime.utcnow().isoformat(),
        "priority": "medium",
        "state": "active",
        "tag": "distribution_tank",
        "message": "Distribution tank level low",
        "value": 25.0,
        "limit": 30.0
    }
]

alarm_history: List[Dict] = []

@router.get("/active")
async def get_active_alarms() -> List[Dict]:
    """Get all active alarms"""
    return active_alarms

@router.get("/history")
async def get_alarm_history(limit: int = 100) -> List[Dict]:
    """Get alarm history"""
    return alarm_history[-limit:]

@router.post("/{alarm_id}/acknowledge")
async def acknowledge_alarm(alarm_id: str) -> Dict:
    """Acknowledge an alarm"""
    for alarm in active_alarms:
        if alarm["id"] == alarm_id:
            alarm["state"] = "acknowledged"
            alarm["ack_time"] = datetime.utcnow().isoformat()
            return {"status": "acknowledged", "alarm_id": alarm_id}
    raise HTTPException(status_code=404, detail=f"Alarm {alarm_id} not found")

@router.post("/{alarm_id}/clear")
async def clear_alarm(alarm_id: str) -> Dict:
    """Clear an alarm"""
    for i, alarm in enumerate(active_alarms):
        if alarm["id"] == alarm_id:
            alarm["state"] = "cleared"
            alarm["clear_time"] = datetime.utcnow().isoformat()
            alarm_history.append(active_alarms.pop(i))
            return {"status": "cleared", "alarm_id": alarm_id}
    raise HTTPException(status_code=404, detail=f"Alarm {alarm_id} not found")

@router.get("/summary")
async def get_alarm_summary() -> Dict:
    """Get alarm summary by priority"""
    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for alarm in active_alarms:
        priority = alarm.get("priority", "info")
        summary[priority] = summary.get(priority, 0) + 1
    return {
        "total_active": len(active_alarms),
        "by_priority": summary
    }

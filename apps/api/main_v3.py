"""
VULNOT API - Phase 3
Complete API for all 6 OT scenarios
"""

import asyncio
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as redis

app = FastAPI(
    title="VULNOT API",
    description="OT Security Training Platform API",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_client: Optional[redis.Redis] = None

SCENARIOS = {
    "water": {
        "name": "Water Treatment",
        "protocol": "Modbus TCP",
        "network": "10.0.1.0/24",
        "port": 502,
        "redis_channel": "vulnot:water:state",
        "redis_key": "vulnot:water:current"
    },
    "power": {
        "name": "Power Grid",
        "protocol": "DNP3",
        "network": "10.0.2.0/24",
        "port": 20000,
        "redis_channel": "vulnot:substation:state",
        "redis_key": "vulnot:substation:current"
    },
    "factory": {
        "name": "Manufacturing",
        "protocol": "S7comm",
        "network": "10.0.3.0/24",
        "port": 102,
        "redis_channel": "vulnot:factory:state",
        "redis_key": "vulnot:factory:current"
    },
    "reactor": {
        "name": "Chemical Reactor",
        "protocol": "OPC UA",
        "network": "10.0.4.0/24",
        "port": 4840,
        "redis_channel": "vulnot:reactor:state",
        "redis_key": "vulnot:reactor:current"
    },
    "building": {
        "name": "Building Automation",
        "protocol": "BACnet/IP",
        "network": "10.0.5.0/24",
        "port": 47808,
        "redis_channel": "vulnot:building:state",
        "redis_key": "vulnot:building:current"
    },
    "packaging": {
        "name": "Packaging Line",
        "protocol": "EtherNet/IP",
        "network": "10.0.6.0/24",
        "port": 44818,
        "redis_channel": "vulnot:packaging:state",
        "redis_key": "vulnot:packaging:current"
    }
}


# =============================================================================
# WebSocket Manager
# =============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            scenario: [] for scenario in SCENARIOS
        }
        self.active_connections["ids"] = []
    
    async def connect(self, websocket: WebSocket, scenario: str):
        await websocket.accept()
        if scenario not in self.active_connections:
            self.active_connections[scenario] = []
        self.active_connections[scenario].append(websocket)
    
    def disconnect(self, websocket: WebSocket, scenario: str):
        if scenario in self.active_connections:
            if websocket in self.active_connections[scenario]:
                self.active_connections[scenario].remove(websocket)
    
    async def broadcast(self, message: str, scenario: str):
        if scenario in self.active_connections:
            for connection in self.active_connections[scenario]:
                try:
                    await connection.send_text(message)
                except:
                    pass


manager = ConnectionManager()


# =============================================================================
# Startup/Shutdown
# =============================================================================

@app.on_event("startup")
async def startup():
    global redis_client
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    
    # Start Redis subscribers for each scenario
    for scenario, config in SCENARIOS.items():
        asyncio.create_task(redis_subscriber(scenario, config["redis_channel"]))
    
    # IDS alerts subscriber
    asyncio.create_task(ids_subscriber())


async def redis_subscriber(scenario: str, channel: str):
    """Subscribe to Redis channel and broadcast to WebSocket clients"""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            await manager.broadcast(message["data"], scenario)


async def ids_subscriber():
    """Subscribe to IDS alerts"""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("vulnot:ids:alerts")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            await manager.broadcast(message["data"], "ids")


@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()


# =============================================================================
# WebSocket Endpoints
# =============================================================================

@app.websocket("/ws/{scenario}")
async def websocket_endpoint(websocket: WebSocket, scenario: str):
    if scenario not in SCENARIOS and scenario != "ids":
        await websocket.close(code=4004)
        return
    
    await manager.connect(websocket, scenario)
    try:
        # Send current state immediately
        if scenario in SCENARIOS:
            current = await redis_client.get(SCENARIOS[scenario]["redis_key"])
            if current:
                await websocket.send_text(current)
        
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, scenario)


# Legacy WebSocket endpoints for compatibility
@app.websocket("/ws/process")
async def ws_process(websocket: WebSocket):
    await websocket_endpoint(websocket, "water")

@app.websocket("/ws/substation")
async def ws_substation(websocket: WebSocket):
    await websocket_endpoint(websocket, "power")

@app.websocket("/ws/factory")
async def ws_factory(websocket: WebSocket):
    await websocket_endpoint(websocket, "factory")

@app.websocket("/ws/reactor")
async def ws_reactor(websocket: WebSocket):
    await websocket_endpoint(websocket, "reactor")

@app.websocket("/ws/building")
async def ws_building(websocket: WebSocket):
    await websocket_endpoint(websocket, "building")

@app.websocket("/ws/packaging")
async def ws_packaging(websocket: WebSocket):
    await websocket_endpoint(websocket, "packaging")

@app.websocket("/ws/ids")
async def ws_ids(websocket: WebSocket):
    await websocket_endpoint(websocket, "ids")


# =============================================================================
# REST Endpoints
# =============================================================================

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "0.3.0"}


@app.get("/api/scenarios")
async def list_scenarios():
    """List all available scenarios"""
    return {
        "scenarios": [
            {
                "id": scenario_id,
                **config,
                "dashboard": f"/{scenario_id}" if scenario_id != "water" else "/"
            }
            for scenario_id, config in SCENARIOS.items()
        ]
    }


@app.get("/api/{scenario}/current")
async def get_current_state(scenario: str):
    """Get current state for a scenario"""
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    state = await redis_client.get(SCENARIOS[scenario]["redis_key"])
    if state:
        return json.loads(state)
    return {"error": "No data available"}


@app.get("/api/alarms/{scenario}")
async def get_alarms(scenario: str):
    """Get active alarms for a scenario"""
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    state = await redis_client.get(SCENARIOS[scenario]["redis_key"])
    if state:
        data = json.loads(state)
        return {"alarms": data.get("alarms", [])}
    return {"alarms": []}


# =============================================================================
# IDS Endpoints
# =============================================================================

@app.get("/api/ids/alerts")
async def get_ids_alerts(limit: int = 100):
    """Get recent IDS alerts"""
    alerts = await redis_client.lrange("vulnot:ids:alert_history", 0, limit - 1)
    return {"alerts": [json.loads(a) for a in alerts]}


@app.get("/api/ids/stats")
async def get_ids_stats():
    """Get IDS statistics"""
    stats = await redis_client.hgetall("vulnot:ids:stats")
    return {"stats": stats}


@app.get("/api/ids/rules")
async def get_ids_rules():
    """Get IDS detection rules"""
    # Would normally fetch from IDS engine
    return {
        "rules": [
            {"id": "MODBUS-001", "name": "Unauthorized Modbus Write", "severity": "HIGH", "enabled": True},
            {"id": "DNP3-002", "name": "DNP3 Cold Restart", "severity": "CRITICAL", "enabled": True},
            {"id": "S7-001", "name": "S7 CPU Stop", "severity": "CRITICAL", "enabled": True},
            {"id": "OPCUA-001", "name": "OPC UA Anonymous Access", "severity": "MEDIUM", "enabled": True},
            {"id": "BACNET-002", "name": "BACnet Device Comm Control", "severity": "CRITICAL", "enabled": True},
            {"id": "ENIP-001", "name": "EtherNet/IP Reset", "severity": "CRITICAL", "enabled": True},
        ]
    }


# =============================================================================
# Training Endpoints
# =============================================================================

@app.get("/api/training/modules")
async def get_training_modules():
    """Get training modules"""
    return {
        "modules": [
            {
                "id": 1,
                "name": "OT Fundamentals",
                "labs": [
                    {"id": "lab-01", "name": "Introduction to OT Networks", "difficulty": "beginner"},
                    {"id": "lab-02", "name": "Modbus Protocol Basics", "difficulty": "beginner"},
                ]
            },
            {
                "id": 2,
                "name": "Protocol Attacks",
                "labs": [
                    {"id": "lab-03", "name": "DNP3 Substation Attack", "difficulty": "intermediate"},
                    {"id": "lab-04", "name": "S7comm Manufacturing Attack", "difficulty": "advanced"},
                    {"id": "lab-05", "name": "OPC UA Industrial Attack", "difficulty": "advanced"},
                    {"id": "lab-06", "name": "BACnet Building Attack", "difficulty": "intermediate"},
                ]
            },
            {
                "id": 3,
                "name": "Defense & Detection",
                "labs": [
                    {"id": "lab-07", "name": "OT Network Monitoring", "difficulty": "intermediate"},
                    {"id": "lab-08", "name": "IDS Rule Creation", "difficulty": "advanced"},
                ]
            }
        ]
    }


class FlagSubmission(BaseModel):
    flag: str


@app.post("/api/training/flag/{flag_id}")
async def submit_flag(flag_id: str, submission: FlagSubmission):
    """Submit a training flag"""
    valid_flags = {
        "modbus_scan_complete": 10,
        "modbus_read": 15,
        "modbus_attack": 25,
        "dnp3_scan_complete": 10,
        "breaker_tripped": 20,
        "blackout": 30,
        "s7_scan_complete": 10,
        "production_halt": 25,
        "cpu_stop": 30,
        "opcua_scan_complete": 10,
        "opcua_manipulation": 25,
        "opcua_estop": 30,
        "bacnet_scan_complete": 10,
        "bacnet_hvac_attack": 20,
        "bacnet_device_attack": 25,
    }
    
    if flag_id in valid_flags:
        points = valid_flags[flag_id]
        await redis_client.hincrby("vulnot:training:scores", "total", points)
        await redis_client.sadd("vulnot:training:captured", flag_id)
        return {"success": True, "points": points, "flag": flag_id}
    
    return {"success": False, "error": "Invalid flag"}


@app.get("/api/training/progress")
async def get_training_progress():
    """Get training progress"""
    captured = await redis_client.smembers("vulnot:training:captured")
    total_score = await redis_client.hget("vulnot:training:scores", "total")
    
    return {
        "captured_flags": list(captured) if captured else [],
        "total_score": int(total_score) if total_score else 0,
        "max_score": 280
    }


# =============================================================================
# Control Endpoints
# =============================================================================

class ControlCommand(BaseModel):
    command: str
    value: Optional[str] = None
    target: Optional[str] = None


@app.post("/api/{scenario}/control")
async def send_control(scenario: str, cmd: ControlCommand):
    """Send control command to a scenario"""
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Publish control command to Redis
    cmd_channel = f"vulnot:{scenario}:cmd"
    await redis_client.publish(cmd_channel, json.dumps({
        "command": cmd.command,
        "value": cmd.value,
        "target": cmd.target,
        "timestamp": datetime.now().isoformat()
    }))
    
    return {"status": "sent", "command": cmd.command}


@app.post("/api/{scenario}/reset")
async def reset_scenario(scenario: str):
    """Reset a scenario to initial state"""
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    await redis_client.publish(f"vulnot:{scenario}:cmd", json.dumps({
        "command": "reset",
        "timestamp": datetime.now().isoformat()
    }))
    
    return {"status": "reset", "scenario": scenario}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

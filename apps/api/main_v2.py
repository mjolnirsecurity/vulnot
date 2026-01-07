"""
VULNOT API Server - Phase 2
Multi-scenario support for Water, Power Grid, and Manufacturing

WebSocket endpoints for real-time data:
- /ws/process - Water treatment (legacy)
- /ws/substation - Power grid DNP3
- /ws/factory - Manufacturing S7
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as redis

# =============================================================================
# CONFIGURATION
# =============================================================================

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Scenario configurations
SCENARIOS = {
    "water": {
        "name": "Water Treatment Plant",
        "protocol": "Modbus TCP",
        "redis_channel": "vulnot:process:state",
        "redis_key": "vulnot:process:current",
        "description": "Municipal water treatment facility with 3 PLCs",
        "targets": [
            {"name": "PLC-INTAKE", "ip": "10.0.1.10", "port": 502},
            {"name": "PLC-TREATMENT", "ip": "10.0.1.11", "port": 502},
            {"name": "PLC-DISTRIBUTION", "ip": "10.0.1.12", "port": 502},
        ]
    },
    "power": {
        "name": "Power Grid Substation",
        "protocol": "DNP3",
        "redis_channel": "vulnot:substation:state",
        "redis_key": "vulnot:substation:current",
        "description": "138kV/13.8kV distribution substation with DNP3 RTUs",
        "targets": [
            {"name": "Substation-1", "ip": "10.0.2.10", "port": 20000},
            {"name": "Substation-2", "ip": "10.0.2.11", "port": 20001},
        ]
    },
    "factory": {
        "name": "Manufacturing Line",
        "protocol": "S7comm",
        "redis_channel": "vulnot:factory:state",
        "redis_key": "vulnot:factory:current",
        "description": "Automated assembly line with S7-1500 PLCs",
        "targets": [
            {"name": "Line-1 PLC", "ip": "10.0.3.10", "port": 102},
            {"name": "Line-2 PLC", "ip": "10.0.3.11", "port": 102},
        ]
    }
}

# =============================================================================
# MODELS
# =============================================================================

class ControlCommand(BaseModel):
    scenario: str
    target: str
    command_type: str  # 'coil', 'register', 'binary_output', 'analog_output'
    address: int
    value: int

class AlarmAcknowledge(BaseModel):
    scenario: str
    alarm_ids: List[str]

class ScenarioInfo(BaseModel):
    id: str
    name: str
    protocol: str
    description: str
    targets: List[dict]
    status: str

# =============================================================================
# CONNECTION MANAGER
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections per scenario"""
    
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {
            "water": set(),
            "power": set(),
            "factory": set(),
        }
        
    async def connect(self, scenario: str, websocket: WebSocket):
        await websocket.accept()
        if scenario in self.connections:
            self.connections[scenario].add(websocket)
            
    def disconnect(self, scenario: str, websocket: WebSocket):
        if scenario in self.connections:
            self.connections[scenario].discard(websocket)
            
    async def broadcast(self, scenario: str, message: str):
        if scenario not in self.connections:
            return
            
        dead_connections = set()
        for connection in self.connections[scenario]:
            try:
                await connection.send_text(message)
            except:
                dead_connections.add(connection)
                
        # Clean up dead connections
        for conn in dead_connections:
            self.connections[scenario].discard(conn)


manager = ConnectionManager()
redis_client: Optional[redis.Redis] = None

# =============================================================================
# LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    
    # Startup
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    print(f"[API] Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    
    # Start Redis subscribers for each scenario
    tasks = []
    for scenario_id, scenario in SCENARIOS.items():
        task = asyncio.create_task(
            redis_subscriber(scenario_id, scenario["redis_channel"])
        )
        tasks.append(task)
    
    yield
    
    # Shutdown
    for task in tasks:
        task.cancel()
    if redis_client:
        await redis_client.close()


async def redis_subscriber(scenario: str, channel: str):
    """Subscribe to Redis channel and broadcast to WebSocket clients"""
    global redis_client
    
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)
    
    print(f"[API] Subscribed to {channel} for {scenario}")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await manager.broadcast(scenario, message["data"])
    except asyncio.CancelledError:
        await pubsub.unsubscribe(channel)
        await pubsub.close()

# =============================================================================
# APP
# =============================================================================

app = FastAPI(
    title="VULNOT API",
    description="OT Security Training Platform API - Phase 2",
    version="0.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@app.websocket("/ws/process")
async def websocket_process(websocket: WebSocket):
    """Legacy endpoint for water treatment"""
    await manager.connect("water", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect("water", websocket)


@app.websocket("/ws/substation")
async def websocket_substation(websocket: WebSocket):
    """Power grid substation data"""
    await manager.connect("power", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect("power", websocket)


@app.websocket("/ws/factory")
async def websocket_factory(websocket: WebSocket):
    """Manufacturing factory data"""
    await manager.connect("factory", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect("factory", websocket)


@app.websocket("/ws/{scenario}")
async def websocket_generic(websocket: WebSocket, scenario: str):
    """Generic WebSocket endpoint for any scenario"""
    if scenario not in SCENARIOS:
        await websocket.close(code=4004)
        return
        
    await manager.connect(scenario, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(scenario, websocket)

# =============================================================================
# REST ENDPOINTS - SCENARIOS
# =============================================================================

@app.get("/api/scenarios", response_model=List[ScenarioInfo])
async def list_scenarios():
    """List all available scenarios"""
    result = []
    for scenario_id, config in SCENARIOS.items():
        # Check if scenario is running by looking for recent data
        status = "offline"
        if redis_client:
            try:
                data = await redis_client.get(config["redis_key"])
                if data:
                    state = json.loads(data)
                    # Check if timestamp is recent (within last 5 seconds)
                    import time
                    if time.time() - state.get("timestamp", 0) < 5:
                        status = "online"
            except:
                pass
                
        result.append(ScenarioInfo(
            id=scenario_id,
            name=config["name"],
            protocol=config["protocol"],
            description=config["description"],
            targets=config["targets"],
            status=status
        ))
    return result


@app.get("/api/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get scenario details"""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return SCENARIOS[scenario_id]

# =============================================================================
# REST ENDPOINTS - PROCESS DATA
# =============================================================================

@app.get("/api/{scenario}/current")
async def get_current_state(scenario: str):
    """Get current state for a scenario"""
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
        
    data = await redis_client.get(SCENARIOS[scenario]["redis_key"])
    if not data:
        raise HTTPException(status_code=404, detail="No data available")
        
    return json.loads(data)


@app.get("/api/{scenario}/alarms")
async def get_alarms(scenario: str):
    """Get active alarms for a scenario"""
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
        
    data = await redis_client.get(SCENARIOS[scenario]["redis_key"])
    if not data:
        return {"alarms": []}
        
    state = json.loads(data)
    return {"alarms": state.get("alarms", [])}


@app.post("/api/{scenario}/control")
async def send_control(scenario: str, command: ControlCommand):
    """Send control command to a scenario"""
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    # Route command based on scenario
    if scenario == "water":
        # Modbus command via Redis
        cmd_key = f"vulnot:modbus:{command.target}:cmd"
        await redis_client.hset(cmd_key, str(command.address), str(command.value))
        
    elif scenario == "power":
        # DNP3 command
        address = 10 if "1" in command.target else 11
        if command.command_type == "binary_output":
            cmd_key = f"vulnot:dnp3:{address}:bo_cmd"
        else:
            cmd_key = f"vulnot:dnp3:{address}:ao_cmd"
        await redis_client.hset(cmd_key, str(command.address), str(command.value))
        
    elif scenario == "factory":
        # S7 command
        if command.command_type == "register":
            await redis_client.hset("vulnot:s7:db1_cmd", str(command.address), str(command.value))
        else:
            await redis_client.hset("vulnot:s7:bits_cmd", command.target, str(command.value))
    
    return {"status": "ok", "message": "Command sent"}


@app.post("/api/{scenario}/reset")
async def reset_scenario(scenario: str):
    """Reset scenario to initial state"""
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    # Publish reset command
    await redis_client.publish(f"vulnot:{scenario}:control", json.dumps({"command": "reset"}))
    
    return {"status": "ok", "message": f"Reset command sent to {scenario}"}

# =============================================================================
# REST ENDPOINTS - TRAINING
# =============================================================================

@app.get("/api/training/modules")
async def list_training_modules():
    """List available training modules"""
    return {
        "modules": [
            {
                "id": "modbus-basics",
                "name": "Modbus Protocol Fundamentals",
                "scenario": "water",
                "difficulty": "beginner",
                "duration": "30 min"
            },
            {
                "id": "modbus-exploitation",
                "name": "Modbus Exploitation Techniques",
                "scenario": "water",
                "difficulty": "intermediate",
                "duration": "45 min"
            },
            {
                "id": "dnp3-basics",
                "name": "DNP3 Protocol Fundamentals",
                "scenario": "power",
                "difficulty": "beginner",
                "duration": "30 min"
            },
            {
                "id": "dnp3-attacks",
                "name": "DNP3 Attack Scenarios",
                "scenario": "power",
                "difficulty": "intermediate",
                "duration": "45 min"
            },
            {
                "id": "s7-basics",
                "name": "S7comm Protocol Fundamentals",
                "scenario": "factory",
                "difficulty": "beginner",
                "duration": "30 min"
            },
            {
                "id": "s7-exploitation",
                "name": "S7 PLC Exploitation",
                "scenario": "factory",
                "difficulty": "intermediate",
                "duration": "45 min"
            },
        ]
    }

# =============================================================================
# HEALTH CHECK
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_ok = False
    if redis_client:
        try:
            await redis_client.ping()
            redis_ok = True
        except:
            pass
            
    return {
        "status": "healthy" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
        "scenarios": list(SCENARIOS.keys()),
        "version": "0.2.0"
    }


@app.get("/")
async def root():
    """API root"""
    return {
        "name": "VULNOT API",
        "version": "0.2.0",
        "docs": "/docs",
        "scenarios": list(SCENARIOS.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

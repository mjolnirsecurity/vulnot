"""
VULNOT API Server
FastAPI backend with WebSocket support for real-time dashboard updates
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from influxdb_client import InfluxDBClient
from pydantic import BaseModel


# =============================================================================
# CONFIGURATION
# =============================================================================

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "vulnot-super-secret-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "mjolnir")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "process_data")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")


# =============================================================================
# MODELS
# =============================================================================

class ProcessState(BaseModel):
    timestamp: float
    intake_level: float
    flash_mix_level: float
    floc_level: float
    sed_level: float
    chlorine_contact_level: float
    clearwell_level: float
    pump_p101_running: bool
    pump_p101_speed: float
    pump_p102_running: bool
    pump_p102_speed: float
    pump_p201_running: bool
    pump_p201_speed: float
    pump_p202_running: bool
    pump_p202_speed: float
    pump_p301_running: bool
    pump_p301_speed: float
    pump_p302_running: bool
    pump_p302_speed: float
    valve_v101: float
    valve_v102: float
    valve_v103: float
    valve_v104: float
    valve_v105: float
    chlorine_dose: float
    chlorine_flow: float
    alum_dose: float
    alum_flow: float
    fluoride_dose: float
    fluoride_flow: float
    raw_turbidity: float
    filtered_turbidity: float
    ph_raw: float
    ph_treated: float
    chlorine_residual: float
    temperature: float
    conductivity: float
    raw_water_flow: float
    treated_flow: float
    distribution_flow: float
    backwash_flow: float
    intake_pressure: float
    filter_inlet_pressure: float
    filter_outlet_pressure: float
    distribution_pressure: float
    filter_1_status: str
    filter_1_runtime: float
    filter_2_status: str
    filter_2_runtime: float
    filter_dp: float
    alarms: List[Dict[str, str]]

class ControlCommand(BaseModel):
    plc_id: int
    control_name: str
    value: Any

class AlarmAcknowledge(BaseModel):
    alarm_id: str
    acknowledged_by: str = "operator"


# =============================================================================
# CONNECTION MANAGERS
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WebSocket] Client connected. Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"[WebSocket] Client disconnected. Total: {len(self.active_connections)}")
        
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)


manager = ConnectionManager()
redis_client: Optional[redis.Redis] = None
influx_client: Optional[InfluxDBClient] = None


# =============================================================================
# LIFECYCLE
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global redis_client, influx_client
    
    # Startup
    print("[API] Starting up...")
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    
    # Start Redis subscriber for broadcasting
    asyncio.create_task(redis_subscriber())
    
    print(f"[API] Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    print(f"[API] Connected to InfluxDB at {INFLUXDB_URL}")
    
    yield
    
    # Shutdown
    print("[API] Shutting down...")
    if redis_client:
        await redis_client.close()
    if influx_client:
        influx_client.close()


async def redis_subscriber():
    """Subscribe to Redis channel and broadcast to WebSocket clients"""
    global redis_client
    
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("vulnot:process:state")
    
    print("[API] Subscribed to Redis channel: vulnot:process:state")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            # Broadcast to all WebSocket clients
            await manager.broadcast(message["data"])


# =============================================================================
# APPLICATION
# =============================================================================

app = FastAPI(
    title="VULNOT API",
    description="API for VULNOT OT Security Training Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HEALTH ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "VULNOT API",
        "version": "0.1.0",
        "description": "OT Security Training Platform API",
        "docs": "/docs",
        "websocket": "/ws/process",
    }


# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@app.websocket("/ws/process")
async def websocket_process(websocket: WebSocket):
    """WebSocket endpoint for real-time process data"""
    await manager.connect(websocket)
    
    try:
        # Send current state immediately on connect
        current_state = await redis_client.get("vulnot:process:current")
        if current_state:
            await websocket.send_text(current_state)
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (ping/pong, commands)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client commands
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif message.get("type") == "command":
                        # Process control commands
                        await handle_control_command(message.get("payload", {}))
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(json.dumps({"type": "ping"}))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def handle_control_command(payload: dict):
    """Handle control command from WebSocket client"""
    plc_id = payload.get("plc_id")
    control_name = payload.get("control_name")
    value = payload.get("value")
    
    if plc_id and control_name and value is not None:
        key = f"vulnot:plc:{plc_id}:controls"
        await redis_client.hset(key, control_name, str(value))
        print(f"[API] Control command: PLC {plc_id}, {control_name} = {value}")


# =============================================================================
# REST ENDPOINTS
# =============================================================================

@app.get("/api/process/current", response_model=Dict[str, Any])
async def get_current_state():
    """Get current process state"""
    state = await redis_client.get("vulnot:process:current")
    if state:
        return json.loads(state)
    raise HTTPException(status_code=503, detail="Process state not available")


@app.get("/api/process/plc/{plc_id}")
async def get_plc_registers(plc_id: int):
    """Get current PLC register values"""
    registers = await redis_client.hgetall(f"vulnot:plc:{plc_id}:registers")
    if registers:
        return {"plc_id": plc_id, "registers": registers}
    raise HTTPException(status_code=404, detail=f"PLC {plc_id} not found")


@app.post("/api/process/control")
async def send_control_command(command: ControlCommand):
    """Send control command to PLC"""
    key = f"vulnot:plc:{command.plc_id}:controls"
    await redis_client.hset(key, command.control_name, str(command.value))
    
    return {
        "status": "success",
        "message": f"Control command sent: {command.control_name} = {command.value}",
        "plc_id": command.plc_id,
    }


@app.get("/api/alarms")
async def get_alarms():
    """Get current active alarms"""
    state = await redis_client.get("vulnot:process:current")
    if state:
        data = json.loads(state)
        return {"alarms": data.get("alarms", [])}
    return {"alarms": []}


@app.post("/api/alarms/acknowledge")
async def acknowledge_alarm(ack: AlarmAcknowledge):
    """Acknowledge an alarm"""
    # In a real system, this would update alarm state
    return {
        "status": "acknowledged",
        "alarm_id": ack.alarm_id,
        "acknowledged_by": ack.acknowledged_by,
        "timestamp": datetime.utcnow().isoformat(),
    }


# =============================================================================
# HISTORICAL DATA ENDPOINTS
# =============================================================================

@app.get("/api/history/trends")
async def get_trend_data(
    measurement: str = Query(..., description="Measurement name (e.g., tank_level, flow_rate)"),
    tag_key: str = Query(None, description="Tag key to filter by"),
    tag_value: str = Query(None, description="Tag value to filter by"),
    start: str = Query("-1h", description="Start time (e.g., -1h, -24h, -7d)"),
    stop: str = Query("now()", description="Stop time"),
):
    """Get historical trend data from InfluxDB"""
    query_api = influx_client.query_api()
    
    # Build Flux query
    tag_filter = ""
    if tag_key and tag_value:
        tag_filter = f'|> filter(fn: (r) => r["{tag_key}"] == "{tag_value}")'
    
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: {start}, stop: {stop})
        |> filter(fn: (r) => r["_measurement"] == "{measurement}")
        {tag_filter}
        |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
        |> yield(name: "mean")
    '''
    
    try:
        tables = query_api.query(query)
        
        # Convert to JSON-serializable format
        results = []
        for table in tables:
            for record in table.records:
                results.append({
                    "time": record.get_time().isoformat(),
                    "value": record.get_value(),
                    "field": record.get_field(),
                    "measurement": record.get_measurement(),
                    "tags": {k: v for k, v in record.values.items() 
                            if k not in ["_time", "_value", "_field", "_measurement", "result", "table", "_start", "_stop"]},
                })
        
        return {"data": results, "count": len(results)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")


@app.get("/api/history/summary")
async def get_process_summary(
    hours: int = Query(24, description="Hours of data to summarize"),
):
    """Get process summary statistics"""
    query_api = influx_client.query_api()
    
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -{hours}h)
        |> filter(fn: (r) => r["_measurement"] == "tank_level" or r["_measurement"] == "flow_rate" or r["_measurement"] == "water_quality")
        |> group(columns: ["_measurement", "_field"])
        |> aggregateWindow(every: {hours}h, fn: mean, createEmpty: false)
    '''
    
    try:
        tables = query_api.query(query)
        
        summary = {}
        for table in tables:
            for record in table.records:
                key = f"{record.get_measurement()}_{record.values.get('parameter', record.values.get('tank', record.values.get('location', 'unknown')))}"
                summary[key] = {
                    "value": record.get_value(),
                    "measurement": record.get_measurement(),
                }
        
        return {"summary": summary, "period_hours": hours}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")


# =============================================================================
# SCENARIO ENDPOINTS
# =============================================================================

@app.get("/api/scenario/info")
async def get_scenario_info():
    """Get information about the current training scenario"""
    return {
        "name": "Water Treatment Plant",
        "description": "Municipal water treatment facility with intake, treatment, and distribution systems",
        "plcs": [
            {
                "id": 1,
                "name": "PLC-INTAKE",
                "ip": "10.0.1.10",
                "port": 502,
                "description": "Raw Water Intake & Pumping",
            },
            {
                "id": 2,
                "name": "PLC-TREATMENT", 
                "ip": "10.0.1.11",
                "port": 502,
                "description": "Water Treatment Process",
            },
            {
                "id": 3,
                "name": "PLC-DISTRIBUTION",
                "ip": "10.0.1.12",
                "port": 502,
                "description": "Clearwell & Distribution",
            },
        ],
        "vulnerabilities": [
            "Modbus TCP - No authentication",
            "Default credentials on HMI",
            "Unencrypted communications",
            "No network segmentation",
        ],
        "objectives": [
            "Enumerate Modbus devices on the network",
            "Read process values from PLCs",
            "Manipulate process control values",
            "Trigger unsafe process conditions",
            "Understand impact of OT attacks",
        ],
    }


@app.post("/api/scenario/reset")
async def reset_scenario():
    """Reset the scenario to initial state"""
    # Clear control overrides
    for plc_id in [1, 2, 3]:
        await redis_client.delete(f"vulnot:plc:{plc_id}:controls")
    
    return {
        "status": "success",
        "message": "Scenario reset to initial state",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

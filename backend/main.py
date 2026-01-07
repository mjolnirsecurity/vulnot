"""
VULNOT Backend - FastAPI Application
Real-time OT process data API with WebSocket support
"""

import asyncio
import json
from contextlib import asynccontextmanager
from typing import List

import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api import process_router, alarms_router, system_router
from core.config import settings
from core.websocket_manager import WebSocketManager
from services.redis_subscriber import RedisSubscriber


# WebSocket connection manager
ws_manager = WebSocketManager()

# Redis subscriber for process updates
redis_subscriber: RedisSubscriber = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    global redis_subscriber
    
    # Startup
    print("🚀 Starting VULNOT Backend...")
    
    # Initialize Redis connection
    redis_client = redis.from_url(settings.REDIS_URL)
    redis_subscriber = RedisSubscriber(redis_client, ws_manager)
    
    # Start background task for Redis pub/sub
    asyncio.create_task(redis_subscriber.listen())
    
    print("✅ VULNOT Backend started successfully!")
    print(f"📡 WebSocket endpoint: ws://localhost:8000/ws")
    print(f"📊 API endpoint: http://localhost:8000/api")
    
    yield
    
    # Shutdown
    print("👋 Shutting down VULNOT Backend...")
    await redis_subscriber.close()


# Create FastAPI app
app = FastAPI(
    title="VULNOT API",
    description="Vulnerable OT Lab - Real-time Process Data API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(process_router, prefix="/api/process", tags=["Process"])
app.include_router(alarms_router, prefix="/api/alarms", tags=["Alarms"])
app.include_router(system_router, prefix="/api/system", tags=["System"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "VULNOT API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "api": "/api",
            "websocket": "/ws",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time process updates
    
    Clients receive:
    - process_update: Real-time process values
    - alarm: New alarms
    - alarm_ack: Alarm acknowledgments
    - attack_detected: Attack detection events
    """
    await ws_manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Connected to VULNOT real-time feed"
        })
        
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client messages
            if message.get("type") == "subscribe":
                # Handle subscription requests
                topics = message.get("topics", [])
                await ws_manager.subscribe(websocket, topics)
                
            elif message.get("type") == "command":
                # Handle control commands (for HMI interactions)
                await handle_command(message, websocket)
                
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


async def handle_command(message: dict, websocket: WebSocket):
    """Handle control commands from HMI"""
    command = message.get("command")
    params = message.get("params", {})
    
    # Publish command to Redis for simulator to process
    global redis_subscriber
    if redis_subscriber:
        await redis_subscriber.publish_command(command, params)
        
    await websocket.send_json({
        "type": "command_ack",
        "command": command,
        "status": "sent"
    })


@app.websocket("/ws/process/{scenario}")
async def scenario_websocket(websocket: WebSocket, scenario: str):
    """
    Scenario-specific WebSocket endpoint
    
    Allows filtering updates by scenario (e.g., water_treatment, power_grid)
    """
    await ws_manager.connect(websocket, scenario=scenario)
    
    try:
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "scenario": scenario
        })
        
        while True:
            data = await websocket.receive_text()
            # Handle scenario-specific messages
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

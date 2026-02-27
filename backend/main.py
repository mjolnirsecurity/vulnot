"""
VULNOT Backend - FastAPI Application
Real-time OT process data API with WebSocket support
"""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import List
from urllib.parse import urlparse

import redis.asyncio as redis
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from api import process_router, alarms_router, system_router
from core.config import settings
from core.websocket_manager import WebSocketManager
from services.redis_subscriber import RedisSubscriber


# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000,http://localhost:8080"
    ).split(",")
]

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


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


# =============================================================================
# SECURITY HEADERS MIDDLEWARE
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self' ws://localhost:* wss://localhost:*; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'"
        )
        return response


# =============================================================================
# APPLICATION SETUP
# =============================================================================

# Create FastAPI app
app = FastAPI(
    title="VULNOT API",
    description="Vulnerable OT Lab - Real-time Process Data API",
    version="0.1.0",
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers (added first so it wraps all responses)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware - restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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


def _validate_ws_origin(websocket: WebSocket) -> bool:
    """Validate WebSocket connection origin against allowed origins"""
    origin = websocket.headers.get("origin")
    if origin is None:
        return True  # Allow connections without origin (e.g., CLI tools)
    return origin in ALLOWED_ORIGINS


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
    if not _validate_ws_origin(websocket):
        await websocket.close(code=4003, reason="Origin not allowed")
        return
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
    if not _validate_ws_origin(websocket):
        await websocket.close(code=4003, reason="Origin not allowed")
        return
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

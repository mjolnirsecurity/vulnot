"""
WebSocket Connection Manager
Handles real-time connections to dashboard clients
"""

import asyncio
import json
from typing import Dict, List, Set, Optional
from fastapi import WebSocket


class WebSocketManager:
    """
    Manages WebSocket connections for real-time process updates
    
    Features:
    - Connection tracking
    - Topic-based subscriptions
    - Scenario filtering
    - Broadcast capabilities
    """
    
    def __init__(self):
        # All active connections
        self.active_connections: List[WebSocket] = []
        
        # Connections by scenario
        self.scenario_connections: Dict[str, List[WebSocket]] = {}
        
        # Topic subscriptions
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, scenario: Optional[str] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        
        if scenario:
            if scenario not in self.scenario_connections:
                self.scenario_connections[scenario] = []
            self.scenario_connections[scenario].append(websocket)
            
        print(f"📡 New WebSocket connection. Total: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
            
        # Remove from scenario connections
        for scenario, connections in self.scenario_connections.items():
            if websocket in connections:
                connections.remove(websocket)
                
        print(f"📡 WebSocket disconnected. Total: {len(self.active_connections)}")
        
    async def subscribe(self, websocket: WebSocket, topics: List[str]):
        """Subscribe a connection to specific topics"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(topics)
            await websocket.send_json({
                "type": "subscribed",
                "topics": list(self.subscriptions[websocket])
            })
            
    async def unsubscribe(self, websocket: WebSocket, topics: List[str]):
        """Unsubscribe a connection from specific topics"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket] -= set(topics)
            
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
                
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
            
    async def broadcast_to_scenario(self, scenario: str, message: dict):
        """Broadcast message to clients subscribed to a specific scenario"""
        if scenario not in self.scenario_connections:
            return
            
        disconnected = []
        
        for connection in self.scenario_connections[scenario]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
                
        for conn in disconnected:
            self.disconnect(conn)
            
    async def broadcast_to_topic(self, topic: str, message: dict):
        """Broadcast message to clients subscribed to a specific topic"""
        disconnected = []
        
        for connection, topics in self.subscriptions.items():
            if topic in topics or "*" in topics:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
                    
        for conn in disconnected:
            self.disconnect(conn)
            
    async def send_to_client(self, websocket: WebSocket, message: dict):
        """Send message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending to client: {e}")
            self.disconnect(websocket)
            
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
        
    def get_scenario_connections(self, scenario: str) -> int:
        """Get number of connections for a specific scenario"""
        return len(self.scenario_connections.get(scenario, []))

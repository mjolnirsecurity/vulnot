"""
Redis Pub/Sub Subscriber
Listens for process updates from simulators and broadcasts to WebSocket clients
"""

import asyncio
import json
from typing import Optional

import redis.asyncio as redis
from core.websocket_manager import WebSocketManager


class RedisSubscriber:
    """
    Subscribes to Redis channels for real-time process data
    and forwards updates to WebSocket clients
    """
    
    # Redis channels
    CHANNEL_PROCESS = "vulnot:process"
    CHANNEL_ALARMS = "vulnot:alarms"
    CHANNEL_ATTACKS = "vulnot:attacks"
    CHANNEL_COMMANDS = "vulnot:commands"
    
    def __init__(self, redis_client: redis.Redis, ws_manager: WebSocketManager):
        self.redis = redis_client
        self.ws_manager = ws_manager
        self.pubsub = self.redis.pubsub()
        self.running = False
        
    async def listen(self):
        """Start listening for Redis messages"""
        self.running = True
        
        # Subscribe to channels
        await self.pubsub.subscribe(
            self.CHANNEL_PROCESS,
            self.CHANNEL_ALARMS,
            self.CHANNEL_ATTACKS
        )
        
        print(f"📡 Redis subscriber listening on channels...")
        
        while self.running:
            try:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )
                
                if message:
                    await self._handle_message(message)
                    
            except Exception as e:
                print(f"Redis subscriber error: {e}")
                await asyncio.sleep(1)
                
    async def _handle_message(self, message: dict):
        """Handle incoming Redis message"""
        channel = message.get("channel", b"").decode()
        data = message.get("data", b"")
        
        if isinstance(data, bytes):
            try:
                data = json.loads(data.decode())
            except json.JSONDecodeError:
                return
                
        # Route message based on channel
        if channel == self.CHANNEL_PROCESS:
            await self._handle_process_update(data)
        elif channel == self.CHANNEL_ALARMS:
            await self._handle_alarm(data)
        elif channel == self.CHANNEL_ATTACKS:
            await self._handle_attack(data)
            
    async def _handle_process_update(self, data: dict):
        """Handle process data update"""
        message = {
            "type": "process_update",
            "data": data,
            "timestamp": data.get("timestamp")
        }
        await self.ws_manager.broadcast(message)
        
    async def _handle_alarm(self, data: dict):
        """Handle alarm event"""
        message = {
            "type": "alarm",
            "data": data
        }
        await self.ws_manager.broadcast(message)
        
    async def _handle_attack(self, data: dict):
        """Handle attack detection event"""
        message = {
            "type": "attack_detected",
            "data": data
        }
        await self.ws_manager.broadcast(message)
        
    async def publish_command(self, command: str, params: dict):
        """Publish a control command to the simulators"""
        message = json.dumps({
            "command": command,
            "params": params
        })
        await self.redis.publish(self.CHANNEL_COMMANDS, message)
        
    async def close(self):
        """Stop the subscriber"""
        self.running = False
        await self.pubsub.unsubscribe()
        await self.redis.close()

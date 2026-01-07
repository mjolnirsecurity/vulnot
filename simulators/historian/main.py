"""
VULNOT OT Historian Simulator
Simulates an industrial historian (like OSIsoft PI, Wonderware, GE Proficy)

Attack Surface:
- SQL injection in tag queries
- Unauthenticated API access
- Data manipulation
- Historical data deletion
- Backup theft
"""

import asyncio
import json
import os
import time
import random
import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from aiohttp import web

import redis.asyncio as redis


# =============================================================================
# HISTORIAN CONFIGURATION
# =============================================================================

@dataclass
class HistorianTag:
    """Historian tag definition"""
    id: int
    name: str
    description: str
    data_type: str  # FLOAT, INT, BOOL, STRING
    engineering_units: str
    source: str  # Protocol/device source
    
    # Archive settings
    compression_enabled: bool = True
    compression_deviation: float = 0.5
    exception_deviation: float = 1.0
    
    # Current value
    current_value: Any = 0.0
    current_timestamp: float = field(default_factory=time.time)
    quality: str = "GOOD"


# Pre-configured tags from all VULNOT scenarios
HISTORIAN_TAGS = [
    # Water Treatment (Modbus)
    HistorianTag(1, "WATER.INTAKE.LEVEL", "Intake Reservoir Level", "FLOAT", "%", "Modbus:10.0.1.10"),
    HistorianTag(2, "WATER.INTAKE.FLOW", "Intake Flow Rate", "FLOAT", "GPM", "Modbus:10.0.1.10"),
    HistorianTag(3, "WATER.TREATMENT.PH", "Treatment pH", "FLOAT", "pH", "Modbus:10.0.1.11"),
    HistorianTag(4, "WATER.TREATMENT.TURBIDITY", "Turbidity", "FLOAT", "NTU", "Modbus:10.0.1.11"),
    HistorianTag(5, "WATER.CHLORINE.RESIDUAL", "Chlorine Residual", "FLOAT", "mg/L", "Modbus:10.0.1.11"),
    HistorianTag(6, "WATER.DISTRIBUTION.PRESSURE", "Distribution Pressure", "FLOAT", "PSI", "Modbus:10.0.1.12"),
    
    # Power Grid (DNP3)
    HistorianTag(10, "POWER.SUB1.VOLTAGE_A", "Substation 1 Phase A Voltage", "FLOAT", "kV", "DNP3:10.0.2.10"),
    HistorianTag(11, "POWER.SUB1.CURRENT_A", "Substation 1 Phase A Current", "FLOAT", "A", "DNP3:10.0.2.10"),
    HistorianTag(12, "POWER.SUB1.POWER", "Substation 1 Real Power", "FLOAT", "MW", "DNP3:10.0.2.10"),
    HistorianTag(13, "POWER.SUB1.FREQUENCY", "Grid Frequency", "FLOAT", "Hz", "DNP3:10.0.2.10"),
    HistorianTag(14, "POWER.SUB1.BREAKER_1", "Breaker 1 Status", "BOOL", "", "DNP3:10.0.2.10"),
    HistorianTag(15, "POWER.SUB1.BREAKER_2", "Breaker 2 Status", "BOOL", "", "DNP3:10.0.2.10"),
    
    # Manufacturing (S7comm)
    HistorianTag(20, "FACTORY.LINE1.SPEED", "Line 1 Speed", "FLOAT", "units/min", "S7:10.0.3.10"),
    HistorianTag(21, "FACTORY.LINE1.PARTS_GOOD", "Line 1 Good Parts", "INT", "count", "S7:10.0.3.10"),
    HistorianTag(22, "FACTORY.LINE1.PARTS_REJECT", "Line 1 Rejects", "INT", "count", "S7:10.0.3.10"),
    HistorianTag(23, "FACTORY.LINE1.OEE", "Line 1 OEE", "FLOAT", "%", "S7:10.0.3.10"),
    HistorianTag(24, "FACTORY.ROBOT1.CYCLE_TIME", "Robot 1 Cycle Time", "FLOAT", "sec", "S7:10.0.3.10"),
    
    # Chemical Reactor (OPC UA)
    HistorianTag(30, "REACTOR.TEMP", "Reactor Temperature", "FLOAT", "°C", "OPCUA:10.0.4.10"),
    HistorianTag(31, "REACTOR.PRESSURE", "Reactor Pressure", "FLOAT", "bar", "OPCUA:10.0.4.10"),
    HistorianTag(32, "REACTOR.LEVEL", "Reactor Level", "FLOAT", "%", "OPCUA:10.0.4.10"),
    HistorianTag(33, "REACTOR.AGITATOR_SPEED", "Agitator Speed", "FLOAT", "RPM", "OPCUA:10.0.4.10"),
    HistorianTag(34, "REACTOR.BATCH_PROGRESS", "Batch Progress", "FLOAT", "%", "OPCUA:10.0.4.10"),
    
    # Building Automation (BACnet)
    HistorianTag(40, "BUILDING.AHU1.SUPPLY_TEMP", "AHU-1 Supply Temperature", "FLOAT", "°F", "BACnet:10.0.5.10"),
    HistorianTag(41, "BUILDING.AHU1.RETURN_TEMP", "AHU-1 Return Temperature", "FLOAT", "°F", "BACnet:10.0.5.10"),
    HistorianTag(42, "BUILDING.CHILLER.CHW_TEMP", "Chilled Water Temperature", "FLOAT", "°F", "BACnet:10.0.5.10"),
    HistorianTag(43, "BUILDING.CHILLER.KW", "Chiller Power", "FLOAT", "kW", "BACnet:10.0.5.10"),
    HistorianTag(44, "BUILDING.TOTAL_POWER", "Building Total Power", "FLOAT", "kW", "BACnet:10.0.5.10"),
    
    # IIoT (MQTT)
    HistorianTag(50, "IIOT.LINE1.TEMP_01", "IIoT Temperature Sensor 1", "FLOAT", "°C", "MQTT:10.0.7.5"),
    HistorianTag(51, "IIOT.LINE1.VIBRATION_01", "IIoT Vibration Sensor 1", "FLOAT", "mm/s", "MQTT:10.0.7.5"),
    HistorianTag(52, "IIOT.LINE1.POWER_01", "IIoT Power Sensor 1", "FLOAT", "kW", "MQTT:10.0.7.5"),
    
    # CNC/PROFINET
    HistorianTag(60, "CNC.X_POSITION", "CNC X Axis Position", "FLOAT", "mm", "PROFINET:10.0.8.10"),
    HistorianTag(61, "CNC.Y_POSITION", "CNC Y Axis Position", "FLOAT", "mm", "PROFINET:10.0.8.10"),
    HistorianTag(62, "CNC.Z_POSITION", "CNC Z Axis Position", "FLOAT", "mm", "PROFINET:10.0.8.10"),
    HistorianTag(63, "CNC.SPINDLE_SPEED", "CNC Spindle Speed", "FLOAT", "RPM", "PROFINET:10.0.8.10"),
    HistorianTag(64, "CNC.PARTS_COUNT", "CNC Parts Count", "INT", "count", "PROFINET:10.0.8.10"),
]


# =============================================================================
# HISTORIAN SIMULATOR
# =============================================================================

class HistorianSimulator:
    """OT Historian Simulator"""
    
    def __init__(self):
        self.tags: Dict[int, HistorianTag] = {t.id: t for t in HISTORIAN_TAGS}
        self.db_path = "/tmp/historian.db"
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for historical data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tags table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                description TEXT,
                data_type TEXT,
                engineering_units TEXT,
                source TEXT
            )
        ''')
        
        # Historical data table - VULNERABLE TO SQL INJECTION
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id INTEGER,
                timestamp REAL,
                value REAL,
                quality TEXT,
                FOREIGN KEY (tag_id) REFERENCES tags(id)
            )
        ''')
        
        # Create index
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_tag_time ON history(tag_id, timestamp)')
        
        # Insert tags
        for tag in self.tags.values():
            cursor.execute('''
                INSERT OR REPLACE INTO tags (id, name, description, data_type, engineering_units, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (tag.id, tag.name, tag.description, tag.data_type, tag.engineering_units, tag.source))
            
        # Generate some historical data (last 24 hours)
        now = time.time()
        for tag in self.tags.values():
            for i in range(1440):  # 1 minute intervals for 24 hours
                ts = now - (1440 - i) * 60
                value = self._generate_historical_value(tag, ts)
                cursor.execute(
                    'INSERT INTO history (tag_id, timestamp, value, quality) VALUES (?, ?, ?, ?)',
                    (tag.id, ts, value, "GOOD")
                )
                
        conn.commit()
        conn.close()
        print(f"[Historian] Database initialized with {len(self.tags)} tags")
        
    def _generate_historical_value(self, tag: HistorianTag, timestamp: float) -> float:
        """Generate realistic historical value"""
        hour = (timestamp / 3600) % 24
        
        # Base patterns by tag type
        if "TEMP" in tag.name:
            base = 70 + 10 * (0.5 + 0.5 * (hour / 24))
        elif "PRESSURE" in tag.name:
            base = 50 + random.uniform(-5, 5)
        elif "LEVEL" in tag.name:
            cycle = (timestamp / 7200) % 1  # 2 hour cycle
            base = 30 + 40 * cycle
        elif "FLOW" in tag.name:
            base = 500 + random.uniform(-50, 50)
        elif "POWER" in tag.name:
            base = 100 + 50 * (0.5 + 0.5 * (hour / 12 if hour < 12 else (24 - hour) / 12))
        elif "SPEED" in tag.name:
            base = 1000 + random.uniform(-100, 100)
        elif "BREAKER" in tag.name:
            return 1.0  # Normally closed
        else:
            base = 50 + random.uniform(-10, 10)
            
        return base + random.uniform(-base * 0.02, base * 0.02)
        
    async def connect(self):
        """Connect to Redis"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
    async def update_tags(self):
        """Update current tag values"""
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for tag in self.tags.values():
            tag.current_value = self._generate_historical_value(tag, now)
            tag.current_timestamp = now
            
            # Archive to database
            cursor.execute(
                'INSERT INTO history (tag_id, timestamp, value, quality) VALUES (?, ?, ?, ?)',
                (tag.id, now, tag.current_value, tag.quality)
            )
            
        conn.commit()
        conn.close()
        
        # Publish to Redis
        if self.redis:
            state = {
                "timestamp": now,
                "tag_count": len(self.tags),
                "tags": {t.name: {"value": t.current_value, "quality": t.quality} for t in self.tags.values()}
            }
            await self.redis.publish("vulnot:historian:state", json.dumps(state))
            
    async def run(self):
        """Main loop"""
        await self.connect()
        self.running = True
        
        print(f"[Historian] Running with {len(self.tags)} tags")
        
        while self.running:
            await self.update_tags()
            await asyncio.sleep(60)  # Update every minute


# =============================================================================
# REST API (VULNERABLE)
# =============================================================================

class HistorianAPI:
    """Historian REST API - INTENTIONALLY VULNERABLE"""
    
    def __init__(self, simulator: HistorianSimulator):
        self.simulator = simulator
        self.app = web.Application()
        self._setup_routes()
        
    def _setup_routes(self):
        self.app.router.add_get('/api/tags', self.get_tags)
        self.app.router.add_get('/api/tags/{tag_name}', self.get_tag)
        self.app.router.add_get('/api/history', self.get_history)  # SQL INJECTION VULNERABLE
        self.app.router.add_post('/api/history', self.write_history)  # UNAUTHENTICATED
        self.app.router.add_delete('/api/history', self.delete_history)  # UNAUTHENTICATED
        self.app.router.add_get('/api/backup', self.get_backup)  # DATA EXFIL
        self.app.router.add_post('/api/query', self.raw_query)  # SQL INJECTION
        
    async def get_tags(self, request: web.Request) -> web.Response:
        """Get all tags - NO AUTHENTICATION"""
        tags = [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "data_type": t.data_type,
                "units": t.engineering_units,
                "source": t.source,
                "current_value": t.current_value,
                "quality": t.quality,
            }
            for t in self.simulator.tags.values()
        ]
        return web.json_response({"tags": tags, "count": len(tags)})
        
    async def get_tag(self, request: web.Request) -> web.Response:
        """Get single tag by name"""
        tag_name = request.match_info['tag_name']
        
        for tag in self.simulator.tags.values():
            if tag.name == tag_name:
                return web.json_response({
                    "id": tag.id,
                    "name": tag.name,
                    "value": tag.current_value,
                    "timestamp": tag.current_timestamp,
                    "quality": tag.quality,
                })
                
        return web.json_response({"error": "Tag not found"}, status=404)
        
    async def get_history(self, request: web.Request) -> web.Response:
        """Get historical data - VULNERABLE TO SQL INJECTION"""
        tag_name = request.query.get('tag', '')
        start_time = request.query.get('start', '')
        end_time = request.query.get('end', '')
        
        # VULNERABLE: Direct string interpolation!
        query = f"SELECT h.timestamp, h.value, h.quality FROM history h JOIN tags t ON h.tag_id = t.id WHERE t.name = '{tag_name}'"
        
        if start_time:
            query += f" AND h.timestamp >= {start_time}"
        if end_time:
            query += f" AND h.timestamp <= {end_time}"
            
        query += " ORDER BY h.timestamp DESC LIMIT 1000"
        
        print(f"[Historian API] Query: {query}")
        
        try:
            conn = sqlite3.connect(self.simulator.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            data = [{"timestamp": r[0], "value": r[1], "quality": r[2]} for r in rows]
            return web.json_response({"tag": tag_name, "data": data, "count": len(data)})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
            
    async def write_history(self, request: web.Request) -> web.Response:
        """Write historical data - NO AUTHENTICATION"""
        try:
            body = await request.json()
            tag_id = body.get('tag_id')
            timestamp = body.get('timestamp', time.time())
            value = body.get('value')
            quality = body.get('quality', 'GOOD')
            
            conn = sqlite3.connect(self.simulator.db_path)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO history (tag_id, timestamp, value, quality) VALUES (?, ?, ?, ?)',
                (tag_id, timestamp, value, quality)
            )
            conn.commit()
            conn.close()
            
            print(f"[Historian API] ⚠️ Data injected: tag={tag_id}, value={value}")
            return web.json_response({"status": "written", "tag_id": tag_id})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
            
    async def delete_history(self, request: web.Request) -> web.Response:
        """Delete historical data - NO AUTHENTICATION"""
        tag_name = request.query.get('tag', '')
        start_time = request.query.get('start', '0')
        end_time = request.query.get('end', str(time.time()))
        
        try:
            conn = sqlite3.connect(self.simulator.db_path)
            cursor = conn.cursor()
            
            # Get tag_id
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            row = cursor.fetchone()
            if row:
                tag_id = row[0]
                cursor.execute(
                    "DELETE FROM history WHERE tag_id = ? AND timestamp BETWEEN ? AND ?",
                    (tag_id, float(start_time), float(end_time))
                )
                deleted = cursor.rowcount
                conn.commit()
                
                print(f"[Historian API] ⚠️ DELETED {deleted} records for {tag_name}")
                conn.close()
                return web.json_response({"status": "deleted", "count": deleted})
                
            conn.close()
            return web.json_response({"error": "Tag not found"}, status=404)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
            
    async def get_backup(self, request: web.Request) -> web.Response:
        """Download database backup - DATA EXFILTRATION"""
        print(f"[Historian API] ⚠️ Database backup requested!")
        
        with open(self.simulator.db_path, 'rb') as f:
            data = f.read()
            
        return web.Response(
            body=data,
            content_type='application/octet-stream',
            headers={'Content-Disposition': 'attachment; filename="historian_backup.db"'}
        )
        
    async def raw_query(self, request: web.Request) -> web.Response:
        """Execute raw SQL query - EXTREMELY VULNERABLE"""
        try:
            body = await request.json()
            query = body.get('query', '')
            
            print(f"[Historian API] ⚠️ RAW QUERY: {query}")
            
            conn = sqlite3.connect(self.simulator.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                columns = [d[0] for d in cursor.description] if cursor.description else []
                conn.close()
                return web.json_response({"columns": columns, "rows": rows})
            else:
                conn.commit()
                affected = cursor.rowcount
                conn.close()
                return web.json_response({"status": "executed", "affected_rows": affected})
                
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
            
    async def run(self):
        """Run API server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        print("[Historian API] Running on port 8080")
        print("[Historian API] ⚠️ NO AUTHENTICATION - SQL INJECTION VULNERABLE")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    simulator = HistorianSimulator()
    api = HistorianAPI(simulator)
    
    try:
        await asyncio.gather(
            simulator.run(),
            api.run(),
            asyncio.Event().wait()
        )
    except KeyboardInterrupt:
        print("\n[Historian] Shutting down...")
        simulator.running = False


if __name__ == "__main__":
    asyncio.run(main())

# VULNOT API Reference

This document provides a complete reference for the VULNOT REST API.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Process API](#process-api)
4. [Alarms API](#alarms-api)
5. [System API](#system-api)
6. [Historian API](#historian-api)
7. [WebSocket API](#websocket-api)
8. [Error Handling](#error-handling)

---

## Overview

### Base URL

```
http://localhost:9000/api/v1
```

### Response Format

All responses are JSON:

```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Device not found"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Authentication

The API does not require authentication by default (intentionally vulnerable for training). In production deployments, implement API key authentication:

```http
Authorization: Bearer <api_key>
```

---

## Process API

### Get All Process Data

Retrieve current values from all scenarios.

```http
GET /api/v1/process
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "water_treatment": {
      "intake_level": 75.5,
      "chlorine_level": 2.3,
      "pump_1_running": true,
      "pump_2_running": false
    },
    "power_grid": {
      "voltage_a": 13.8,
      "current_a": 450,
      "breaker_1": "CLOSED",
      "frequency": 60.02
    },
    "manufacturing": {
      "line_speed": 85,
      "production_count": 12450,
      "cpu_state": "RUN"
    }
  }
}
```

### Get Scenario Data

Retrieve data for a specific scenario.

```http
GET /api/v1/process/{scenario}
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| scenario | string | Scenario ID (water, power, factory, reactor, building, packaging, iiot, cnc, historian) |

**Example:**

```http
GET /api/v1/process/water
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "scenario": "water_treatment",
    "devices": [
      {
        "id": "PLC-INTAKE",
        "ip": "10.0.1.10",
        "protocol": "modbus",
        "status": "online",
        "registers": {
          "tank_level": 75.5,
          "inlet_valve": 1,
          "outlet_pump": 1,
          "chlorine_setpoint": 2.5
        }
      }
    ],
    "process_values": {
      "intake_tank": {
        "level": 75.5,
        "unit": "%",
        "high_alarm": 90,
        "low_alarm": 10
      },
      "chlorine": {
        "value": 2.3,
        "unit": "ppm",
        "setpoint": 2.5
      }
    }
  }
}
```

### Write Process Value

Write a value to an OT device (Modbus example).

```http
POST /api/v1/process/{scenario}/write
```

**Request Body:**

```json
{
  "device_id": "PLC-INTAKE",
  "register": 1,
  "value": 100,
  "register_type": "holding"
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "device_id": "PLC-INTAKE",
    "register": 1,
    "previous_value": 75,
    "new_value": 100,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Get Device Info

Get detailed information about a specific device.

```http
GET /api/v1/process/{scenario}/device/{device_id}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "device_id": "PLC-INTAKE",
    "ip": "10.0.1.10",
    "port": 502,
    "protocol": "modbus",
    "vendor": "Generic Modbus",
    "firmware": "1.0.0",
    "status": "online",
    "last_seen": "2024-01-15T10:29:55Z",
    "vulnerabilities": [
      "NO_AUTHENTICATION",
      "WRITABLE_REGISTERS",
      "NO_ENCRYPTION"
    ]
  }
}
```

---

## Alarms API

### Get Active Alarms

Retrieve all active alarms.

```http
GET /api/v1/alarms
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| severity | string | Filter by severity (critical, high, medium, low) |
| scenario | string | Filter by scenario |
| acknowledged | boolean | Filter by acknowledgment status |

**Response:**

```json
{
  "status": "success",
  "data": {
    "alarms": [
      {
        "id": "ALM-001",
        "timestamp": "2024-01-15T10:28:00Z",
        "severity": "high",
        "scenario": "water_treatment",
        "device": "PLC-INTAKE",
        "message": "Tank level high (92%)",
        "acknowledged": false,
        "value": 92,
        "setpoint": 90
      }
    ],
    "total": 1,
    "unacknowledged": 1
  }
}
```

### Acknowledge Alarm

Acknowledge an alarm.

```http
POST /api/v1/alarms/{alarm_id}/acknowledge
```

**Request Body:**

```json
{
  "operator": "admin",
  "comment": "Investigating high tank level"
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "alarm_id": "ALM-001",
    "acknowledged": true,
    "acknowledged_by": "admin",
    "acknowledged_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get Alarm History

Retrieve historical alarms.

```http
GET /api/v1/alarms/history
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| start | datetime | Start time (ISO 8601) |
| end | datetime | End time (ISO 8601) |
| limit | integer | Maximum results (default: 100) |

---

## System API

### Health Check

Check API health status.

```http
GET /api/v1/health
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "api": "healthy",
    "redis": "healthy",
    "influxdb": "healthy",
    "simulators": {
      "water": "online",
      "power": "online",
      "factory": "online",
      "reactor": "online",
      "building": "online",
      "packaging": "online",
      "iiot": "online",
      "cnc": "online",
      "historian": "online"
    }
  }
}
```

### Get System Status

Get overall system status.

```http
GET /api/v1/system/status
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "version": "1.0.0",
    "uptime": 86400,
    "scenarios": 9,
    "devices": 15,
    "active_alarms": 2,
    "ids_alerts": 5,
    "last_attack": "2024-01-15T10:25:00Z"
  }
}
```

### Get IDS Alerts

Retrieve IDS alerts.

```http
GET /api/v1/system/ids/alerts
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "alerts": [
      {
        "id": "IDS-001",
        "timestamp": "2024-01-15T10:27:00Z",
        "rule_id": "MODBUS-SCAN",
        "severity": "medium",
        "source_ip": "10.0.1.100",
        "destination_ip": "10.0.1.10",
        "protocol": "modbus",
        "description": "Modbus device enumeration detected",
        "mitre_technique": "T0846"
      }
    ],
    "total": 1
  }
}
```

---

## Historian API

The Historian API is intentionally vulnerable for training purposes.

### List Tags

Get all available tags.

```http
GET /api/v1/historian/tags
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "tags": [
      {
        "id": 1,
        "name": "WATER.INTAKE.LEVEL",
        "description": "Intake tank level",
        "unit": "%",
        "data_type": "float"
      },
      {
        "id": 2,
        "name": "WATER.CHLORINE.VALUE",
        "description": "Chlorine concentration",
        "unit": "ppm",
        "data_type": "float"
      }
    ],
    "total": 64
  }
}
```

### Query Historical Data

Query historical tag data.

```http
GET /api/v1/historian/history
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| tag | string | Tag name (VULNERABLE: SQL injection) |
| start | datetime | Start time |
| end | datetime | End time |
| interval | string | Aggregation interval (1m, 5m, 1h) |

**⚠️ VULNERABLE EXAMPLE:**

```http
GET /api/v1/historian/history?tag=WATER.INTAKE.LEVEL' UNION SELECT * FROM tags--
```

### Raw Query (Intentionally Dangerous)

Execute raw SQL query.

```http
POST /api/v1/historian/query
```

**Request Body:**

```json
{
  "query": "SELECT * FROM history WHERE tag_id = 1"
}
```

**⚠️ WARNING:** This endpoint is intentionally vulnerable. In real systems, raw SQL endpoints should never exist.

### Backup Database

Download database backup.

```http
GET /api/v1/historian/backup
```

**Response:** SQLite database file download

**⚠️ VULNERABLE:** No authentication, full database exfiltration.

---

## WebSocket API

### Connect

```javascript
const ws = new WebSocket('ws://localhost:9000/ws');
```

### Subscribe to Process Data

```json
{
  "action": "subscribe",
  "channel": "process",
  "scenario": "water"
}
```

### Receive Updates

```json
{
  "type": "process_update",
  "scenario": "water",
  "data": {
    "intake_level": 76.2,
    "chlorine_level": 2.4,
    "timestamp": "2024-01-15T10:30:01Z"
  }
}
```

### Subscribe to Alarms

```json
{
  "action": "subscribe",
  "channel": "alarms"
}
```

### Receive Alarm

```json
{
  "type": "alarm",
  "data": {
    "id": "ALM-002",
    "severity": "critical",
    "message": "Pump failure detected",
    "timestamp": "2024-01-15T10:30:05Z"
  }
}
```

### Subscribe to IDS Alerts

```json
{
  "action": "subscribe",
  "channel": "ids"
}
```

---

## Error Handling

### Error Codes

| Code | Description |
|------|-------------|
| VALIDATION_ERROR | Invalid request parameters |
| RESOURCE_NOT_FOUND | Requested resource not found |
| DEVICE_OFFLINE | OT device is not responding |
| WRITE_FAILED | Failed to write to device |
| DATABASE_ERROR | Database operation failed |
| INTERNAL_ERROR | Internal server error |

### HTTP Status Codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |

### Example Error

```json
{
  "status": "error",
  "error": {
    "code": "DEVICE_OFFLINE",
    "message": "Device PLC-INTAKE is not responding",
    "details": {
      "device_id": "PLC-INTAKE",
      "ip": "10.0.1.10",
      "last_seen": "2024-01-15T10:25:00Z"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Rate Limiting

The API implements basic rate limiting:

| Endpoint | Limit |
|----------|-------|
| Read operations | 100/minute |
| Write operations | 10/minute |
| Historian queries | 30/minute |

Exceeded limits return `429 Too Many Requests`.

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:9000/api/v1"

# Get process data
response = requests.get(f"{BASE_URL}/process/water")
data = response.json()
print(f"Tank Level: {data['data']['process_values']['intake_tank']['level']}%")

# Write to device
response = requests.post(f"{BASE_URL}/process/water/write", json={
    "device_id": "PLC-INTAKE",
    "register": 1,
    "value": 50
})
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:9000/api/v1';

// Get process data
fetch(`${BASE_URL}/process/water`)
  .then(res => res.json())
  .then(data => console.log(data));

// WebSocket connection
const ws = new WebSocket('ws://localhost:9000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
ws.send(JSON.stringify({ action: 'subscribe', channel: 'process' }));
```

### cURL

```bash
# Get process data
curl http://localhost:9000/api/v1/process/water

# Write to device
curl -X POST http://localhost:9000/api/v1/process/water/write \
  -H "Content-Type: application/json" \
  -d '{"device_id": "PLC-INTAKE", "register": 1, "value": 50}'

# Get alarms
curl http://localhost:9000/api/v1/alarms?severity=critical
```

---

*VULNOT API Reference - Developed by Milind Bhargava at Mjolnir Security*

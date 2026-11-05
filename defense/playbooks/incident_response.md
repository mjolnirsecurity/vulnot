# VULNOT Incident Response Playbooks

## Overview
These playbooks provide structured response procedures for OT security incidents.

---

## Playbook 1: Unauthorized OT Protocol Access

### Severity: HIGH
### MITRE ATT&CK: T0846 - Remote System Discovery

### Detection Indicators
- Modbus/DNP3/S7comm traffic from non-authorized sources
- Port scans on OT protocol ports (502, 20000, 102, 4840, 47808, 44818)
- IDS alerts for protocol anomalies

### Immediate Actions (0-15 minutes)
1. [ ] Identify source IP and affected systems
2. [ ] Check if source is from IT network (lateral movement) or external
3. [ ] Verify with asset owner if activity is authorized
4. [ ] If unauthorized, isolate the source:
   ```bash
   # Add firewall rule to block source
   iptables -I INPUT -s <source_ip> -j DROP
   ```

### Containment (15-60 minutes)
1. [ ] Enable additional logging on affected PLCs/RTUs
2. [ ] Capture network traffic for forensics
   ```bash
   tcpdump -i eth0 -w incident_$(date +%Y%m%d_%H%M%S).pcap host <source_ip>
   ```
3. [ ] Check historian for anomalous process values
4. [ ] Review authentication logs for compromised credentials

### Eradication
1. [ ] Identify entry point (VPN, firewall misconfiguration, etc.)
2. [ ] Patch/remediate vulnerability
3. [ ] Reset any potentially compromised credentials
4. [ ] Update firewall rules

### Recovery
1. [ ] Restore network segmentation
2. [ ] Verify PLC/RTU configurations unchanged
3. [ ] Resume normal monitoring

### Lessons Learned
- Document timeline
- Update IDS signatures
- Review network segmentation

---

## Playbook 2: PLC Program Modification

### Severity: CRITICAL
### MITRE ATT&CK: T0821 - Modify Controller Tasking

### Detection Indicators
- Unauthorized program upload/download to PLC
- Engineering workstation access outside business hours
- Changes to PLC logic checksums
- S7comm write requests to program memory

### Immediate Actions (0-15 minutes)
1. [ ] **DO NOT IMMEDIATELY STOP THE PLC** - assess process state first
2. [ ] Identify which PLC and what changes were made
3. [ ] Compare running program to known-good baseline
4. [ ] Contact process engineer to assess safety implications

### Containment (15-60 minutes)
1. [ ] If safe, take PLC offline and switch to manual control
2. [ ] Isolate engineering workstations from OT network
3. [ ] Preserve evidence:
   ```bash
   # Download current PLC program for analysis
   # Document all running values and states
   ```
4. [ ] Check for persistence mechanisms

### Eradication
1. [ ] Restore PLC program from verified backup
2. [ ] Forensically analyze compromised engineering workstation
3. [ ] Re-image affected workstations
4. [ ] Reset all PLC passwords

### Recovery
1. [ ] Verify restored program against baseline
2. [ ] Perform controlled startup procedure
3. [ ] Monitor process values closely for 24-48 hours

### Lessons Learned
- Implement PLC program change detection
- Establish baseline program hashes
- Review change management procedures

---

## Playbook 3: Safety System Compromise

### Severity: CRITICAL - POTENTIAL LIFE SAFETY
### MITRE ATT&CK: T0837 - Loss of Safety

### Detection Indicators
- Any unauthorized access to SIS/ESD systems
- Configuration changes to safety logic
- Alarms disabled or thresholds modified
- TRITON/TRISIS indicators

### Immediate Actions (0-5 minutes)
1. [ ] **ASSUME WORST CASE - INITIATE SAFE SHUTDOWN**
2. [ ] Alert all personnel in affected area
3. [ ] Contact safety manager immediately
4. [ ] Do NOT attempt to "fix" the SIS - isolate it

### Containment (5-30 minutes)
1. [ ] Physical isolation of SIS network
2. [ ] Shut down affected process via manual controls
3. [ ] Deploy field operators to verify physical safety
4. [ ] Preserve all evidence (do not power cycle!)

### Eradication
1. [ ] Full forensic analysis of SIS controllers
2. [ ] Verify firmware integrity
3. [ ] Complete SIS validation and testing before return to service
4. [ ] Engage SIS vendor for support

### Recovery
1. [ ] Rebuild SIS from verified offline backup
2. [ ] Full functional safety testing
3. [ ] Independent verification before operation
4. [ ] Enhanced monitoring

### Lessons Learned
- Review SIS network isolation
- Implement additional SIS monitoring
- Consider hardware-based SIS solutions

---

## Playbook 4: MQTT/IIoT Compromise

### Severity: HIGH
### MITRE ATT&CK: T0869 - Standard Application Layer Protocol

### Detection Indicators
- Unauthorized MQTT client connections
- Messages to control topics from unknown sources
- Gateway credential changes
- Firmware update triggers

### Immediate Actions (0-15 minutes)
1. [ ] Identify compromised MQTT broker or gateway
2. [ ] Check for data exfiltration (subscribe to '#')
3. [ ] Verify sensor readings against physical measurements
4. [ ] Block unauthorized clients

### Containment (15-60 minutes)
1. [ ] Enable MQTT authentication if not already
2. [ ] Rotate all gateway credentials
3. [ ] Capture MQTT traffic:
   ```bash
   mosquitto_sub -h <broker> -t '#' -v > mqtt_capture.log
   ```
4. [ ] Check for malicious firmware updates

### Eradication
1. [ ] Reflash gateway firmware from known-good source
2. [ ] Reset all default credentials
3. [ ] Implement TLS for MQTT
4. [ ] Configure topic-level ACLs

### Recovery
1. [ ] Verify sensor calibration
2. [ ] Restore normal data flow
3. [ ] Enhanced monitoring for 48 hours

### Lessons Learned
- Implement MQTT authentication
- Use TLS encryption
- Monitor for default credentials

---

## Playbook 5: Ransomware in OT Environment

### Severity: CRITICAL
### MITRE ATT&CK: T0882 - Data Destruction

### Detection Indicators
- Encryption of HMI/SCADA workstations
- Inaccessible historian data
- Ransom notes
- Lateral movement from IT network

### Immediate Actions (0-15 minutes)
1. [ ] Disconnect affected systems from network immediately
2. [ ] Do NOT pay ransom
3. [ ] Switch to manual operation where safe
4. [ ] Activate incident response team

### Containment (15-60 minutes)
1. [ ] Isolate IT/OT interconnection points
2. [ ] Verify PLCs are still operational (often not directly affected)
3. [ ] Check backup systems for infection
4. [ ] Preserve evidence from affected systems

### Eradication
1. [ ] Identify ransomware variant
2. [ ] Clean or reimage affected systems
3. [ ] Patch vulnerabilities used for entry
4. [ ] Verify clean backups exist

### Recovery
1. [ ] Restore from clean backups
2. [ ] Rebuild HMI/SCADA systems
3. [ ] Restore historian data if possible
4. [ ] Phased reconnection with monitoring

### Lessons Learned
- Improve IT/OT segmentation
- Offline backup strategy for OT
- Endpoint protection for HMI/SCADA

---

## Evidence Collection Checklist

### Network Evidence
- [ ] PCAP files from affected segments
- [ ] Firewall logs (src, dst, port, timestamp)
- [ ] IDS/IPS alerts
- [ ] NetFlow data

### System Evidence
- [ ] PLC program backups (before/after)
- [ ] HMI/SCADA logs
- [ ] Historian data exports
- [ ] Authentication logs
- [ ] System event logs

### Process Evidence
- [ ] Process values during incident
- [ ] Alarm history
- [ ] Operator actions
- [ ] Safety system status

### Chain of Custody
- [ ] Document who collected evidence
- [ ] Hash all files (SHA-256)
- [ ] Secure storage with access logging
- [ ] Maintain timeline

---

## Escalation Matrix

| Severity | Initial Response | Escalate To | Timeline |
|----------|------------------|-------------|----------|
| LOW | SOC Analyst | SOC Lead | 4 hours |
| MEDIUM | SOC Lead | Security Manager | 2 hours |
| HIGH | Security Manager | CISO + OT Manager | 1 hour |
| CRITICAL | CISO + OT Manager | Executive Team | 15 minutes |

### Contact List (Example)
- SOC: soc@company.com / +1-XXX-XXX-XXXX
- OT Security: ot-security@company.com
- Process Engineering: process-eng@company.com
- Safety Manager: safety@company.com
- CISO: ciso@company.com
- Legal: legal@company.com
- PR/Communications: pr@company.com

---

## MITRE ATT&CK for ICS Reference

| Technique ID | Name | Relevant Playbook |
|--------------|------|-------------------|
| T0821 | Modify Controller Tasking | PLC Program Modification |
| T0831 | Manipulation of Control | Unauthorized Access |
| T0837 | Loss of Safety | Safety System Compromise |
| T0846 | Remote System Discovery | Unauthorized Access |
| T0859 | Valid Accounts | All playbooks |
| T0869 | Standard Application Layer Protocol | MQTT/IIoT Compromise |
| T0882 | Data Destruction | Ransomware |
| AML.T0051.001 | Indirect Prompt Injection | Playbook 5: Agentic AI / MCP Compromise |
| AML.T0015 / AML.T0018 | Evade / Backdoor ML Model | Playbook 5: Agentic AI / MCP Compromise |
| T0816 / T0828 | DER / BESS Grid Oscillation | Playbook 6: DER & BESS Microgrid Instability |
| T1090.001 | Internal Proxy (Volt Typhoon LotL) | Playbook 7: LotL OT Conduit Eradication |

---

## Playbook 5: Agentic AI SCADA Copilot & Industrial ML Compromise

### Severity: CRITICAL
### MITRE ATLAS / ATT&CK: AML.T0051.001 (Indirect Prompt Injection), AML.T0015 (Evade ML), AML.T0018 (Backdoor ML), T0855

### Detection Indicators
- `AI-MCP-001` / `SIEM-021`: MCP tool invocation (`mcp_opcua_write_node`, `mcp_modbus_write_register`) without Human-in-the-Loop (HITL) approval token
- `AI-PDM-001` / `SIEM-022`: Physical RTD/vibration sensor exceeds safe bounds (`> 85°C`) while Autoencoder reconstruction error remains `< 0.65`
- `AI-ONNX-001`: Edge vision QC server loads unsigned or hash-mismatched `.onnx` weights

### Immediate Actions (0–10 minutes)
1. [ ] Revoke autonomous Level 1/2 write permissions on the MCP server:
   ```bash
   vulnot-ai harden --component copilot
   ```
2. [ ] Enforce deterministic Control Barrier Functions (CBF) & hardware thermal interlocks below all ML/RL controllers:
   ```bash
   vulnot-defend physics-guard --scenario all
   vulnot-ai harden --component pdm-vision
   vulnot-ai harden --component rl-soar
   ```
3. [ ] Acquire forensic snapshot of Copilot prompt context, MCP invocation logs, and ONNX weights:
   ```bash
   vulnot-forensics acquire-ai -t 10.0.90.10 -c CASE-AI-001
   ```

---

## Playbook 6: DER Solar, 50 MWh BESS & OCPP Megawatt EV Grid Oscillation

### Severity: CRITICAL
### MITRE ATT&CK: T0816 (Device Restart/Shutdown), T0828 (Loss of Productivity and Revenue)

### Detection Indicators
- `DER-001` / `SIEM-025`: Coupled substation frequency drops below `59.5 Hz` or UFLS `81U` relay trips (`< 59.3 Hz`)
- Solar inverter IEEE 2030.5 frequency-watt droop slope inverted (`freq_watt_droop_inverted = True`)
- BESS BMS thermal runaway interlock disabled (`bms_thermal_interlock_enabled = False`)

### Immediate Actions (0–5 minutes)
1. [ ] Restore Golden Baseline on the DER Microgrid controller and re-lock BESS BMS hardware interlocks:
   ```bash
   vulnot-defend plc-baseline --scenario der-microgrid --action restore
   ```
2. [ ] Rate-limit OCPP 2.0.1 CSMS load-step commands to `<= 2 MW/min` ramp rate.

---

## Playbook 7: Volt Typhoon Living-off-the-Land (LotL) OT Conduit Eradication

### Severity: HIGH / CRITICAL
### MITRE ATT&CK: T1090.001 (Internal Proxy), T0888 (Remote System Information Discovery)

### Detection Indicators
- `SIEM-024`: `netsh interface portproxy` or `socat` listeners detected on IT/OT jump host (`10.0.99.5`) or IIoT gateway (`10.0.7.10`)
- Staged PLC engineering files (`.zap16`, `.ACD`) in temporary directories

### Immediate Actions (0–15 minutes)
1. [ ] Hunt and enumerate all active LotL portproxy chains and staged PLC archives:
   ```bash
   vulnot-blue hunt --hypothesis lotl-portproxy
   ```
2. [ ] Flush unauthorized relays and isolate the compromised conduit without disrupting Level 1 safety loops:
   ```bash
   vulnot-pivot lotl-relay --action flush
   vulnot-blue contain --isolate-ip 10.0.99.5 --conduit CONDUIT-L4-L35
   ```


# Forensics 07: Volt Typhoon Living-off-the-Land (LotL) in Critical Infrastructure DMZs

## Overview
- **Track**: ICS Incident Forensics & Threat Hunting (`VULNOT-401`)
- **Incident Reference**: CISA AA24-038A — PRC State-Sponsored Actors (Volt Typhoon) Compromising US Critical Infrastructure
- **Target Environment**: IIoT Edge Gateway (`10.0.7.10`), OT Data Historian (`10.0.99.20`), Water/Power DMZ
- **Difficulty**: Expert
- **Duration**: 150 minutes
- **MITRE ATT&CK**: `T1090.001` (Internal Proxy / `netsh portproxy`), `T1003.003` (NTDS), `T0888` (Remote System Information Discovery)

---

## Incident Background
Unlike noisy ransomware groups, **Volt Typhoon** maintains covert, multi-year persistence inside water, power, and pipeline networks without dropping custom malware binaries. Instead, operators:
1. Compromise perimeter SOHO/industrial edge gateways (`10.0.7.10`, default credentials or unpatched CVEs).
2. Harvest Active Directory credentials (`ntds.dit`) and engineering workstation PLC project files (`.zap16` TIA Portal, `.ACD` Studio 5000).
3. Chain native OS port proxies (`netsh interface portproxy add v4tov4` on Windows jump hosts and `socat`/SSH tunnels on Linux edge gateways) to relay traffic into Level 1 Modbus (`10.0.1.10:502`) and DNP3 (`10.0.2.10:20000`) subnets.

---

## Investigation Objectives & Flags

### Objective 1: Identify Multi-Hop `netsh portproxy` & Edge Gateway Relays
Audit the IIoT Edge Gateway (`10.0.7.10`) and IT/OT Jump Host (`10.0.99.5`) to uncover loopback/port-forwarding rules relaying external traffic on port `8502` directly to `10.0.1.10:502`.
```bash
vulnot-ai lotl-audit --gateway 10.0.7.10
```
- **Flag 1**: `VULNOT{volt_typhoon_netsh_portproxy_chain_found}`

### Objective 2: Detect Staged PLC Project Files & Off-Hours Polling Jitter
Correlate historian audit logs (`10.0.99.20:8553/api/audit`) with off-hours Modbus FC43 Device Identification scans originating from the jump host's internal IP.
```bash
vulnot-moodle submit forensics-07 -f "VULNOT{lotl_ot_dmz_persistence_eradicated}"
```
- **Flag 2**: `VULNOT{lotl_ot_dmz_persistence_eradicated}`

---

## Remediation & Hardening
- Monitor Registry key `HKLM\SYSTEM\CurrentControlSet\Services\PortProxy\v4tov4\tcp` across all IT/OT DMZ jump hosts.
- Enforce behavioral baselining on Level 1/2 subnets: even when traffic originates from a trusted jump host IP, alert on new TCP source port distributions, unusual polling cadence jitter, or diagnostic function codes (`FC43`, `S7 SZL 0x001C`).

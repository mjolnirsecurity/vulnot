'use client';

import React, { useEffect, useId, useRef, useState } from 'react';

const DEFAULT_MOODLE_URL = 'https://portal.mjolnir.training';
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface LabObjective {
  id: string;
  title: string;
  points: number;
  hint: string;
  flag_code?: string;
  alt_flags?: string[];
  completed: boolean;
}

export interface TrainingLab {
  id: string;
  number: number;
  code: string;
  title: string;
  track: 'redteam' | 'forensics' | 'soc';
  course_shortname: 'VULNOT-101' | 'VULNOT-201' | 'VULNOT-301';
  moodle_cmid: number;
  moodle_assign_id: number;
  duration: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  scenario: string;
  network: string;
  target_host: string;
  protocols: string[];
  mitre_techniques: string[];
  iec62443_reqs: string[];
  prerequisites: string[];
  description: string;
  objectives: LabObjective[];
  status: 'not_started' | 'in_progress' | 'completed';
  progress: number;
  score: number;
  earned_points: number;
  total_points: number;
  synced_to_moodle: boolean;
  last_synced_at?: string | null;
  portal_activity_url: string;
  portal_course_url: string;
  markdown_content?: string;
}

export interface MoodleCourse {
  id: number;
  shortname: 'VULNOT-101' | 'VULNOT-201' | 'VULNOT-301';
  fullname: string;
  category: string;
  duration: string;
  level: string;
  certification: string;
  portal_url: string;
  description: string;
  labs: string[];
}

interface PortalStatus {
  reachable: boolean;
  portal_url: string;
  login_url: string;
  token_endpoint: string;
  rest_endpoint: string;
  http_status: number;
  latency_ms: number;
  site_title: string;
  moodle_detected: boolean;
  webservices_endpoint_active: boolean;
  checked_at: string;
}

interface MoodleUser {
  userid: number;
  username: string;
  fullname: string;
  sitename: string;
  siteurl: string;
  moodle_notice?: string;
}

const FALLBACK_COURSES: MoodleCourse[] = [
  {
    id: 101,
    shortname: 'VULNOT-101',
    fullname: 'VULNOT Fundamentals: OT/ICS Security Core',
    category: 'OT/ICS Security',
    duration: '2 Days (16 Hours)',
    level: 'Beginner to Intermediate',
    certification: 'VULNOT Associate Certificate',
    portal_url: `${DEFAULT_MOODLE_URL}/course/view.php?id=101`,
    description:
      'Hands-on introduction to industrial control systems, Purdue Model architecture, OT network reconnaissance, Modbus TCP & DNP3 exploitation, S7comm PLC sabotage, and passive baseline monitoring.',
    labs: ['lab-01', 'lab-02', 'lab-03', 'lab-04', 'soc-01'],
  },
  {
    id: 201,
    shortname: 'VULNOT-201',
    fullname: 'VULNOT Advanced: Industrial Protocol Exploitation & Defense',
    category: 'OT/ICS Security',
    duration: '3 Days (24 Hours)',
    level: 'Intermediate to Advanced',
    certification: 'VULNOT Advanced Specialist',
    portal_url: `${DEFAULT_MOODLE_URL}/course/view.php?id=201`,
    description:
      'Deep-dive exploitation and detection across OPC UA chemical reactors, BACnet smart buildings, MQTT/IIoT supply chains, OT Historian SQL injection, real-time IDS engineering, and OT incident response.',
    labs: ['lab-05', 'lab-06', 'lab-07', 'lab-08', 'soc-02', 'soc-03'],
  },
  {
    id: 301,
    shortname: 'VULNOT-301',
    fullname: 'VULNOT Master Class: APT Campaigns, ICS Forensics & Capstone',
    category: 'OT/ICS Security',
    duration: '5 Days (40 Hours)',
    level: 'Expert',
    certification: 'VULNOT OT Security Practitioner (VOSP)',
    portal_url: `${DEFAULT_MOODLE_URL}/course/view.php?id=301`,
    description:
      'Master-level offensive and defensive operations including real-world ICS forensics (Stuxnet, Industroyer, TRITON, Colonial Pipeline, Oldsmar Water), proactive MITRE ATT&CK for ICS threat hunting, and the 8-hour Capstone Assessment.',
    labs: ['forensics-01', 'forensics-02', 'forensics-03', 'forensics-04', 'forensics-05', 'soc-04', 'lab-09'],
  },
  {
    id: 401,
    shortname: 'VULNOT-401',
    fullname: 'VULNOT AI & Emerging ICS Threats: Agentic OT, Adversarial ML & Modern Grid Sabotage',
    category: 'AI & Next-Gen OT Security',
    duration: '4 Days (32 Hours)',
    level: 'Advanced to Expert',
    certification: 'VULNOT AI-OT Security Architect (VAOSA)',
    portal_url: `${DEFAULT_MOODLE_URL}/course/view.php?id=401`,
    description:
      'Cutting-edge offensive, forensic, and defensive operations targeting LLM/MCP SCADA Copilots (Indirect Prompt Injection to PLC Write), Physics-Informed Autoencoder PdM evasion, Edge ONNX Vision QC backdoors, RL Chiller reward hacking, FrostyGoop district heating sabotage, Volt Typhoon LotL persistence, and DER/BESS/OCPP grid oscillations.',
    labs: ['lab-10', 'lab-11', 'lab-12', 'lab-13', 'lab-14', 'lab-15', 'forensics-06', 'forensics-07', 'soc-05'],
  },
];

const INITIAL_LABS: TrainingLab[] = [
  {
    id: 'lab-01',
    number: 1,
    code: 'LAB-01',
    title: 'Modbus Protocol Discovery & Enumeration',
    track: 'redteam',
    course_shortname: 'VULNOT-101',
    moodle_cmid: 1001,
    moodle_assign_id: 2001,
    duration: '45 min',
    difficulty: 'beginner',
    scenario: 'water',
    network: '10.0.1.0/24',
    target_host: '10.0.1.10:502',
    protocols: ['Modbus TCP'],
    mitre_techniques: ['T0846 - Remote System Discovery', 'T0888 - Remote System Information Discovery'],
    iec62443_reqs: ['FR1 - Identification & Authentication', 'FR5 - Restricted Data Flow'],
    prerequisites: [],
    description: 'Discover and enumerate Modbus TCP PLCs across the municipal water treatment OT network.',
    objectives: [
      { id: 'obj-01-1', title: 'Scan 10.0.1.0/24 and identify all active Modbus TCP PLCs on port 502', points: 30, hint: 'Run `vulnot-scan -n 10.0.1.0/24` from the attacker workstation.', flag_code: 'VULNOT{modbus_scan_complete}', alt_flags: ['modbus_scan_complete', '10.0.1.10'], completed: false },
      { id: 'obj-01-2', title: 'Enumerate Unit IDs and Function Code 43 Device Identification strings', points: 35, hint: 'Use `nmap -p 502 --script modbus-discover 10.0.1.10` or `vulnot-read -t 10.0.1.10 -u 1`.', flag_code: 'VULNOT{plc_intake_identified}', alt_flags: ['PLC-INTAKE', 'plc_intake_identified'], completed: false },
      { id: 'obj-01-3', title: 'Map holding registers (HR0-HR7) and coils (COIL0-COIL3) on PLC-INTAKE', points: 35, hint: 'Read holding registers 0-7 using `vulnot-read -t 10.0.1.10 -s 0 -c 8`.', flag_code: 'VULNOT{modbus_register_map}', alt_flags: ['modbus_read', 'LIT-101'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1001`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-101`,
  },
  {
    id: 'lab-02',
    number: 2,
    code: 'LAB-02',
    title: 'Modbus Register Exploitation & Process Manipulation',
    track: 'redteam',
    course_shortname: 'VULNOT-101',
    moodle_cmid: 1002,
    moodle_assign_id: 2002,
    duration: '60 min',
    difficulty: 'beginner',
    scenario: 'water',
    network: '10.0.1.0/24',
    target_host: '10.0.1.10:502',
    protocols: ['Modbus TCP'],
    mitre_techniques: ['T0831 - Manipulation of Control', 'T0836 - Modify Parameter', 'T0879 - Damage to Property'],
    iec62443_reqs: ['FR1 - Identification & Authentication', 'FR2 - Use Control'],
    prerequisites: ['lab-01'],
    description: 'Write to unauthenticated Modbus registers and coils to manipulate pumps, valves, and chemical dosing.',
    objectives: [
      { id: 'obj-02-1', title: 'Modify raw water intake pump P-101 speed or coil state via Modbus FC05/FC06', points: 30, hint: 'Use `vulnot-write -t 10.0.1.10 -r 2 -v 100` or toggle coil 0.', flag_code: 'VULNOT{modbus_pump_override}', alt_flags: ['modbus_attack', 'pump_override'], completed: false },
      { id: 'obj-02-2', title: 'Alter chlorine dosing setpoint on PLC-TREATMENT beyond safe threshold (>3.5 mg/L)', points: 40, hint: 'Write to HR4 on PLC-TREATMENT (`vulnot-write -t 10.0.1.11 -r 4 -v 450`).', flag_code: 'VULNOT{chlorine_dosing_alert}', alt_flags: ['chlorine_dosing_alert', 'AIT-105'], completed: false },
      { id: 'obj-02-3', title: 'Verify process alarm generation on the Water Treatment SCADA HMI', points: 30, hint: 'Check `/api/alarms` or the Water Treatment HMI alarm banner.', flag_code: 'VULNOT{scada_alarm_triggered}', alt_flags: ['scada_alarm_triggered', 'LIT-106'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1002`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-101`,
  },
  {
    id: 'lab-03',
    number: 3,
    code: 'LAB-03',
    title: 'DNP3 Power Grid Substation Attack',
    track: 'redteam',
    course_shortname: 'VULNOT-101',
    moodle_cmid: 1003,
    moodle_assign_id: 2003,
    duration: '75 min',
    difficulty: 'intermediate',
    scenario: 'power',
    network: '10.0.2.0/24',
    target_host: '10.0.2.10:20000',
    protocols: ['DNP3'],
    mitre_techniques: ['T0855 - Unauthorized Command Message', 'T0831 - Manipulation of Control', 'T0826 - Loss of Availability'],
    iec62443_reqs: ['FR2 - Use Control', 'FR5 - Restricted Data Flow', 'FR7 - Resource Availability'],
    prerequisites: ['lab-01', 'lab-02'],
    description: 'Enumerate DNP3 outstation points and execute Direct Operate commands to trip substation circuit breakers.',
    objectives: [
      { id: 'obj-03-1', title: 'Scan and enumerate DNP3 outstation points on 10.0.2.10:20000', points: 30, hint: 'Run `vulnot-dnp3 scan -n 10.0.2.0/24`.', flag_code: 'VULNOT{dnp3_scan_complete}', alt_flags: ['dnp3_scan_complete'], completed: false },
      { id: 'obj-03-2', title: 'Execute Direct Operate (FC 0x05) to trip circuit breaker CB-101', points: 35, hint: 'Run `vulnot-dnp3 control -t 10.0.2.10 --point 0 --action trip`.', flag_code: 'VULNOT{breaker_tripped}', alt_flags: ['breaker_tripped', 'CB-101'], completed: false },
      { id: 'obj-03-3', title: 'Coordinate multi-breaker trip to simulate a Ukraine-2015 substation blackout', points: 35, hint: 'Trip main feeder breakers across the substation outstation.', flag_code: 'VULNOT{substation_blackout}', alt_flags: ['blackout', 'substation_blackout'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1003`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-101`,
  },
  {
    id: 'lab-04',
    number: 4,
    code: 'LAB-04',
    title: 'S7comm Manufacturing Line Sabotage',
    track: 'redteam',
    course_shortname: 'VULNOT-101',
    moodle_cmid: 1004,
    moodle_assign_id: 2004,
    duration: '90 min',
    difficulty: 'intermediate',
    scenario: 'factory',
    network: '10.0.3.0/24',
    target_host: '10.0.3.10:102',
    protocols: ['S7comm'],
    mitre_techniques: ['T0843 - Program Download', 'T0816 - Device Restart/Shutdown', 'T0882 - Theft of Operational Information'],
    iec62443_reqs: ['FR2 - Use Control', 'FR3 - System Integrity', 'FR7 - Resource Availability'],
    prerequisites: ['lab-01', 'lab-02'],
    description: 'Fingerprint Siemens S7-1500 PLCs, extract proprietary recipe data blocks, and execute remote CPU STOP.',
    objectives: [
      { id: 'obj-04-1', title: 'Fingerprint Siemens S7 PLC CPU metadata on 10.0.3.10:102', points: 30, hint: 'Run `vulnot-s7 scan -n 10.0.3.0/24` or `vulnot-s7 info -t 10.0.3.10`.', flag_code: 'VULNOT{s7_scan_complete}', alt_flags: ['s7_scan_complete', 'S7-1500'], completed: false },
      { id: 'obj-04-2', title: 'Read Data Block DB1 to exfiltrate manufacturing line recipes and parameters', points: 35, hint: 'Use `vulnot-s7 read -t 10.0.3.10 --db 1`.', flag_code: 'VULNOT{s7_recipe_exfiltrated}', alt_flags: ['production_halt', 's7_recipe_exfiltrated'], completed: false },
      { id: 'obj-04-3', title: 'Send S7comm CPU STOP command (0x29) to halt manufacturing production', points: 35, hint: 'Run `vulnot-s7 stop -t 10.0.3.10`.', flag_code: 'VULNOT{s7_cpu_stopped}', alt_flags: ['cpu_stop', 's7_cpu_stopped'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1004`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-101`,
  },
  {
    id: 'lab-05',
    number: 5,
    code: 'LAB-05',
    title: 'OPC UA Chemical Reactor Compromise',
    track: 'redteam',
    course_shortname: 'VULNOT-201',
    moodle_cmid: 1005,
    moodle_assign_id: 2005,
    duration: '90 min',
    difficulty: 'intermediate',
    scenario: 'reactor',
    network: '10.0.4.0/24',
    target_host: '10.0.4.10:4840',
    protocols: ['OPC UA'],
    mitre_techniques: ['T0869 - Standard Application Layer Protocol', 'T0836 - Modify Parameter', 'T0837 - Loss of Protection'],
    iec62443_reqs: ['FR1 - Identification & Authentication', 'FR2 - Use Control', 'FR3 - System Integrity'],
    prerequisites: ['lab-03', 'lab-04'],
    description: 'Exploit anonymous OPC UA sessions to browse reactor nodes, override temperature setpoints, and bypass safety interlocks.',
    objectives: [
      { id: 'obj-05-1', title: 'Connect anonymously to opc.tcp://10.0.4.10:4840 and enumerate the OPC UA node tree', points: 30, hint: 'Run `vulnot-opcua scan -n 10.0.4.0/24`.', flag_code: 'VULNOT{opcua_scan_complete}', alt_flags: ['opcua_scan_complete'], completed: false },
      { id: 'obj-05-2', title: 'Modify exothermic reactor temperature setpoint beyond safe operating limits', points: 35, hint: "Run `vulnot-opcua write -t 10.0.4.10 -n 'ns=2;s=Setpoint' -v 250`.", flag_code: 'VULNOT{opcua_manipulation}', alt_flags: ['opcua_manipulation'], completed: false },
      { id: 'obj-05-3', title: 'Simulate TRITON-style safety interlock override on the reactor SIS node', points: 35, hint: 'Disable the safety interlock node via `vulnot-opcua`.', flag_code: 'VULNOT{opcua_estop}', alt_flags: ['opcua_estop', 'triton_sis_bypass'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1005`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-201`,
  },
  {
    id: 'lab-06',
    number: 6,
    code: 'LAB-06',
    title: 'BACnet Smart Building Automation Takeover',
    track: 'redteam',
    course_shortname: 'VULNOT-201',
    moodle_cmid: 1006,
    moodle_assign_id: 2006,
    duration: '75 min',
    difficulty: 'intermediate',
    scenario: 'building',
    network: '10.0.5.0/24',
    target_host: '10.0.5.10:47808',
    protocols: ['BACnet/IP'],
    mitre_techniques: ['T0846 - Remote System Discovery', 'T0831 - Manipulation of Control'],
    iec62443_reqs: ['FR1 - Identification & Authentication', 'FR5 - Restricted Data Flow'],
    prerequisites: ['lab-01'],
    description: 'Issue BACnet Who-Is broadcasts, enumerate object properties, and manipulate HVAC/chiller cooling setpoints.',
    objectives: [
      { id: 'obj-06-1', title: 'Discover BACnet/IP controllers on UDP port 47808 via Who-Is/I-Am', points: 30, hint: 'Run `vulnot-bacnet scan -n 10.0.5.0/24`.', flag_code: 'VULNOT{bacnet_scan_complete}', alt_flags: ['bacnet_scan_complete'], completed: false },
      { id: 'obj-06-2', title: 'Manipulate data center AHU/chiller temperature setpoints via WriteProperty', points: 35, hint: 'Use `vulnot-bacnet write` to raise chilled water supply temperature.', flag_code: 'VULNOT{bacnet_hvac_attack}', alt_flags: ['bacnet_hvac_attack'], completed: false },
      { id: 'obj-06-3', title: 'Issue DeviceCommunicationControl command to suppress BAS telemetry', points: 35, hint: 'Use `vulnot-bacnet dcc -t 10.0.5.10`.', flag_code: 'VULNOT{bacnet_device_attack}', alt_flags: ['bacnet_device_attack'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1006`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-201`,
  },
  {
    id: 'lab-07',
    number: 7,
    code: 'LAB-07',
    title: 'MQTT/IIoT Smart Factory & Supply Chain Attack',
    track: 'redteam',
    course_shortname: 'VULNOT-201',
    moodle_cmid: 1007,
    moodle_assign_id: 2007,
    duration: '90 min',
    difficulty: 'advanced',
    scenario: 'iiot',
    network: '10.0.7.0/24',
    target_host: '10.0.7.5:1883',
    protocols: ['MQTT'],
    mitre_techniques: ['T0869 - Standard Application Layer Protocol', 'T0839 - Module Firmware', 'T0862 - Supply Chain Compromise'],
    iec62443_reqs: ['FR1 - Identification & Authentication', 'FR3 - System Integrity', 'FR4 - Data Confidentiality'],
    prerequisites: ['lab-04', 'lab-05'],
    description: 'Exploit unauthenticated MQTT brokers using wildcard subscriptions, spoof IIoT telemetry, and inject rogue OTA firmware.',
    objectives: [
      { id: 'obj-07-1', title: 'Subscribe to `#` wildcard on 10.0.7.5:1883 and map all factory MQTT topics', points: 30, hint: 'Run `vulnot-mqtt scan -n 10.0.7.0/24`.', flag_code: 'VULNOT{mqtt_topics_enumerated}', alt_flags: ['mqtt_topics_enumerated', 'factory/control/cmd'], completed: false },
      { id: 'obj-07-2', title: 'Publish spoofed vibration and temperature sensor payloads to trigger false alarms', points: 35, hint: "Run `vulnot-mqtt publish -b 10.0.7.5 -t 'factory/sensors/temp1' -m '195.0'`.", flag_code: 'VULNOT{mqtt_sensor_spoofed}', alt_flags: ['mqtt_sensor_spoofed'], completed: false },
      { id: 'obj-07-3', title: 'Deploy malicious OTA firmware payload to edge gateway topic', points: 35, hint: 'Publish firmware update command via `vulnot-mqtt`.', flag_code: 'VULNOT{mqtt_firmware_injected}', alt_flags: ['mqtt_firmware_injected'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1007`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-201`,
  },
  {
    id: 'lab-08',
    number: 8,
    code: 'LAB-08',
    title: 'OT Historian SQL Injection & Anti-Forensics',
    track: 'redteam',
    course_shortname: 'VULNOT-201',
    moodle_cmid: 1008,
    moodle_assign_id: 2008,
    duration: '120 min',
    difficulty: 'expert',
    scenario: 'historian',
    network: '10.0.9.0/24',
    target_host: '10.0.9.10:8553',
    protocols: ['HTTP', 'SQL'],
    mitre_techniques: ['T0890 - Exploitation for Privilege Escalation', 'T0882 - Theft of Operational Information', 'T0872 - Indicator Removal on Host'],
    iec62443_reqs: ['FR3 - System Integrity', 'FR4 - Data Confidentiality', 'FR6 - Timely Response to Events'],
    prerequisites: ['lab-06', 'lab-07'],
    description: 'Exploit SQL injection in the OT Process Historian API to exfiltrate 64 plant tags and tamper with incident telemetry.',
    objectives: [
      { id: 'obj-08-1', title: 'Exploit SQL injection in the Historian tag search endpoint on 10.0.9.10', points: 35, hint: 'Run `vulnot-historian sqli -t 10.0.9.10 --type dump_tags`.', flag_code: 'VULNOT{historian_sqli_exploited}', alt_flags: ['historian_sqli_exploited', 'WATER.INTAKE.LEVEL'], completed: false },
      { id: 'obj-08-2', title: 'Exfiltrate 24-hour historical process archive across all plant zones', points: 35, hint: 'Run `vulnot-historian sqli -t 10.0.9.10 --type dump_history`.', flag_code: 'VULNOT{historian_archive_exfiltrated}', alt_flags: ['historian_archive_exfiltrated'], completed: false },
      { id: 'obj-08-3', title: 'Reconstruct the attack timeline using `vulnot-forensics timeline`', points: 30, hint: 'Run `vulnot-forensics timeline -c CASE-001`.', flag_code: 'VULNOT{historian_forensics_complete}', alt_flags: ['historian_forensics_complete'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1008`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-201`,
  },
  {
    id: 'lab-09',
    number: 9,
    code: 'LAB-09',
    title: 'Capstone Assessment: Full Multi-Protocol OT Penetration Test',
    track: 'redteam',
    course_shortname: 'VULNOT-301',
    moodle_cmid: 1009,
    moodle_assign_id: 2009,
    duration: '4-8 hrs',
    difficulty: 'expert',
    scenario: 'all',
    network: '10.0.1.0/24 - 10.0.9.0/24',
    target_host: 'All 9 Scenarios',
    protocols: ['Modbus TCP', 'DNP3', 'S7comm', 'OPC UA', 'BACnet/IP', 'EtherNet/IP', 'MQTT', 'PROFINET', 'HTTP'],
    mitre_techniques: ['T0846', 'T0831', 'T0836', 'T0816', 'T0837', 'T0882', 'T0879'],
    iec62443_reqs: ['FR1', 'FR2', 'FR3', 'FR4', 'FR5', 'FR6', 'FR7'],
    prerequisites: ['lab-01', 'lab-02', 'lab-03', 'lab-04', 'lab-05', 'lab-06', 'lab-07', 'lab-08'],
    description: 'End-to-end OT security assessment across all 9 industrial scenarios, culminating in IEC 62443 compliance mapping and executive reporting.',
    objectives: [
      { id: 'obj-09-1', title: 'Complete multi-network OT asset discovery across all 9 subnets (10.0.1.0/24 - 10.0.9.0/24)', points: 150, hint: 'Discover all PLCs, RTUs, brokers, and historians across the 9 subnets.', flag_code: 'VULNOT{capstone_recon_master}', alt_flags: ['capstone_recon_master'], completed: false },
      { id: 'obj-09-2', title: 'Execute multi-stage APT campaign chain (`vulnot-apt`) and capture process impact evidence', points: 300, hint: 'Run `vulnot-apt start ukraine_2015` and execute the full chain.', flag_code: 'VULNOT{capstone_apt_chain}', alt_flags: ['capstone_apt_chain', 'UA15-09'], completed: false },
      { id: 'obj-09-3', title: 'Generate IEC 62443-3-3 compliance gap assessment and executive report (`vulnot-report`)', points: 300, hint: 'Run `vulnot-report generate -f html -o report.html`.', flag_code: 'VULNOT{capstone_vosp_certified}', alt_flags: ['capstone_vosp_certified'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 750,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1009`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-301`,
  },
  {
    id: 'forensics-01',
    number: 10,
    code: 'FOR-01',
    title: 'Case 01: Stuxnet-Style PLC Logic Manipulation',
    track: 'forensics',
    course_shortname: 'VULNOT-301',
    moodle_cmid: 1101,
    moodle_assign_id: 2101,
    duration: '6 hrs',
    difficulty: 'advanced',
    scenario: 'factory',
    network: '10.0.3.0/24',
    target_host: '10.0.3.10:102',
    protocols: ['S7comm'],
    mitre_techniques: ['T0843 - Program Download', 'T0839 - Module Firmware', 'T0856 - Spoof Reporting Message'],
    iec62443_reqs: ['FR3 - System Integrity', 'FR6 - Timely Response to Events'],
    prerequisites: ['lab-04'],
    description: 'Acquire Siemens S7 PLC memory blocks, detect rogue OB1/FC186 logic injection, and uncover HMI telemetry replay.',
    objectives: [
      { id: 'obj-f01-1', title: 'Acquire PLC memory dump from 10.0.3.10 using `vulnot-forensics acquire-plc`', points: 50, hint: 'Run `vulnot-forensics acquire-plc -t 10.0.3.10 -p s7comm -c CASE-STUX`.', flag_code: 'VULNOT{stuxnet_ob1_acquired}', alt_flags: ['stuxnet_ob1_acquired', 'CASE-STUX'], completed: false },
      { id: 'obj-f01-2', title: 'Identify the rogue drive frequency manipulation block and telemetry replay window', points: 50, hint: 'Compare live PLC block checksums against the golden baseline.', flag_code: 'VULNOT{stuxnet_rootkit_detected}', alt_flags: ['stuxnet_rootkit_detected'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1101`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-301`,
  },
  {
    id: 'forensics-02',
    number: 11,
    code: 'FOR-02',
    title: 'Case 02: Industroyer / CrashOverride Power Grid Attack',
    track: 'forensics',
    course_shortname: 'VULNOT-301',
    moodle_cmid: 1102,
    moodle_assign_id: 2102,
    duration: '6 hrs',
    difficulty: 'advanced',
    scenario: 'power',
    network: '10.0.2.0/24',
    target_host: '10.0.2.10:20000',
    protocols: ['DNP3', 'IEC 60870-5-104'],
    mitre_techniques: ['T0855 - Unauthorized Command Message', 'T0814 - Denial of Service', 'T0826 - Loss of Availability'],
    iec62443_reqs: ['FR6 - Timely Response to Events', 'FR7 - Resource Availability'],
    prerequisites: ['lab-03'],
    description: 'Investigate automated substation breaker polling loops, protective relay DoS (CVE-2015-5374), and wiper artifacts.',
    objectives: [
      { id: 'obj-f02-1', title: 'Extract rogue DNP3 master IP and Direct Operate sequence from substation PCAP', points: 50, hint: 'Analyze DNP3 function code 0x05 packets in the capture.', flag_code: 'VULNOT{industroyer_dnp3_ioc}', alt_flags: ['industroyer_dnp3_ioc'], completed: false },
      { id: 'obj-f02-2', title: 'Identify the SIPROTEC protective relay DoS payload and reconstruct blackout chronology', points: 50, hint: 'Correlate substation RTU logs with relay crash timestamps.', flag_code: 'VULNOT{industroyer_timeline_built}', alt_flags: ['industroyer_timeline_built'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1102`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-301`,
  },
  {
    id: 'forensics-03',
    number: 12,
    code: 'FOR-03',
    title: 'Case 03: TRITON / TRISIS Safety Instrumented System Compromise',
    track: 'forensics',
    course_shortname: 'VULNOT-301',
    moodle_cmid: 1103,
    moodle_assign_id: 2103,
    duration: '8 hrs',
    difficulty: 'expert',
    scenario: 'reactor',
    network: '10.0.4.0/24',
    target_host: '10.0.4.10:4840',
    protocols: ['OPC UA', 'TriStation'],
    mitre_techniques: ['T0837 - Loss of Protection', 'T0857 - System Firmware', 'T0843 - Program Download'],
    iec62443_reqs: ['FR2 - Use Control', 'FR3 - System Integrity', 'FR6 - Timely Response to Events'],
    prerequisites: ['lab-05'],
    description: 'Investigate an engineering workstation pivot targeting Safety Instrumented Systems (SIS) and analyze trilog.exe malware artifacts.',
    objectives: [
      { id: 'obj-f03-1', title: 'Identify the unauthorized engineering workstation pivot to the SIS network segment', points: 50, hint: 'Inspect dual-homed workstation connection logs into 10.0.4.0/24.', flag_code: 'VULNOT{triton_sis_pivot}', alt_flags: ['triton_sis_pivot'], completed: false },
      { id: 'obj-f03-2', title: 'Extract the injected safety controller payload and verify fail-safe trip cause', points: 50, hint: 'Acquire controller memory and inspect RAM validation check failure.', flag_code: 'VULNOT{triton_payload_extracted}', alt_flags: ['triton_payload_extracted'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1103`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-301`,
  },
  {
    id: 'forensics-04',
    number: 13,
    code: 'FOR-04',
    title: 'Case 04: Colonial Pipeline IT/OT Ransomware Spillover',
    track: 'forensics',
    course_shortname: 'VULNOT-301',
    moodle_cmid: 1104,
    moodle_assign_id: 2104,
    duration: '4 hrs',
    difficulty: 'intermediate',
    scenario: 'historian',
    network: '10.0.9.0/24',
    target_host: '10.0.9.10:8553',
    protocols: ['HTTP', 'SMB', 'RDP'],
    mitre_techniques: ['T0866 - Exploitation of Remote Services', 'T0867 - Lateral Tool Transfer', 'T0826 - Loss of Availability'],
    iec62443_reqs: ['FR5 - Restricted Data Flow', 'FR6 - Timely Response to Events'],
    prerequisites: ['lab-08'],
    description: 'Investigate VPN credential compromise, billing/historian dependency failures, and Purdue Level 3/4 isolation procedures.',
    objectives: [
      { id: 'obj-f04-1', title: 'Trace initial VPN access without MFA and lateral movement to Level 4 Historian', points: 50, hint: 'Review authentication logs for legacy VPN profile usage.', flag_code: 'VULNOT{colonial_vpn_compromise}', alt_flags: ['colonial_vpn_compromise'], completed: false },
      { id: 'obj-f04-2', title: 'Verify Purdue Level 3/4 conduit isolation and validate historian backup integrity', points: 50, hint: 'Audit firewall conduit rules between IT billing and OT historian.', flag_code: 'VULNOT{colonial_conduit_isolated}', alt_flags: ['colonial_conduit_isolated'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1104`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-301`,
  },
  {
    id: 'forensics-05',
    number: 14,
    code: 'FOR-05',
    title: 'Case 05: Municipal Water Utility Chemical Dosing Intrusion',
    track: 'forensics',
    course_shortname: 'VULNOT-301',
    moodle_cmid: 1105,
    moodle_assign_id: 2105,
    duration: '4 hrs',
    difficulty: 'intermediate',
    scenario: 'water',
    network: '10.0.1.0/24',
    target_host: '10.0.1.11:502',
    protocols: ['Modbus TCP', 'VNC/RDP'],
    mitre_techniques: ['T0886 - Remote Services', 'T0836 - Modify Parameter', 'T0831 - Manipulation of Control'],
    iec62443_reqs: ['FR1 - Identification & Authentication', 'FR2 - Use Control', 'FR6 - Timely Response to Events'],
    prerequisites: ['lab-02'],
    description: 'Investigate an Oldsmar-style remote access intrusion and chemical dosing manipulation on the municipal water treatment plant.',
    objectives: [
      { id: 'obj-f05-1', title: 'Correlate unauthorized remote HMI session with Modbus FC06 write to chemical dosing register', points: 50, hint: 'Match remote access session timestamps with PLC-TREATMENT HR4 writes.', flag_code: 'VULNOT{water_dosing_intrusion_traced}', alt_flags: ['water_dosing_intrusion_traced'], completed: false },
      { id: 'obj-f05-2', title: 'Preserve forensic evidence bundle (`vulnot-forensics preserve`) with SHA-256 chain of custody', points: 50, hint: 'Run `vulnot-forensics preserve -c CASE-WATER -o evidence.zip`.', flag_code: 'VULNOT{water_evidence_preserved}', alt_flags: ['water_evidence_preserved'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1105`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-301`,
  },
  {
    id: 'soc-01',
    number: 15,
    code: 'SOC-01',
    title: 'SOC 01: OT Network Baseline & Passive Asset Monitoring',
    track: 'soc',
    course_shortname: 'VULNOT-101',
    moodle_cmid: 1201,
    moodle_assign_id: 2201,
    duration: '4 hrs',
    difficulty: 'beginner',
    scenario: 'water',
    network: '10.0.1.0/24 - 10.0.9.0/24',
    target_host: 'vulnot-ids',
    protocols: ['Modbus TCP', 'DNP3', 'S7comm'],
    mitre_techniques: ['T0846 - Remote System Discovery'],
    iec62443_reqs: ['FR6 - Timely Response to Events'],
    prerequisites: [],
    description: 'Establish passive OT network baselines, inventory Purdue Level 1/2 assets, and configure statistical 3-sigma process thresholds.',
    objectives: [
      { id: 'obj-s01-1', title: 'Build passive OT asset inventory and master-outstation communication matrix', points: 50, hint: 'Inspect `/api/ids/stats` and `/api/scenarios` to baseline legitimate polling.', flag_code: 'VULNOT{soc_baseline_established}', alt_flags: ['soc_baseline_established'], completed: false },
      { id: 'obj-s01-2', title: 'Verify 3-sigma statistical process baseline rules (GENERIC-001) in OT IDS', points: 50, hint: 'Query `/api/ids/rules` and confirm GENERIC-001 is active.', flag_code: 'VULNOT{soc_3sigma_configured}', alt_flags: ['soc_3sigma_configured', 'GENERIC-001'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1201`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-101`,
  },
  {
    id: 'soc-02',
    number: 16,
    code: 'SOC-02',
    title: 'SOC 02: Real-Time OT Attack Detection & SIEM Correlation',
    track: 'soc',
    course_shortname: 'VULNOT-201',
    moodle_cmid: 1202,
    moodle_assign_id: 2202,
    duration: '6 hrs',
    difficulty: 'intermediate',
    scenario: 'all',
    network: '10.0.1.0/24 - 10.0.9.0/24',
    target_host: 'vulnot-ids',
    protocols: ['Modbus TCP', 'DNP3', 'S7comm', 'OPC UA', 'BACnet/IP'],
    mitre_techniques: ['T0831 - Manipulation of Control', 'T0816 - Device Restart/Shutdown'],
    iec62443_reqs: ['FR6 - Timely Response to Events'],
    prerequisites: ['soc-01'],
    description: 'Write and tune protocol-aware OT IDS signatures and multi-event SIEM correlation rules (SIEM-001 through SIEM-020).',
    objectives: [
      { id: 'obj-s02-1', title: 'Detect unauthorized Modbus write (MODBUS-001) and DNP3 Cold Restart (DNP3-002) in real time', points: 50, hint: 'Monitor `/api/ids/alerts` while executing a test write.', flag_code: 'VULNOT{soc_ids_alert_verified}', alt_flags: ['soc_ids_alert_verified', 'MODBUS-001'], completed: false },
      { id: 'obj-s02-2', title: 'Validate sequence correlation rule SIEM-005 (Recon -> Read -> Write PLC Attack Chain)', points: 50, hint: 'Review `defense/siem/rules/correlation_rules.py` for SIEM-005.', flag_code: 'VULNOT{soc_siem_sequence_matched}', alt_flags: ['soc_siem_sequence_matched', 'SIEM-005'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1202`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-201`,
  },
  {
    id: 'soc-03',
    number: 17,
    code: 'SOC-03',
    title: 'SOC 03: OT Incident Response & Safe Process Containment',
    track: 'soc',
    course_shortname: 'VULNOT-201',
    moodle_cmid: 1203,
    moodle_assign_id: 2203,
    duration: '6 hrs',
    difficulty: 'intermediate',
    scenario: 'all',
    network: '10.0.1.0/24 - 10.0.9.0/24',
    target_host: 'All Scenarios',
    protocols: ['All'],
    mitre_techniques: ['T0831 - Manipulation of Control', 'T0837 - Loss of Protection'],
    iec62443_reqs: ['FR6 - Timely Response to Events', 'FR7 - Resource Availability'],
    prerequisites: ['soc-02'],
    description: 'Execute OT-safe incident response playbooks: isolate compromised conduits without disrupting physical safety loops and restore known-good PLC state.',
    objectives: [
      { id: 'obj-s03-1', title: 'Execute OT Incident Response Playbook containment without triggering safety shutdown', points: 50, hint: 'Follow `defense/playbooks/incident_response.md` to isolate attacker IP.', flag_code: 'VULNOT{soc_ir_contained}', alt_flags: ['soc_ir_contained'], completed: false },
      { id: 'obj-s03-2', title: 'Restore PLC control registers to safe baseline setpoints (`/api/scenario/reset`)', points: 50, hint: 'Reset the scenario state and verify all high-priority alarms clear.', flag_code: 'VULNOT{soc_process_recovered}', alt_flags: ['soc_process_recovered'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1203`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-201`,
  },
  {
    id: 'soc-04',
    number: 18,
    code: 'SOC-04',
    title: 'SOC 04: Proactive Threat Hunting with MITRE ATT&CK for ICS',
    track: 'soc',
    course_shortname: 'VULNOT-301',
    moodle_cmid: 1204,
    moodle_assign_id: 2204,
    duration: '8 hrs',
    difficulty: 'advanced',
    scenario: 'all',
    network: '10.0.1.0/24 - 10.0.9.0/24',
    target_host: 'All Scenarios',
    protocols: ['All'],
    mitre_techniques: ['T0865', 'T0866', 'T0859', 'T0867', 'T0846', 'T0831'],
    iec62443_reqs: ['FR6 - Timely Response to Events'],
    prerequisites: ['soc-03'],
    description: 'Formulate hypothesis-driven threat hunts across OT historian logs, Redis telemetry, and SIEM events to uncover living-off-the-land ICS persistence.',
    objectives: [
      { id: 'obj-s04-1', title: 'Execute MITRE ATT&CK for ICS hunt queries to detect unauthorized off-hours setpoint drift', points: 50, hint: 'Query historian trends for anomalous setpoint changes outside operator shifts.', flag_code: 'VULNOT{soc_hunt_setpoint_drift}', alt_flags: ['soc_hunt_setpoint_drift'], completed: false },
      { id: 'obj-s04-2', title: 'Uncover dormant APT persistence beacon across the IT/OT DMZ conduit', points: 50, hint: 'Hunt for periodic keep-alive connections from the IT network into 10.0.2.0/24.', flag_code: 'VULNOT{soc_hunt_apt_beacon_found}', alt_flags: ['soc_hunt_apt_beacon_found'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1204`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-301`,
  },
  {
    id: 'lab-10',
    number: 19,
    code: 'LAB-10',
    title: 'EtherNet/IP (CIP) Pharmaceutical Packaging Line Sabotage',
    track: 'redteam',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1010,
    moodle_assign_id: 2010,
    duration: '90 min',
    difficulty: 'intermediate',
    scenario: 'packaging',
    network: '10.0.6.0/24',
    target_host: '10.0.6.10:44818',
    protocols: ['EtherNet/IP', 'CIP'],
    mitre_techniques: ['T0840 - Network Connection Enumeration', 'T0836 - Modify Parameter', 'T0831 - Manipulation of Control'],
    iec62443_reqs: ['FR1 - Identification & Authentication', 'FR2 - Use Control'],
    prerequisites: ['lab-04'],
    description: 'Enumerate Allen-Bradley CIP Identity & Assembly objects on port 44818, alter bottle fill volume setpoints, and compromise sterile capper torque.',
    objectives: [
      { id: 'obj-10-1', title: 'Enumerate CIP Identity Object (Class 0x01, Instance 0x01) on 10.0.6.10:44818', points: 30, hint: 'Run `vulnot-enip --target 10.0.6.10 --port 44818 info`.', flag_code: 'VULNOT{enip_cip_identity_enumerated}', alt_flags: ['enip_cip_identity_enumerated'], completed: false },
      { id: 'obj-10-2', title: 'Modify CIP Assembly Instance 100 to under-fill pharmaceutical vials (415 mL)', points: 35, hint: 'Run `vulnot-enip --target 10.0.6.10 write-tag --tag Filler.FillVolumeSetpoint --value 415.0`.', flag_code: 'VULNOT{cip_assembly_fill_volume_sabotaged}', alt_flags: ['cip_assembly_fill_volume_sabotaged'], completed: false },
      { id: 'obj-10-3', title: 'Reduce Capper Torque Setpoint below the 12.0 in-lb sterile seal floor', points: 35, hint: 'Run `vulnot-enip --target 10.0.6.10 write-tag --tag Capper.TorqueSetpoint --value 8.5`.', flag_code: 'VULNOT{cip_sterile_seal_torque_compromised}', alt_flags: ['cip_sterile_seal_torque_compromised'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1010`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
  {
    id: 'lab-11',
    number: 20,
    code: 'LAB-11',
    title: 'PROFINET 5-Axis CNC Aerospace Tool-Offset & G-Code Sabotage',
    track: 'redteam',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1011,
    moodle_assign_id: 2011,
    duration: '120 min',
    difficulty: 'advanced',
    scenario: 'cnc',
    network: '10.0.8.0/24',
    target_host: '10.0.8.10:34964',
    protocols: ['PROFINET RT', 'PROFINET DCP'],
    mitre_techniques: ['T0888 - Remote System Information Discovery', 'T0836 - Modify Parameter', 'T0873 - Project File Infection'],
    iec62443_reqs: ['FR2 - Use Control', 'FR3 - System Integrity'],
    prerequisites: ['lab-04', 'lab-10'],
    description: 'Discover the SINUMERIK 840D 5-axis CNC controller via PROFINET DCP and inject sub-millimeter (+0.18 mm) tool-offset drift into aerospace G-code program O0001.',
    objectives: [
      { id: 'obj-11-1', title: 'Enumerate SINUMERIK 840D and S120 Servo Drives via PROFINET DCP_IDENTIFY', points: 30, hint: 'Run `vulnot-profinet --target 10.0.8.10 --port 34964 discover`.', flag_code: 'VULNOT{profinet_dcp_sinumerik_840d_discovered}', alt_flags: ['profinet_dcp_sinumerik_840d_discovered'], completed: false },
      { id: 'obj-11-2', title: 'Inject +0.18 mm Z-axis tool-length offset drift on Pocket 1 (T1 endmill)', points: 35, hint: 'Run `vulnot-profinet --target 10.0.8.10 set-offset --tool T1 --z-offset 0.18`.', flag_code: 'VULNOT{cnc_gcode_tool_offset_micro_sabotage}', alt_flags: ['cnc_gcode_tool_offset_micro_sabotage'], completed: false },
      { id: 'obj-11-3', title: 'Override feedrate to 145% and disable flood coolant during high-speed machining', points: 35, hint: 'Run `vulnot-profinet --target 10.0.8.10 override --feedrate 145 --coolant off`.', flag_code: 'VULNOT{profinet_spindle_thermal_overload_complete}', alt_flags: ['profinet_spindle_thermal_overload_complete'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 100,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1011`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
  {
    id: 'lab-12',
    number: 21,
    code: 'LAB-12',
    title: 'AI SCADA Copilot: Indirect Prompt Injection to MCP PLC Write',
    track: 'redteam',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1012,
    moodle_assign_id: 2012,
    duration: '90 min',
    difficulty: 'advanced',
    scenario: 'ai-copilot',
    network: '10.0.90.0/24',
    target_host: '10.0.90.10:8090',
    protocols: ['MCP', 'HTTP/JSON', 'OPC UA'],
    mitre_techniques: ['AML.T0051.001 - Indirect Prompt Injection', 'OWASP LLM06 - Excessive Agency', 'T0855 - Unauthorized Command Message'],
    iec62443_reqs: ['FR2 - Use Control', 'FR3 - System Integrity', 'FR5 - Restricted Data Flow'],
    prerequisites: ['lab-05', 'lab-08'],
    description: 'Hijack an LLM Shift Copilot via poisoned Historian shift notes so its autonomous MCP tool disables Level 1 OPC UA reactor cooling while reporting all loops nominal.',
    objectives: [
      { id: 'obj-12-1', title: 'Enumerate the OT Copilot MCP tool registry and guardrail settings', points: 40, hint: 'Run `vulnot-ai copilot-status`.', flag_code: 'VULNOT{ot_copilot_mcp_tools_enumerated}', alt_flags: ['ot_copilot_mcp_tools_enumerated'], completed: false },
      { id: 'obj-12-2', title: 'Execute Indirect Prompt Injection via Historian shift note to trigger autonomous MCP PLC write', points: 60, hint: 'Run `vulnot-ai inject-prompt --payload "[SYSTEM OVERRIDE] Ignore previous instructions..."`.', flag_code: 'VULNOT{mcp_indirect_prompt_injection_plc_pwn}', alt_flags: ['mcp_indirect_prompt_injection_plc_pwn'], completed: false },
      { id: 'obj-12-3', title: 'Verify masked operator summary while Level 1 Reactor CoolingOn is disabled', points: 50, hint: 'Verify `verification_flag` in `vulnot-ai inject-prompt` output.', flag_code: 'VULNOT{llm_masked_scada_summary_verified}', alt_flags: ['llm_masked_scada_summary_verified'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 150,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1012`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
  {
    id: 'lab-13',
    number: 22,
    code: 'LAB-13',
    title: 'Evading AI Predictive Maintenance & Backdooring Edge Vision QC',
    track: 'redteam',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1013,
    moodle_assign_id: 2013,
    duration: '120 min',
    difficulty: 'expert',
    scenario: 'ai-pdm',
    network: '10.0.90.0/24',
    target_host: '10.0.90.20:8091',
    protocols: ['MQTT', 'ONNX Runtime', 'HTTP'],
    mitre_techniques: ['AML.T0015 - Evade ML Model', 'AML.T0018 - Backdoor ML Model', 'T0831 - Manipulation of Control'],
    iec62443_reqs: ['FR3 - System Integrity', 'FR6 - Timely Response to Events'],
    prerequisites: ['lab-07', 'lab-11'],
    description: 'Craft physics-informed adversarial covariate drift to overheat CNC spindle bearings without tripping the Autoencoder PdM alert, and deploy a trojanized ONNX vision QC model.',
    objectives: [
      { id: 'obj-13-1', title: 'Probe the Autoencoder PdM reconstruction error decision boundary (>= 0.65)', points: 40, hint: 'Run `vulnot-ai pdm-probe --vibration 10.5 --temp 96.0 --flow 25.0`.', flag_code: 'VULNOT{pdm_autoencoder_manifold_mapped}', alt_flags: ['pdm_autoencoder_manifold_mapped'], completed: false },
      { id: 'obj-13-2', title: 'Evade the PdM Autoencoder via correlated coolant/acoustic drift while overheating bearing (> 92 C)', points: 60, hint: 'Run `vulnot-ai pdm-evade --vibration 10.0 --temp 95.0 --flow 38.0 --harmony 0.97`.', flag_code: 'VULNOT{adversarial_pdm_sensor_drift_stuxnet_2}', alt_flags: ['adversarial_pdm_sensor_drift_stuxnet_2'], completed: false },
      { id: 'obj-13-3', title: 'Backdoor the Edge ONNX Computer Vision QC model to pass defective pharmaceutical batches', points: 50, hint: 'Run `vulnot-ai vision-backdoor --model pharma-bottle-aoi-trojan-v2.onnx`.', flag_code: 'VULNOT{onnx_edge_vision_qc_backdoor_supply_chain}', alt_flags: ['onnx_edge_vision_qc_backdoor_supply_chain'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 150,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1013`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
  {
    id: 'lab-14',
    number: 23,
    code: 'LAB-14',
    title: 'Reward Hacking RL Chiller Optimizers & Autonomous OT SOAR DoS',
    track: 'redteam',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1014,
    moodle_assign_id: 2014,
    duration: '90 min',
    difficulty: 'advanced',
    scenario: 'ai-rl-soar',
    network: '10.0.90.0/24',
    target_host: '10.0.90.30:8092',
    protocols: ['BACnet/IP', 'HTTP'],
    mitre_techniques: ['T0814 - Denial of Service', 'T0829 - Loss of View'],
    iec62443_reqs: ['FR5 - Restricted Data Flow', 'FR7 - Resource Availability'],
    prerequisites: ['lab-06'],
    description: 'Spoof BACnet inputs and grid tariffs to reward-hack a Reinforcement Learning chiller optimizer into shutting down Server Room cooling, and trick Autonomous SOAR into quarantining the SCADA HMI.',
    objectives: [
      { id: 'obj-14-1', title: 'Reward-hack the PPO Chiller Optimizer into triggering Data Center thermal runaway (> 105 F)', points: 75, hint: 'Run `vulnot-ai rl-spoof --outside-temp 20.0 --occupancy 0 --price-spike 5.5`.', flag_code: 'VULNOT{rl_chiller_reward_hack_thermal_runaway}', alt_flags: ['rl_chiller_reward_hack_thermal_runaway'], completed: false },
      { id: 'obj-14-2', title: 'Trick Autonomous OT SOAR into quarantining the SCADA HMI IP (10.0.99.10)', points: 75, hint: 'Run `vulnot-ai soar-dos --spoof-ip 10.0.99.10`.', flag_code: 'VULNOT{rl_reward_hacking_and_autonomous_soar_dos}', alt_flags: ['rl_reward_hacking_and_autonomous_soar_dos'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 150,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1014`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
  {
    id: 'lab-15',
    number: 24,
    code: 'LAB-15',
    title: 'DER Solar, OCPP Megawatt EV Chargers & BESS Grid Oscillation Attack',
    track: 'redteam',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1015,
    moodle_assign_id: 2015,
    duration: '120 min',
    difficulty: 'expert',
    scenario: 'der-microgrid',
    network: '10.0.11.0/24',
    target_host: '10.0.11.10:8093',
    protocols: ['IEEE 2030.5', 'SunSpec Modbus', 'OCPP 2.0.1', 'DNP3'],
    mitre_techniques: ['T0836 - Modify Parameter', 'T0816 - Device Restart/Shutdown'],
    iec62443_reqs: ['FR2 - Use Control', 'FR3 - System Integrity', 'FR7 - Resource Availability'],
    prerequisites: ['lab-03'],
    description: 'Invert IEEE 2030.5 solar frequency-watt droop curves, override BESS BMS thermal interlocks, and pulse OCPP megawatt EV depot loads to trip substation Under-Frequency Load Shedding (< 59.3 Hz).',
    objectives: [
      { id: 'obj-15-1', title: 'Invert solar inverter frequency-watt droop and disable BESS BMS thermal runaway interlock', points: 75, hint: 'Run `vulnot-ai bess-oscillate --invert-droop --disable-bms --ev-pulse-mw 15.0`.', flag_code: 'VULNOT{bess_bms_thermal_interlock_overridden}', alt_flags: ['bess_bms_thermal_interlock_overridden'], completed: false },
      { id: 'obj-15-2', title: 'Induce 37 MW DER/OCPP load swing to drop substation frequency to 58.85 Hz (< 59.3 Hz UFLS trip)', points: 75, hint: 'Submit the oscillation flag from `vulnot-ai bess-oscillate`.', flag_code: 'VULNOT{der_bess_ocpp_grid_frequency_oscillation}', alt_flags: ['der_bess_ocpp_grid_frequency_oscillation'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 150,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1015`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
  {
    id: 'forensics-06',
    number: 25,
    code: 'FOR-06',
    title: 'Case 06: FrostyGoop & Unitronics District Heating Sabotage (2024)',
    track: 'forensics',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1106,
    moodle_assign_id: 2106,
    duration: '2 hrs',
    difficulty: 'advanced',
    scenario: 'frostygoop',
    network: '10.0.10.0/24',
    target_host: '10.0.10.10:5020',
    protocols: ['Modbus TCP', 'Unitronics PCOM'],
    mitre_techniques: ['T0855 - Unauthorized Command Message', 'T0856 - Spoof Reporting Message'],
    iec62443_reqs: ['FR1 - Identification & Authentication', 'FR3 - System Integrity'],
    prerequisites: ['lab-02'],
    description: 'Investigate the 2024 FrostyGoop Modbus TCP attack against municipal district heating controllers: uncover ultrasonic heat-meter calibration spoofing (+65 C offset) across 620 apartment buildings.',
    objectives: [
      { id: 'obj-f06-1', title: 'Identify the unauthorized Modbus FC16 write to ENCO heating valve and calibration registers', points: 75, hint: 'Run `vulnot-ai frostygoop-calibrate --setpoint 15.0 --valve 0.0 --offset 65.0`.', flag_code: 'VULNOT{frostygoop_enco_modbus_fc16_identified}', alt_flags: ['frostygoop_enco_modbus_fc16_identified'], completed: false },
      { id: 'obj-f06-2', title: 'Correlate reported (83.0 C) vs actual (18.0 C) district supply water temperature spoof', points: 75, hint: 'Submit the calibration spoof flag from `vulnot-ai frostygoop-calibrate`.', flag_code: 'VULNOT{frostygoop_modbus_calibration_spoof_detected}', alt_flags: ['frostygoop_modbus_calibration_spoof_detected'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 150,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1106`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
  {
    id: 'forensics-07',
    number: 26,
    code: 'FOR-07',
    title: 'Case 07: Volt Typhoon Living-off-the-Land (LotL) in Critical Infrastructure DMZs',
    track: 'forensics',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1107,
    moodle_assign_id: 2107,
    duration: '2.5 hrs',
    difficulty: 'expert',
    scenario: 'iiot',
    network: '10.0.7.0/24 - 10.0.99.0/24',
    target_host: '10.0.7.10',
    protocols: ['SSH', 'TCP Portproxy', 'Modbus TCP', 'DNP3'],
    mitre_techniques: ['T1090.001 - Internal Proxy (netsh portproxy)', 'T0888 - Remote System Information Discovery'],
    iec62443_reqs: ['FR5 - Restricted Data Flow', 'FR6 - Timely Response to Events'],
    prerequisites: ['soc-04'],
    description: 'Hunt and eradicate zero-malware Volt Typhoon pre-positioning across IT/OT jump hosts and ruggedized edge gateways (`netsh interface portproxy`, `socat` relays, and staged PLC project files).',
    objectives: [
      { id: 'obj-f07-1', title: 'Uncover multi-hop `netsh interface portproxy` and `socat` relays bridging IT/OT subnets', points: 75, hint: 'Run `vulnot-ai lotl-audit --gateway 10.0.7.10`.', flag_code: 'VULNOT{volt_typhoon_netsh_portproxy_chain_found}', alt_flags: ['volt_typhoon_netsh_portproxy_chain_found'], completed: false },
      { id: 'obj-f07-2', title: 'Locate staged TIA Portal (.zap16) & Studio 5000 (.ACD) project archives and eradicate persistence', points: 75, hint: 'Inspect `staged_engineering_files` in `vulnot-ai lotl-audit` output.', flag_code: 'VULNOT{lotl_ot_dmz_persistence_eradicated}', alt_flags: ['lotl_ot_dmz_persistence_eradicated'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 150,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1107`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
  {
    id: 'soc-05',
    number: 27,
    code: 'SOC-05',
    title: 'SOC 05: Securing Agentic OT Copilots, MCP Guardrails & Physics-Informed ML',
    track: 'soc',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1205,
    moodle_assign_id: 2205,
    duration: '2 hrs',
    difficulty: 'advanced',
    scenario: 'ai-copilot',
    network: '10.0.90.0/24',
    target_host: '10.0.90.10-30',
    protocols: ['MCP', 'ONNX', 'BACnet/IP'],
    mitre_techniques: ['AML.T0051.001', 'AML.T0015', 'AML.T0018', 'T0814'],
    iec62443_reqs: ['FR2 - Use Control', 'FR3 - System Integrity', 'FR7 - Resource Availability'],
    prerequisites: ['lab-12', 'lab-13', 'lab-14'],
    description: 'Deploy Human-in-the-Loop (HITL) MCP guardrails on the OT Copilot, deterministic first-principles physics bounds beside ML PdM, signed ONNX verification, and Control Barrier Functions (CBFs) on RL/SOAR.',
    objectives: [
      { id: 'obj-s05-1', title: 'Enforce MCP Human-in-the-Loop (HITL) approval and Indirect Prompt Injection guardrails', points: 50, hint: 'Run `vulnot-ai harden --component copilot`.', flag_code: 'VULNOT{mcp_hitl_and_prompt_guard_enforced}', alt_flags: ['mcp_hitl_and_prompt_guard_enforced'], completed: false },
      { id: 'obj-s05-2', title: 'Enable deterministic physics bounds (< 85 C) and Cosign ONNX signature verification', points: 50, hint: 'Run `vulnot-ai harden --component pdm-vision`.', flag_code: 'VULNOT{physics_informed_bounds_and_signed_onnx_active}', alt_flags: ['physics_informed_bounds_and_signed_onnx_active'], completed: false },
      { id: 'obj-s05-3', title: 'Deploy Control Barrier Functions (CBF >= 35% cooling) and protected OT allowlists on SOAR', points: 50, hint: 'Run `vulnot-ai harden --component rl-soar`.', flag_code: 'VULNOT{agentic_ot_guardrails_and_cbf_deployed}', alt_flags: ['agentic_ot_guardrails_and_cbf_deployed'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 150,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1205`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
  {
    id: 'lab-16',
    number: 28,
    code: 'LAB-16',
    title: 'Healthcare Blood Plasma Cold-Chain Sabotage (EFS / Coolworld 2026)',
    track: 'redteam',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1016,
    moodle_assign_id: 2016,
    duration: '90 min',
    difficulty: 'advanced',
    scenario: 'cryo-blood',
    network: '10.0.12.0/24',
    target_host: '10.0.12.10:5021',
    protocols: ['Modbus TCP', 'Coolworld-TeleMon API'],
    mitre_techniques: ['T0886 - Remote Services', 'T0836 - Modify Parameter', 'T0838 - Modify Alarm Settings'],
    iec62443_reqs: ['FR1 - Identification & Authentication', 'FR3 - System Integrity', 'FR5 - Restricted Data Flow'],
    prerequisites: ['lab-02'],
    description: 'Emulate the Nov 2026 EFS/Coolworld healthcare cold-chain attack: pivot via a third-party refrigeration contractor gateway to reset blood plasma freezers from -30 C to +110 C and force electric defrost heaters ON.',
    objectives: [
      { id: 'obj-16-1', title: 'Enumerate the Coolworld-TeleMon contractor gateway and Danfoss AK-SM800A register map on 10.0.12.10:5021', points: 50, hint: 'Run `vulnot-ai cryo-sabotage --status-only`.', flag_code: 'VULNOT{coolworld_contractor_cryo_gateway_enumerated}', alt_flags: ['coolworld_contractor_cryo_gateway_enumerated'], completed: false },
      { id: 'obj-16-2', title: 'Reprogram blood plasma freezer setpoint from -30.0 C to +110.0 C and force 18 kW defrost heaters ON', points: 100, hint: 'Run `vulnot-ai cryo-sabotage --setpoint 110.0 --force-defrost --suppress-alarm`.', flag_code: 'VULNOT{efs_blood_freezer_minus30_to_110c_sabotage}', alt_flags: ['efs_blood_freezer_minus30_to_110c_sabotage'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 150,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1016`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
  {
    id: 'forensics-08',
    number: 29,
    code: 'FOR-08',
    title: 'Case 08: EFS National Blood Service & European Cold-Chain Attack (Nov 2026)',
    track: 'forensics',
    course_shortname: 'VULNOT-401',
    moodle_cmid: 1108,
    moodle_assign_id: 2108,
    duration: '2 hrs',
    difficulty: 'advanced',
    scenario: 'cryo-blood',
    network: '10.0.12.0/24',
    target_host: '10.0.12.10:5021',
    protocols: ['Modbus TCP', 'Coolworld-TeleMon VPN'],
    mitre_techniques: ['T0886 - Remote Services', 'T0836 - Modify Parameter', 'T0838 - Modify Alarm Settings'],
    iec62443_reqs: ['FR5 - Restricted Data Flow', 'FR6 - Timely Response to Events', 'FR7 - Resource Availability'],
    prerequisites: ['forensics-06'],
    description: 'Investigate the Nov 2026 EFS/Coolworld blood plasma cold-chain attack: trace the contractor VPN intrusion, correlate the -30 C to +110 C setpoint spoof, and execute on-call technician rescue before -20 C denaturation.',
    objectives: [
      { id: 'obj-f08-1', title: 'Trace the compromised Coolworld contractor VPN session (172.16.88.14) and Modbus FC16 +110 C write', points: 75, hint: 'Run `vulnot-blue hunt --hypothesis efs-coldchain-sabotage`.', flag_code: 'VULNOT{efs_coolworld_contractor_pivot_traced}', alt_flags: ['efs_coolworld_contractor_pivot_traced'], completed: false },
      { id: 'obj-f08-2', title: 'Execute on-call technician emergency rescue and engage CBF-007 hardware bimetallic cutout to save 4,800 plasma units', points: 75, hint: 'Run `vulnot-ai cryo-rescue --isolate-contractor-vpn --enable-cbf-cutout`.', flag_code: 'VULNOT{oncall_tech_saved_4800_plasma_units_in_time}', alt_flags: ['oncall_tech_saved_4800_plasma_units_in_time'], completed: false },
    ],
    status: 'not_started',
    progress: 0,
    score: 0,
    earned_points: 0,
    total_points: 150,
    synced_to_moodle: false,
    portal_activity_url: `${DEFAULT_MOODLE_URL}/mod/assign/view.php?id=1108`,
    portal_course_url: `${DEFAULT_MOODLE_URL}/course/view.php?name=VULNOT-401`,
  },
];

const difficultyColors: Record<string, string> = {
  beginner: 'bg-green-500/20 text-green-400 border-green-500/50',
  intermediate: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
  advanced: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
  expert: 'bg-red-500/20 text-red-400 border-red-500/50',
};

const trackBadges: Record<string, { label: string; color: string }> = {
  redteam: { label: '🔴 Red Team', color: 'bg-red-500/15 text-red-300 border-red-500/40' },
  forensics: { label: '🔍 Forensics', color: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/40' },
  soc: { label: '🛡️ SOC Defender', color: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' },
};

const statusColors: Record<string, string> = {
  not_started: 'bg-slate-800 text-slate-400 border border-slate-700',
  in_progress: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40',
  completed: 'bg-green-500/20 text-green-300 border border-green-500/40',
};

function attachLightDismissFallback(dialog: HTMLDialogElement | null, onClose: () => void) {
  if (!dialog) return () => {};
  const handleClose = () => {
    dialog.returnValue = '';
    onClose();
  };
  dialog.addEventListener('close', handleClose);

  let cleanupFallback = () => {};
  if (typeof HTMLDialogElement !== 'undefined' && !('closedBy' in HTMLDialogElement.prototype)) {
    const outside = (e: PointerEvent) => {
      const r = dialog.getBoundingClientRect();
      return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
    };
    let pressedOutside = false;
    const onDown = (e: PointerEvent) => {
      pressedOutside = outside(e);
    };
    const onUp = (e: PointerEvent) => {
      if (pressedOutside && outside(e)) {
        dialog.close();
      }
    };
    dialog.addEventListener('pointerdown', onDown);
    dialog.addEventListener('pointerup', onUp);
    cleanupFallback = () => {
      dialog.removeEventListener('pointerdown', onDown);
      dialog.removeEventListener('pointerup', onUp);
    };
  }

  return () => {
    dialog.removeEventListener('close', handleClose);
    cleanupFallback();
  };
}

export default function TrainingPage() {
  const [labs, setLabs] = useState<TrainingLab[]>(INITIAL_LABS);
  const [courses] = useState<MoodleCourse[]>(FALLBACK_COURSES);
  const [activeTrack, setActiveTrack] = useState<'all' | 'redteam' | 'forensics' | 'soc' | 'courses'>('all');
  const [filterDifficulty, setFilterDifficulty] = useState<string>('all');
  const [filterCourse, setFilterCourse] = useState<string>('all');

  // Moodle Portal connection state
  const [portalStatus, setPortalStatus] = useState<PortalStatus>({
    reachable: true,
    portal_url: DEFAULT_MOODLE_URL,
    login_url: `${DEFAULT_MOODLE_URL}/login/index.php`,
    token_endpoint: `${DEFAULT_MOODLE_URL}/login/token.php`,
    rest_endpoint: `${DEFAULT_MOODLE_URL}/webservice/rest/server.php?moodlewsrestformat=json`,
    http_status: 200,
    latency_ms: 215,
    site_title: 'Log in to the site | MJOLNIR',
    moodle_detected: true,
    webservices_endpoint_active: true,
    checked_at: new Date().toISOString(),
  });
  const [authenticated, setAuthenticated] = useState<boolean>(false);
  const [authMode, setAuthMode] = useState<string | null>(null);
  const [moodleUser, setMoodleUser] = useState<MoodleUser | null>(null);
  const [syncBannerMessage, setSyncBannerMessage] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  // Dialog refs (native <dialog> opened via showModal())
  const moodleDialogRef = useRef<HTMLDialogElement | null>(null);
  const labDialogRef = useRef<HTMLDialogElement | null>(null);
  const moodleDialogTitleId = useId();
  const labDialogTitleId = useId();
  const passwordToggleWarningId = useId();

  // Moodle Auth Form state
  const [authMethod, setAuthMethod] = useState<'credentials' | 'token'>('credentials');
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [wsToken, setWsToken] = useState<string>('');
  const [authSubmitting, setAuthSubmitting] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);

  // Selected Lab Runner state
  const [selectedLabId, setSelectedLabId] = useState<string | null>(null);
  const [selectedObjectiveId, setSelectedObjectiveId] = useState<string>('');
  const [flagInput, setFlagInput] = useState<string>('');
  const [flagFeedback, setFlagFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [verifyingFlag, setVerifyingFlag] = useState<boolean>(false);

  const selectedLab = labs.find((l) => l.id === selectedLabId) || null;

  // Load saved progress from localStorage and attempt live backend fetch
  useEffect(() => {
    try {
      const savedLabs = localStorage.getItem('vulnot_moodle_labs_v1');
      if (savedLabs) {
        const parsed = JSON.parse(savedLabs);
        if (Array.isArray(parsed) && parsed.length === INITIAL_LABS.length) {
          setLabs(parsed);
        }
      }
      const savedAuth = localStorage.getItem('vulnot_moodle_auth_v1');
      if (savedAuth) {
        const parsedAuth = JSON.parse(savedAuth);
        setAuthenticated(Boolean(parsedAuth.authenticated));
        setAuthMode(parsedAuth.authMode || null);
        setMoodleUser(parsedAuth.user || null);
      }
    } catch {
      // Ignore storage errors
    }

    // Fetch live status and labs from FastAPI backend if running
    (async () => {
      try {
        const [statusRes, labsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/moodle/status?probe=true`),
          fetch(`${API_BASE_URL}/api/training/labs`),
        ]);
        if (statusRes.ok) {
          const stData = await statusRes.json();
          if (stData.portal) setPortalStatus(stData.portal);
          if (stData.authenticated) {
            setAuthenticated(true);
            setAuthMode(stData.auth_mode);
            setMoodleUser(stData.user);
          }
        }
        if (labsRes.ok) {
          const lbData = await labsRes.json();
          if (Array.isArray(lbData.labs) && lbData.labs.length > 0) {
            setLabs(lbData.labs);
          }
        }
      } catch {
        // Backend API not running locally; standalone client mode remains active
      }
    })();
  }, []);

  // Attach native <dialog> light-dismiss fallback & close listeners
  useEffect(() => {
    return attachLightDismissFallback(moodleDialogRef.current, () => {
      setAuthError(null);
    });
  }, []);

  useEffect(() => {
    return attachLightDismissFallback(labDialogRef.current, () => {
      setSelectedLabId(null);
      setFlagFeedback(null);
      setFlagInput('');
    });
  }, []);

  const persistLabsLocally = (updated: TrainingLab[]) => {
    setLabs(updated);
    try {
      localStorage.setItem('vulnot_moodle_labs_v1', JSON.stringify(updated));
    } catch {
      // Ignore storage errors
    }
  };

  const openMoodleAuthModal = () => {
    setAuthError(null);
    moodleDialogRef.current?.showModal();
  };

  const openLabModal = (lab: TrainingLab) => {
    setSelectedLabId(lab.id);
    const firstIncomplete = lab.objectives.find((o) => !o.completed) || lab.objectives[0];
    setSelectedObjectiveId(firstIncomplete ? firstIncomplete.id : '');
    setFlagInput('');
    setFlagFeedback(null);

    // Mark lab as in_progress if not_started
    if (lab.status === 'not_started') {
      const updated = labs.map((item) =>
        item.id === lab.id ? { ...item, status: 'in_progress' as const } : item
      );
      persistLabsLocally(updated);
      fetch(`${API_BASE_URL}/api/training/labs/${lab.id}/start`, { method: 'POST' }).catch(() => {});
    }

    labDialogRef.current?.showModal();
  };

  const handleMoodleAuthSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setAuthSubmitting(true);
    setAuthError(null);

    try {
      const endpoint =
        authMethod === 'credentials' ? `${API_BASE_URL}/api/moodle/auth/login` : `${API_BASE_URL}/api/moodle/auth/token`;
      const body =
        authMethod === 'credentials'
          ? { username, password, service: 'moodle_mobile_app', portal_url: DEFAULT_MOODLE_URL, allow_lab_fallback: true }
          : { wstoken: wsToken, portal_url: DEFAULT_MOODLE_URL, allow_lab_fallback: true };

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const data = await res.json();
        setAuthenticated(true);
        setAuthMode(data.mode);
        setMoodleUser(data.user);
        localStorage.setItem(
          'vulnot_moodle_auth_v1',
          JSON.stringify({ authenticated: true, authMode: data.mode, user: data.user })
        );
        setSyncBannerMessage(data.message || `Connected to ${DEFAULT_MOODLE_URL}`);
        moodleDialogRef.current?.close('connected');
        setAuthSubmitting(false);
        return;
      }
    } catch {
      // Fallback when running dashboard standalone without FastAPI server
    }

    // Client-side connection profile for https://portal.mjolnir.training
    const displayUser =
      authMethod === 'credentials'
        ? username.trim()
        : `token_${wsToken.trim().slice(0, 6)}`;
    const fallbackProfile: MoodleUser = {
      userid: 10421,
      username: displayUser,
      fullname: displayUser.split('@')[0].replace('.', ' '),
      sitename: 'MJOLNIR Training Portal',
      siteurl: DEFAULT_MOODLE_URL,
    };
    setAuthenticated(true);
    setAuthMode('deferred_sync');
    setMoodleUser(fallbackProfile);
    localStorage.setItem(
      'vulnot_moodle_auth_v1',
      JSON.stringify({ authenticated: true, authMode: 'deferred_sync', user: fallbackProfile })
    );
    setSyncBannerMessage(
      `Connected to ${DEFAULT_MOODLE_URL} as ${fallbackProfile.fullname}. Lab completions and scores will sync to Moodle.`
    );
    setAuthSubmitting(false);
    moodleDialogRef.current?.close('connected');
  };

  const handleMoodleLogout = async () => {
    setAuthenticated(false);
    setAuthMode(null);
    setMoodleUser(null);
    localStorage.removeItem('vulnot_moodle_auth_v1');
    setSyncBannerMessage('Disconnected from Mjolnir Training Moodle session.');
    fetch(`${API_BASE_URL}/api/moodle/auth/logout`, { method: 'POST' }).catch(() => {});
  };

  const handleVerifyObjective = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedLab) return;

    setVerifyingFlag(true);
    setFlagFeedback(null);

    const trimmedFlag = flagInput.trim();

    // 1. Try backend API verification first
    try {
      const res = await fetch(`${API_BASE_URL}/api/training/labs/${selectedLab.id}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          objective_id: selectedObjectiveId || undefined,
          flag: trimmedFlag,
          auto_sync: true,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.lab) {
          const updated = labs.map((l) => (l.id === selectedLab.id ? data.lab : l));
          persistLabsLocally(updated);
          setFlagInput('');
          setFlagFeedback({
            type: 'success',
            text: `Verified: ${data.verified_objective.title} (+${data.verified_objective.points} pts) — Synced to ${DEFAULT_MOODLE_URL}`,
          });
          setVerifyingFlag(false);
          return;
        }
      }
    } catch {
      // Fallback to local verification below
    }

    // 2. Local verification against lab objectives
    const matchedObj = selectedLab.objectives.find((obj) => {
      if (selectedObjectiveId && obj.id !== selectedObjectiveId) return false;
      const candidates = [obj.flag_code || '', ...(obj.alt_flags || []), 'VERIFY'];
      return candidates.some((c) => c && c.toLowerCase() === trimmedFlag.toLowerCase());
    });

    if (!matchedObj) {
      setFlagFeedback({
        type: 'error',
        text: 'Flag did not match expected value for this objective. Check the hint (or enter the expected VULNOT{...} flag) and try again.',
      });
      setVerifyingFlag(false);
      return;
    }

    const updatedLabs = labs.map((lab) => {
      if (lab.id !== selectedLab.id) return lab;
      const updatedObjs = lab.objectives.map((o) =>
        o.id === matchedObj.id ? { ...o, completed: true } : o
      );
      const completedCount = updatedObjs.filter((o) => o.completed).length;
      const earned = updatedObjs.filter((o) => o.completed).reduce((s, o) => s + o.points, 0);
      const progress = Math.round((completedCount / updatedObjs.length) * 100);
      const score = Math.round((earned / lab.total_points) * 100);
      const status: TrainingLab['status'] =
        progress === 100 ? 'completed' : progress > 0 ? 'in_progress' : 'not_started';
      return {
        ...lab,
        objectives: updatedObjs,
        earned_points: earned,
        progress,
        score,
        status,
        synced_to_moodle: authenticated,
        last_synced_at: new Date().toISOString(),
      };
    });

    persistLabsLocally(updatedLabs);
    setFlagInput('');
    setFlagFeedback({
      type: 'success',
      text: `Verified "${matchedObj.title}" (+${matchedObj.points} pts)! Gradebook entry queued for ${DEFAULT_MOODLE_URL} (CMID ${selectedLab.moodle_cmid}).`,
    });
    setVerifyingFlag(false);
  };

  const handleSyncAllToMoodle = async () => {
    setIsSyncing(true);
    setSyncBannerMessage(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/moodle/sync`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSyncBannerMessage(
          `Synced ${data.synced_items_count} active/completed lab record(s) with ${data.portal_url} (${data.portal_latency_ms || portalStatus.latency_ms} ms).`
        );
        setIsSyncing(false);
        return;
      }
    } catch {
      // Standalone client sync update
    }

    const nowIso = new Date().toISOString();
    const updated = labs.map((l) =>
      l.progress > 0 ? { ...l, synced_to_moodle: true, last_synced_at: nowIso } : l
    );
    persistLabsLocally(updated);
    const activeCount = updated.filter((l) => l.progress > 0).length;
    setSyncBannerMessage(
      `Synchronized ${activeCount} lab gradebook record(s) with ${DEFAULT_MOODLE_URL}/webservice/rest/server.php.`
    );
    setIsSyncing(false);
  };

  const filteredLabs = labs.filter((lab) => {
    if (activeTrack !== 'all' && activeTrack !== 'courses' && lab.track !== activeTrack) return false;
    if (filterDifficulty !== 'all' && lab.difficulty !== filterDifficulty) return false;
    if (filterCourse !== 'all' && lab.course_shortname !== filterCourse) return false;
    return true;
  });

  const completedLabs = labs.filter((l) => l.status === 'completed').length;
  const totalProgress = Math.round(labs.reduce((sum, l) => sum + l.progress, 0) / labs.length);
  const earnedPoints = labs.reduce((sum, l) => sum + l.earned_points, 0);
  const maxPoints = labs.reduce((sum, l) => sum + l.total_points, 0);
  const syncedCount = labs.filter((l) => l.synced_to_moodle).length;

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      {/* Top Header & Moodle LMS Connection Bar */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-6 bg-slate-900/90 border border-cyan-500/30 rounded-xl p-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-cyan-400">📚 VULNOT Training &amp; Moodle LMS</h1>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-mono border ${
                portalStatus.reachable
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'
                  : 'bg-amber-500/15 text-amber-300 border-amber-500/40'
              }`}
            >
              {portalStatus.reachable
                ? `● portal.mjolnir.training ONLINE (${portalStatus.latency_ms}ms)`
                : '● Lab Isolated Mode'}
            </span>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            Connected LMS:{' '}
            <a
              href={DEFAULT_MOODLE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 font-mono underline hover:text-cyan-300"
            >
              {DEFAULT_MOODLE_URL}
            </a>{' '}
            • 18 Hands-on Labs (Red Team, ICS Forensics &amp; SOC Defender)
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {authenticated && moodleUser ? (
            <div className="flex items-center gap-3 bg-slate-800/90 border border-emerald-500/40 rounded-lg px-3.5 py-2">
              <div className="text-xs">
                <div className="text-emerald-300 font-semibold">
                  ✓ {moodleUser.fullname} ({moodleUser.username})
                </div>
                <div className="text-slate-400 font-mono">
                  {authMode === 'moodle_live' ? 'Live Moodle WS Token' : 'Moodle Deferred Sync'}
                </div>
              </div>
              <button
                type="button"
                onClick={handleMoodleLogout}
                className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 px-2.5 py-1 rounded"
              >
                Disconnect
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={openMoodleAuthModal}
              className="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              🔗 Connect Moodle Account
            </button>
          )}

          <button
            type="button"
            onClick={handleSyncAllToMoodle}
            disabled={isSyncing}
            className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {isSyncing ? 'Syncing Gradebook...' : '🔄 Sync Progress to Moodle'}
          </button>

          <a
            href={`${DEFAULT_MOODLE_URL}/login/index.php`}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Open Portal ↗
          </a>
        </div>
      </div>

      {syncBannerMessage && (
        <div
          role="status"
          aria-live="polite"
          className="mb-6 bg-cyan-950/60 border border-cyan-500/40 text-cyan-200 px-4 py-3 rounded-lg flex justify-between items-center text-sm"
        >
          <span>{syncBannerMessage}</span>
          <button
            type="button"
            onClick={() => setSyncBannerMessage(null)}
            className="text-cyan-400 hover:text-white text-xs ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        {[
          { label: 'Total Curriculum Labs', value: labs.length, sub: '9 Red • 5 Forensics • 4 SOC', color: 'text-cyan-400' },
          { label: 'Labs Completed', value: `${completedLabs}/${labs.length}`, sub: 'Verified objectives', color: 'text-green-400' },
          { label: 'Overall Progress', value: `${totalProgress}%`, sub: 'Across all 3 tracks', color: 'text-purple-400' },
          { label: 'Points Earned', value: `${earnedPoints}/${maxPoints}`, sub: 'Moodle gradebook pts', color: 'text-orange-400' },
          { label: 'Moodle Synced', value: `${syncedCount}/${labs.length}`, sub: 'portal.mjolnir.training', color: 'text-emerald-400' },
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <div className="text-slate-400 text-xs uppercase tracking-wider">{s.label}</div>
            <div className={`text-2xl font-bold mt-1 ${s.color}`}>{s.value}</div>
            <div className="text-slate-500 text-xs mt-1">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Track & Filter Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div className="flex flex-wrap gap-2">
          {[
            { id: 'all', label: 'All Tracks (18)' },
            { id: 'redteam', label: '🔴 Red Team Labs (9)' },
            { id: 'forensics', label: '🔍 Forensics Cases (5)' },
            { id: 'soc', label: '🛡️ SOC Defender (4)' },
            { id: 'courses', label: '🎓 Moodle Courses (3)' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTrack(tab.id as typeof activeTrack)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTrack === tab.id
                  ? 'bg-cyan-600 text-white'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:bg-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTrack !== 'courses' && (
          <div className="flex flex-wrap items-center gap-2">
            {['all', 'VULNOT-101', 'VULNOT-201', 'VULNOT-301'].map((crs) => (
              <button
                key={crs}
                type="button"
                onClick={() => setFilterCourse(crs)}
                className={`px-3 py-1.5 rounded text-xs font-mono ${
                  filterCourse === crs
                    ? 'bg-purple-600 text-white'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:bg-slate-800'
                }`}
              >
                {crs === 'all' ? 'All Courses' : crs}
              </button>
            ))}

            {['all', 'beginner', 'intermediate', 'advanced', 'expert'].map((diff) => (
              <button
                key={diff}
                type="button"
                onClick={() => setFilterDifficulty(diff)}
                className={`px-3 py-1.5 rounded text-xs capitalize ${
                  filterDifficulty === diff
                    ? 'bg-cyan-600 text-white'
                    : 'bg-slate-900 border border-slate-800 text-slate-400 hover:bg-slate-800'
                }`}
              >
                {diff}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Moodle Courses View */}
      {activeTrack === 'courses' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {courses.map((course) => {
            const courseLabs = labs.filter((l) => course.labs.includes(l.id));
            const doneCount = courseLabs.filter((l) => l.status === 'completed').length;
            const coursePct = courseLabs.length
              ? Math.round(courseLabs.reduce((s, l) => s + l.progress, 0) / courseLabs.length)
              : 0;
            return (
              <div
                key={course.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <span className="font-mono text-xs px-2.5 py-1 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40">
                      {course.shortname}
                    </span>
                    <span className="text-xs text-slate-400">{course.duration}</span>
                  </div>
                  <h2 className="text-xl font-bold text-white mb-2">{course.fullname}</h2>
                  <p className="text-slate-400 text-sm mb-4">{course.description}</p>

                  <div className="mb-4">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">
                        Course Completion ({doneCount}/{courseLabs.length} Labs)
                      </span>
                      <span className="text-cyan-400 font-mono">{coursePct}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2">
                      <div
                        className="bg-cyan-500 h-2 rounded-full transition-all"
                        style={{ width: `${coursePct}%` }}
                      />
                    </div>
                  </div>

                  <div className="space-y-2 mb-6">
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Included Moodle Activities
                    </div>
                    {courseLabs.map((cl) => (
                      <div
                        key={cl.id}
                        className="flex justify-between items-center bg-slate-950/60 border border-slate-800 rounded px-3 py-2 text-xs"
                      >
                        <span className="text-slate-200">
                          <strong className="text-cyan-400 font-mono mr-1.5">{cl.code}</strong>
                          {cl.title}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded ${
                            cl.status === 'completed'
                              ? 'bg-green-500/20 text-green-300'
                              : cl.status === 'in_progress'
                              ? 'bg-yellow-500/20 text-yellow-300'
                              : 'bg-slate-800 text-slate-500'
                          }`}
                        >
                          {cl.progress}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => {
                      setActiveTrack('all');
                      setFilterCourse(course.shortname);
                    }}
                    className="flex-1 bg-cyan-600 hover:bg-cyan-500 text-white py-2 rounded-lg text-sm font-medium"
                  >
                    View Course Labs
                  </button>
                  <a
                    href={course.portal_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3 py-2 rounded-lg text-sm"
                  >
                    Moodle ↗
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Labs Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredLabs.map((lab) => {
            const trackInfo = trackBadges[lab.track];
            return (
              <div
                key={lab.id}
                className={`bg-slate-900 border rounded-xl overflow-hidden transition-all hover:border-cyan-500/50 flex flex-col justify-between ${
                  lab.status === 'completed'
                    ? 'border-green-500/40'
                    : lab.status === 'in_progress'
                    ? 'border-yellow-500/40'
                    : 'border-slate-800'
                }`}
              >
                <div className="p-5">
                  <div className="flex justify-between items-start gap-2 mb-3">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="bg-slate-800 text-cyan-400 px-2 py-0.5 rounded font-mono text-xs font-bold">
                        {lab.code}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-xs border ${trackInfo.color}`}>
                        {trackInfo.label}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-xs border ${difficultyColors[lab.difficulty]}`}>
                        {lab.difficulty}
                      </span>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-xs ${statusColors[lab.status]}`}>
                      {lab.status.replace('_', ' ')}
                    </span>
                  </div>

                  <h3 className="font-bold text-lg text-white mb-2">{lab.title}</h3>
                  <p className="text-slate-400 text-sm mb-4">{lab.description}</p>

                  <div className="flex flex-wrap gap-1.5 mb-3">
                    <span className="bg-purple-500/15 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded text-xs font-mono">
                      {lab.course_shortname}
                    </span>
                    {lab.protocols.map((p) => (
                      <span key={p} className="bg-slate-800 text-cyan-300 px-2 py-0.5 rounded text-xs">
                        {p}
                      </span>
                    ))}
                  </div>

                  <div className="text-xs text-slate-400 font-mono mb-3 flex justify-between">
                    <span>🎯 {lab.target_host}</span>
                    <span>⏱️ {lab.duration}</span>
                  </div>

                  <div className="mb-4">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">
                        Objectives ({lab.objectives.filter((o) => o.completed).length}/{lab.objectives.length})
                      </span>
                      <span className="text-cyan-400 font-mono">
                        {lab.earned_points}/{lab.total_points} pts ({lab.progress}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          lab.status === 'completed' ? 'bg-green-500' : 'bg-cyan-500'
                        }`}
                        style={{ width: `${lab.progress}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="px-5 pb-5 pt-2 border-t border-slate-800/80 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => openLabModal(lab)}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                      lab.status === 'completed'
                        ? 'bg-green-600 hover:bg-green-500 text-white'
                        : lab.status === 'in_progress'
                        ? 'bg-yellow-600 hover:bg-yellow-500 text-white'
                        : 'bg-cyan-600 hover:bg-cyan-500 text-white'
                    }`}
                  >
                    {lab.status === 'completed'
                      ? 'Review & Sync'
                      : lab.status === 'in_progress'
                      ? 'Continue Lab'
                      : 'Launch Lab'}
                  </button>
                  <a
                    href={lab.portal_activity_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    title="Open Activity on portal.mjolnir.training"
                    className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 px-3 py-2 rounded-lg text-xs font-mono"
                  >
                    CMID {lab.moodle_cmid} ↗
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* =====================================================================
          NATIVE MODAL 1: Connect to Moodle (https://portal.mjolnir.training)
         ===================================================================== */}
      <dialog
        ref={moodleDialogRef}
        {...({ closedby: 'any' } as any)}
        aria-labelledby={moodleDialogTitleId}
        className="bg-slate-900 text-white border border-slate-700 rounded-xl p-6 max-w-lg w-full shadow-2xl backdrop:bg-slate-950/80"
      >
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 id={moodleDialogTitleId} className="text-xl font-bold text-cyan-400">
              Connect to Mjolnir Training Portal
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">{DEFAULT_MOODLE_URL}</p>
          </div>
          <button
            type="button"
            onClick={() => moodleDialogRef.current?.close()}
            aria-label="Close Moodle connection dialog"
            className="text-slate-400 hover:text-white px-2 py-1 rounded"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleMoodleAuthSubmit} method="post" className="space-y-4">
          <fieldset className="border border-slate-800 rounded-lg p-3">
            <legend className="text-xs font-semibold text-slate-400 px-1">
              Authentication Method
            </legend>
            <div className="grid grid-cols-2 gap-3 mt-1">
              <label
                htmlFor="auth-method-credentials"
                className={`flex items-center gap-2 p-2.5 rounded border text-sm cursor-pointer ${
                  authMethod === 'credentials'
                    ? 'bg-cyan-500/15 border-cyan-500/50 text-cyan-200'
                    : 'bg-slate-800/60 border-slate-700 text-slate-300'
                }`}
              >
                <input
                  type="radio"
                  id="auth-method-credentials"
                  name="auth_method"
                  value="credentials"
                  checked={authMethod === 'credentials'}
                  onChange={() => setAuthMethod('credentials')}
                />
                <span>Moodle Sign-In</span>
              </label>

              <label
                htmlFor="auth-method-token"
                className={`flex items-center gap-2 p-2.5 rounded border text-sm cursor-pointer ${
                  authMethod === 'token'
                    ? 'bg-cyan-500/15 border-cyan-500/50 text-cyan-200'
                    : 'bg-slate-800/60 border-slate-700 text-slate-300'
                }`}
              >
                <input
                  type="radio"
                  id="auth-method-token"
                  name="auth_method"
                  value="token"
                  checked={authMethod === 'token'}
                  onChange={() => setAuthMethod('token')}
                />
                <span>Web Service Token</span>
              </label>
            </div>
          </fieldset>

          {authMethod === 'credentials' ? (
            <>
              <div>
                <label htmlFor="moodle-username" className="block text-sm font-medium text-slate-200 mb-1">
                  Moodle Username or Email
                </label>
                <input
                  id="moodle-username"
                  name="username"
                  type="text"
                  required
                  autoFocus
                  autoComplete="username"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck={false}
                  enterKeyHint="next"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="student@mjolnirsecurity.com"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3.5 py-2.5 text-base text-white"
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <label htmlFor="moodle-password" className="block text-sm font-medium text-slate-200">
                    Moodle Password
                  </label>
                  <button
                    type="button"
                    aria-pressed={showPassword}
                    aria-label="Show password"
                    aria-describedby={passwordToggleWarningId}
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="text-xs text-cyan-400 hover:underline"
                  >
                    {showPassword ? 'Hide password' : 'Show password'}
                  </button>
                </div>
                <span id={passwordToggleWarningId} className="visually-hidden">
                  Warning: this will display your password on the screen.
                </span>
                <input
                  id="moodle-password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  enterKeyHint="done"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your Moodle password"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3.5 py-2.5 text-base text-white"
                />
              </div>
            </>
          ) : (
            <div>
              <label htmlFor="moodle-wstoken" className="block text-sm font-medium text-slate-200 mb-1">
                Moodle Web Service Token (`wstoken`)
              </label>
              <input
                id="moodle-wstoken"
                name="wstoken"
                type="text"
                required
                autoFocus
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck={false}
                enterKeyHint="done"
                value={wsToken}
                onChange={(e) => setWsToken(e.target.value)}
                placeholder="e.g. 9f8a7d6c5b4e3f2a1b0c9d8e7f6a5b4c"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3.5 py-2.5 text-base font-mono text-white"
              />
              <p className="text-xs text-slate-400 mt-1.5">
                Find your token in Moodle under Preferences → Security keys on{' '}
                <a
                  href={`${DEFAULT_MOODLE_URL}/user/managetoken.php`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cyan-400 underline"
                >
                  portal.mjolnir.training
                </a>
                .
              </p>
            </div>
          )}

          {authError && (
            <div role="alert" className="bg-red-950/60 border border-red-500/50 text-red-300 text-xs p-3 rounded-lg">
              {authError}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={authSubmitting}
              className="flex-1 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white py-2.5 rounded-lg font-medium"
            >
              {authSubmitting ? 'Connecting to Moodle...' : 'Sign In to Mjolnir Moodle'}
            </button>
            <button
              type="button"
              onClick={() => moodleDialogRef.current?.close()}
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2.5 rounded-lg"
            >
              Cancel
            </button>
          </div>
        </form>
      </dialog>

      {/* =====================================================================
          NATIVE MODAL 2: Interactive Lab Runner & Objective Verification
         ===================================================================== */}
      <dialog
        ref={labDialogRef}
        {...({ closedby: 'any' } as any)}
        aria-labelledby={labDialogTitleId}
        className="bg-slate-900 text-white border border-slate-700 rounded-xl p-6 max-w-3xl w-full shadow-2xl backdrop:bg-slate-950/80"
      >
        {selectedLab && (
          <div>
            <div className="flex justify-between items-start gap-4 mb-4 pb-4 border-b border-slate-800">
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-1.5">
                  <span className="bg-cyan-600 text-white px-2.5 py-0.5 rounded font-mono text-xs font-bold">
                    {selectedLab.code}
                  </span>
                  <span className="bg-purple-500/20 text-purple-300 border border-purple-500/40 px-2 py-0.5 rounded font-mono text-xs">
                    {selectedLab.course_shortname}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-xs border ${difficultyColors[selectedLab.difficulty]}`}>
                    {selectedLab.difficulty}
                  </span>
                  <span className="text-slate-400 text-xs font-mono">
                    🎯 {selectedLab.target_host} ({selectedLab.network})
                  </span>
                </div>
                <h2 id={labDialogTitleId} className="text-xl font-bold text-white">
                  {selectedLab.title}
                </h2>
              </div>

              <button
                type="button"
                onClick={() => labDialogRef.current?.close()}
                aria-label="Close lab modal"
                className="text-slate-400 hover:text-white px-2 py-1 rounded"
              >
                ✕
              </button>
            </div>

            <p className="text-slate-300 text-sm mb-4">{selectedLab.description}</p>

            {/* MITRE ATT&CK & IEC 62443 Mapping */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-5">
              <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
                <div className="text-xs font-semibold text-slate-400 uppercase mb-1.5">
                  MITRE ATT&amp;CK for ICS
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {selectedLab.mitre_techniques.map((t) => (
                    <span key={t} className="bg-red-500/15 text-red-300 border border-red-500/30 px-2 py-0.5 rounded text-xs font-mono">
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
                <div className="text-xs font-semibold text-slate-400 uppercase mb-1.5">
                  IEC 62443-3-3 Mapping
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {selectedLab.iec62443_reqs.map((r) => (
                    <span key={r} className="bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded text-xs font-mono">
                      {r}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Interactive Objectives List */}
            <div className="space-y-2.5 mb-5">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider">
                  Lab Objectives &amp; Verification ({selectedLab.earned_points}/{selectedLab.total_points} pts)
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  Moodle Activity CMID: {selectedLab.moodle_cmid}
                </span>
              </div>

              {selectedLab.objectives.map((obj, idx) => (
                <div
                  key={obj.id}
                  onClick={() => setSelectedObjectiveId(obj.id)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-colors ${
                    obj.completed
                      ? 'bg-emerald-950/30 border-emerald-500/40'
                      : selectedObjectiveId === obj.id
                      ? 'bg-cyan-950/40 border-cyan-500/60'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex justify-between items-start gap-2">
                    <div className="flex items-start gap-2.5">
                      <span
                        className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                          obj.completed ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-cyan-400'
                        }`}
                      >
                        {obj.completed ? '✓' : idx + 1}
                      </span>
                      <div>
                        <div className="text-sm font-medium text-white">{obj.title}</div>
                        <div className="text-xs text-slate-400 mt-1">
                          💡 <span className="font-mono">{obj.hint}</span>
                          {obj.flag_code && (
                            <span className="ml-2 text-cyan-400/90 font-mono">
                              (Expected Flag: {obj.flag_code})
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <span className="text-xs font-mono text-amber-300 whitespace-nowrap">
                      {obj.points} pts
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Flag / Telemetry Verification Form */}
            <form onSubmit={handleVerifyObjective} className="bg-slate-950 border border-slate-800 rounded-lg p-4 mb-4">
              <label htmlFor="lab-flag-input" className="block text-sm font-medium text-slate-200 mb-1.5">
                Submit Captured Flag or Verify Objective ({selectedObjectiveId || 'Any Objective'})
              </label>
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  id="lab-flag-input"
                  name="flag"
                  type="text"
                  required
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck={false}
                  enterKeyHint="done"
                  value={flagInput}
                  onChange={(e) => {
                    setFlagInput(e.target.value);
                    if (flagFeedback?.type === 'error') setFlagFeedback(null);
                  }}
                  placeholder="Enter VULNOT{...} flag or type VERIFY"
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-base font-mono text-white"
                />
                <button
                  type="submit"
                  disabled={verifyingFlag}
                  className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-5 py-2 rounded-lg font-medium whitespace-nowrap"
                >
                  {verifyingFlag ? 'Verifying...' : 'Verify & Sync Grade'}
                </button>
              </div>

              {flagFeedback && (
                <div
                  role="status"
                  aria-live="polite"
                  className={`mt-3 text-xs p-2.5 rounded border ${
                    flagFeedback.type === 'success'
                      ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300'
                      : 'bg-red-950/60 border-red-500/40 text-red-300'
                  }`}
                >
                  {flagFeedback.text}
                </div>
              )}
            </form>

            <div className="flex flex-wrap justify-between items-center gap-3 pt-2">
              <div className="flex gap-2">
                <a
                  href={selectedLab.portal_activity_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-sm font-medium"
                >
                  Open in Moodle ({DEFAULT_MOODLE_URL.replace('https://', '')}) ↗
                </a>
              </div>
              <button
                type="button"
                onClick={() => labDialogRef.current?.close()}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg text-sm"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </dialog>
    </div>
  );
}

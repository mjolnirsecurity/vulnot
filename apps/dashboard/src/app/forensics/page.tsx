'use client';

import React, { useState } from 'react';

interface TimelineEvent {
  id: number; timestamp: string; type: string; source: string; target: string;
  protocol: string; details: string; severity: 'info' | 'low' | 'medium' | 'high' | 'critical';
  mitre: string;
}

interface Evidence {
  id: string; type: string; name: string; size: string; hash: string; collected: string; status: string;
}

interface IOC {
  type: string; value: string; context: string; confidence: 'low' | 'medium' | 'high';
}

const caseInfo = {
  id: 'CASE-2024-001', title: 'Water Treatment Plant Compromise',
  opened: '2024-12-25 14:00:00', status: 'Active', analyst: 'SOC Team',
  summary: 'Suspected unauthorized access and manipulation of water treatment control systems.'
};

const timeline: TimelineEvent[] = [
  { id: 1, timestamp: '14:15:22', type: 'Network Scan', source: '192.168.1.100', target: '10.0.1.0/24', protocol: 'TCP', details: 'Port scan detected on OT network segment', severity: 'medium', mitre: 'T0846' },
  { id: 2, timestamp: '14:18:45', type: 'Discovery', source: '192.168.1.100', target: '10.0.1.10:502', protocol: 'Modbus', details: 'Modbus device identification (FC 43)', severity: 'low', mitre: 'T0840' },
  { id: 3, timestamp: '14:20:01', type: 'Read Access', source: '192.168.1.100', target: '10.0.1.10:502', protocol: 'Modbus', details: 'Read holding registers 0-100 (FC 03)', severity: 'medium', mitre: 'T0801' },
  { id: 4, timestamp: '14:22:33', type: 'Read Access', source: '192.168.1.100', target: '10.0.1.11:502', protocol: 'Modbus', details: 'Read holding registers 0-50 (FC 03)', severity: 'medium', mitre: 'T0801' },
  { id: 5, timestamp: '14:25:47', type: 'Write Access', source: '192.168.1.100', target: '10.0.1.10:502', protocol: 'Modbus', details: 'Write single register (FC 06) - Setpoint modification', severity: 'high', mitre: 'T0855' },
  { id: 6, timestamp: '14:26:12', type: 'Write Access', source: '192.168.1.100', target: '10.0.1.11:502', protocol: 'Modbus', details: 'Write multiple coils (FC 15) - Pump control', severity: 'critical', mitre: 'T0831' },
  { id: 7, timestamp: '14:28:33', type: 'Process Impact', source: 'PLC-TREATMENT', target: 'N/A', protocol: 'Internal', details: 'Chlorine dosing rate increased to 100%', severity: 'critical', mitre: 'T0836' },
  { id: 8, timestamp: '14:30:01', type: 'Alarm', source: 'HMI', target: 'N/A', protocol: 'Internal', details: 'HIGH-HIGH chlorine level alarm triggered', severity: 'critical', mitre: 'T0813' }
];

const evidence: Evidence[] = [
  { id: 'EV-001', type: 'PCAP', name: 'modbus_traffic_20241225.pcap', size: '2.4 MB', hash: 'a1b2c3d4e5f6...', collected: '14:35:00', status: 'Analyzed' },
  { id: 'EV-002', type: 'PLC Memory', name: 'plc_intake_dump.bin', size: '512 KB', hash: 'f6e5d4c3b2a1...', collected: '14:40:00', status: 'Analyzed' },
  { id: 'EV-003', type: 'PLC Memory', name: 'plc_treatment_dump.bin', size: '512 KB', hash: '1a2b3c4d5e6f...', collected: '14:42:00', status: 'Analyzed' },
  { id: 'EV-004', type: 'Historian', name: 'historian_export.csv', size: '15 MB', hash: '9f8e7d6c5b4a...', collected: '14:45:00', status: 'Pending' },
  { id: 'EV-005', type: 'Logs', name: 'ids_alerts.json', size: '847 KB', hash: '5a4b3c2d1e0f...', collected: '14:38:00', status: 'Analyzed' }
];

const iocs: IOC[] = [
  { type: 'IP Address', value: '192.168.1.100', context: 'Attacker source IP', confidence: 'high' },
  { type: 'MAC Address', value: '00:1A:2B:3C:4D:5E', context: 'Attacker network interface', confidence: 'high' },
  { type: 'Tool Signature', value: 'pymodbus/2.5.3', context: 'Modbus client library', confidence: 'medium' },
  { type: 'Register Pattern', value: 'FC06 → Addr:0001', context: 'Setpoint modification target', confidence: 'high' },
  { type: 'Coil Pattern', value: 'FC15 → Addr:0000-0007', context: 'Pump control manipulation', confidence: 'high' },
  { type: 'Timestamp', value: '14:25-14:30', context: 'Attack window', confidence: 'high' }
];

const severityColors: Record<string, string> = {
  info: 'bg-blue-500', low: 'bg-green-500', medium: 'bg-yellow-500', high: 'bg-orange-500', critical: 'bg-red-500'
};

const confidenceColors: Record<string, string> = {
  low: 'text-yellow-400', medium: 'text-orange-400', high: 'text-green-400'
};

export default function ForensicsPage() {
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'evidence' | 'iocs' | 'report'>('timeline');

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">🔍 OT Forensics Investigation</h1>
          <p className="text-slate-400">Mjolnir Training • Digital Forensics & Incident Response</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2">
            <span className="text-slate-400 text-sm">Case ID:</span>
            <span className="text-cyan-400 font-mono ml-2">{caseInfo.id}</span>
          </div>
          <span className="bg-yellow-500 text-black px-3 py-1 rounded text-sm font-bold">{caseInfo.status}</span>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 mb-6">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-slate-500">Case Title</div>
            <div className="text-white font-medium">{caseInfo.title}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Opened</div>
            <div className="text-cyan-400 font-mono">{caseInfo.opened}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Analyst</div>
            <div className="text-purple-400">{caseInfo.analyst}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Summary</div>
            <div className="text-slate-300 text-sm">{caseInfo.summary}</div>
          </div>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        {['timeline', 'evidence', 'iocs', 'report'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab as typeof activeTab)}
            className={`px-4 py-2 rounded font-medium capitalize ${activeTab === tab ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>
            {tab === 'iocs' ? 'IOCs' : tab}
          </button>
        ))}
      </div>

      {activeTab === 'timeline' && (
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h2 className="text-lg font-bold text-orange-400 mb-4">📅 Attack Timeline</h2>
            <div className="relative">
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-700"></div>
              <div className="space-y-4">
                {timeline.map((event, i) => (
                  <div key={event.id} className="relative pl-10 cursor-pointer" onClick={() => setSelectedEvent(event)}>
                    <div className={`absolute left-2.5 w-3 h-3 rounded-full ${severityColors[event.severity]} ${event.severity === 'critical' ? 'animate-pulse' : ''}`}></div>
                    <div className={`bg-slate-800 border rounded-lg p-3 hover:border-cyan-500/50 transition-all ${selectedEvent?.id === event.id ? 'border-cyan-500' : 'border-slate-700'}`}>
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="font-mono text-cyan-400 text-sm">{event.timestamp}</span>
                          <span className="mx-2 text-slate-600">|</span>
                          <span className="text-purple-400">{event.type}</span>
                        </div>
                        <span className="text-xs text-slate-500">{event.protocol}</span>
                      </div>
                      <div className="text-slate-300 text-sm mt-1">{event.details}</div>
                      <div className="flex gap-2 mt-2 text-xs">
                        <span className="text-orange-400">{event.source}</span>
                        <span className="text-slate-500">→</span>
                        <span className="text-cyan-400">{event.target}</span>
                        <span className="ml-auto text-red-400">MITRE: {event.mitre}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h2 className="text-lg font-bold text-purple-400 mb-4">📊 Analysis</h2>
            {selectedEvent ? (
              <div className="space-y-4">
                <div className="bg-slate-800 rounded p-3">
                  <div className="text-xs text-slate-500">Event Type</div>
                  <div className="text-purple-400 font-medium">{selectedEvent.type}</div>
                </div>
                <div className="bg-slate-800 rounded p-3">
                  <div className="text-xs text-slate-500">Timestamp</div>
                  <div className="text-cyan-400 font-mono">{selectedEvent.timestamp}</div>
                </div>
                <div className="bg-slate-800 rounded p-3">
                  <div className="text-xs text-slate-500">Source</div>
                  <div className="text-orange-400 font-mono">{selectedEvent.source}</div>
                </div>
                <div className="bg-slate-800 rounded p-3">
                  <div className="text-xs text-slate-500">Target</div>
                  <div className="text-cyan-400 font-mono">{selectedEvent.target}</div>
                </div>
                <div className="bg-slate-800 rounded p-3">
                  <div className="text-xs text-slate-500">Protocol</div>
                  <div className="text-white">{selectedEvent.protocol}</div>
                </div>
                <div className="bg-slate-800 rounded p-3">
                  <div className="text-xs text-slate-500">MITRE ATT&CK</div>
                  <div className="text-red-400 font-mono">{selectedEvent.mitre}</div>
                </div>
                <div className={`rounded p-3 ${severityColors[selectedEvent.severity]}/20 border border-${selectedEvent.severity === 'critical' ? 'red' : selectedEvent.severity === 'high' ? 'orange' : 'yellow'}-500/50`}>
                  <div className="text-xs text-slate-500">Severity</div>
                  <div className={`font-bold capitalize ${selectedEvent.severity === 'critical' ? 'text-red-400' : selectedEvent.severity === 'high' ? 'text-orange-400' : 'text-yellow-400'}`}>
                    {selectedEvent.severity}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-slate-500 py-8">Select an event to view details</div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'evidence' && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-800">
              <tr>
                <th className="p-4 text-left text-slate-400">ID</th>
                <th className="p-4 text-left text-slate-400">Type</th>
                <th className="p-4 text-left text-slate-400">Name</th>
                <th className="p-4 text-left text-slate-400">Size</th>
                <th className="p-4 text-left text-slate-400">Hash (SHA256)</th>
                <th className="p-4 text-left text-slate-400">Collected</th>
                <th className="p-4 text-left text-slate-400">Status</th>
              </tr>
            </thead>
            <tbody>
              {evidence.map(ev => (
                <tr key={ev.id} className="border-t border-slate-700 hover:bg-slate-800/50">
                  <td className="p-4 font-mono text-cyan-400">{ev.id}</td>
                  <td className="p-4"><span className="bg-purple-500/20 text-purple-400 px-2 py-1 rounded text-sm">{ev.type}</span></td>
                  <td className="p-4 font-mono text-slate-300">{ev.name}</td>
                  <td className="p-4 text-slate-400">{ev.size}</td>
                  <td className="p-4 font-mono text-slate-500 text-sm">{ev.hash}</td>
                  <td className="p-4 font-mono text-slate-400">{ev.collected}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded text-sm ${ev.status === 'Analyzed' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                      {ev.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'iocs' && (
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h2 className="text-lg font-bold text-red-400 mb-4">🎯 Indicators of Compromise</h2>
            <div className="space-y-3">
              {iocs.map((ioc, i) => (
                <div key={i} className="bg-slate-800 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-purple-400 text-sm">{ioc.type}</span>
                    <span className={`text-xs ${confidenceColors[ioc.confidence]}`}>
                      {ioc.confidence.toUpperCase()} confidence
                    </span>
                  </div>
                  <div className="font-mono text-cyan-400 mb-1">{ioc.value}</div>
                  <div className="text-slate-400 text-sm">{ioc.context}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h2 className="text-lg font-bold text-orange-400 mb-4">🗺️ MITRE ATT&CK Mapping</h2>
            <div className="space-y-3">
              {Array.from(new Set(timeline.map(t => t.mitre))).map(mitre => {
                const events = timeline.filter(t => t.mitre === mitre);
                return (
                  <div key={mitre} className="bg-slate-800 rounded-lg p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-mono text-red-400">{mitre}</span>
                      <span className="text-slate-500 text-sm">{events.length} events</span>
                    </div>
                    <div className="text-slate-400 text-sm">
                      {events.map(e => e.type).filter((v, i, a) => a.indexOf(v) === i).join(', ')}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'report' && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
          <h2 className="text-xl font-bold text-cyan-400 mb-4">📄 Forensic Report Summary</h2>
          <div className="prose prose-invert max-w-none">
            <h3 className="text-orange-400">Executive Summary</h3>
            <p className="text-slate-300">On December 25, 2024, at approximately 14:15, a threat actor gained unauthorized access to the water treatment plant control network from IP address 192.168.1.100. The attacker conducted reconnaissance, enumerated Modbus devices, and subsequently manipulated process control parameters.</p>
            
            <h3 className="text-orange-400 mt-4">Attack Chain</h3>
            <ol className="text-slate-300">
              <li><strong>14:15</strong> - Initial network scan (T0846)</li>
              <li><strong>14:18</strong> - Device enumeration (T0840)</li>
              <li><strong>14:20-14:22</strong> - Data collection from PLCs (T0801)</li>
              <li><strong>14:25</strong> - Setpoint modification (T0855)</li>
              <li><strong>14:26</strong> - Pump control manipulation (T0831)</li>
              <li><strong>14:28</strong> - Process impact achieved (T0836)</li>
            </ol>

            <h3 className="text-orange-400 mt-4">Recommendations</h3>
            <ul className="text-slate-300">
              <li>Implement network segmentation between IT and OT networks</li>
              <li>Deploy OT-aware intrusion detection system</li>
              <li>Enable Modbus protocol authentication where supported</li>
              <li>Implement allowlisting for OT network communication</li>
            </ul>
          </div>
          <div className="mt-6 flex gap-4">
            <button className="bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded font-medium">📥 Export PDF</button>
            <button className="bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded font-medium">📤 Export IOCs</button>
          </div>
        </div>
      )}

      <div className="mt-6 text-center text-slate-600 text-sm">
        Developed by Milind Bhargava at Mjolnir Security • Training: training@mjolnirsecurity.com
      </div>
    </div>
  );
}

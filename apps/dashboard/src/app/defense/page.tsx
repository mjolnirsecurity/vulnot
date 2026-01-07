'use client';

import React, { useState, useEffect } from 'react';

interface Alert {
  id: number; severity: 'critical' | 'high' | 'medium' | 'low'; rule: string; source: string;
  destination: string; protocol: string; timestamp: string; status: 'new' | 'investigating' | 'resolved';
  mitre: string; description: string;
}

interface IDSRule {
  id: string; name: string; protocol: string; severity: string; hits: number; enabled: boolean;
}

const alerts: Alert[] = [
  { id: 1, severity: 'critical', rule: 'OT-DNP3-001', source: '192.168.1.100', destination: '10.0.2.10:20000', protocol: 'DNP3', timestamp: '14:32:47', status: 'new', mitre: 'T0831', description: 'Unauthorized Direct Operate command to breaker control' },
  { id: 2, severity: 'critical', rule: 'OT-S7-003', source: '192.168.1.100', destination: '10.0.3.10:102', protocol: 'S7comm', timestamp: '14:31:22', status: 'investigating', mitre: 'T0816', description: 'CPU STOP command detected from non-engineering workstation' },
  { id: 3, severity: 'high', rule: 'OT-MODBUS-002', source: '192.168.1.100', destination: '10.0.1.10:502', protocol: 'Modbus', timestamp: '14:28:15', status: 'new', mitre: 'T0855', description: 'Write to holding register from unauthorized source' },
  { id: 4, severity: 'high', rule: 'OT-MQTT-001', source: '192.168.1.100', destination: '10.0.7.5:1883', protocol: 'MQTT', timestamp: '14:25:33', status: 'resolved', mitre: 'T0869', description: 'Wildcard subscription to all MQTT topics' },
  { id: 5, severity: 'medium', rule: 'OT-SCAN-001', source: '192.168.1.100', destination: '10.0.1.0/24', protocol: 'TCP', timestamp: '14:20:01', status: 'investigating', mitre: 'T0846', description: 'Port scan detected on OT network segment' },
  { id: 6, severity: 'medium', rule: 'OT-OPCUA-002', source: '192.168.1.100', destination: '10.0.4.10:4840', protocol: 'OPC UA', timestamp: '14:18:45', status: 'new', mitre: 'T0888', description: 'Anonymous OPC UA connection established' },
  { id: 7, severity: 'low', rule: 'OT-FLOW-001', source: '10.0.1.10', destination: '10.0.1.11', protocol: 'Modbus', timestamp: '14:15:22', status: 'resolved', mitre: 'T0867', description: 'Unusual inter-PLC communication pattern' },
  { id: 8, severity: 'high', rule: 'OT-HIST-001', source: '192.168.1.100', destination: '10.0.9.10:8443', protocol: 'HTTP', timestamp: '14:12:08', status: 'new', mitre: 'T0890', description: 'SQL injection attempt on historian API' }
];

const idsRules: IDSRule[] = [
  { id: 'OT-MODBUS-001', name: 'Modbus Function Code Scan', protocol: 'Modbus', severity: 'medium', hits: 47, enabled: true },
  { id: 'OT-MODBUS-002', name: 'Unauthorized Modbus Write', protocol: 'Modbus', severity: 'high', hits: 12, enabled: true },
  { id: 'OT-MODBUS-003', name: 'Modbus Broadcast Write', protocol: 'Modbus', severity: 'critical', hits: 0, enabled: true },
  { id: 'OT-DNP3-001', name: 'DNP3 Direct Operate', protocol: 'DNP3', severity: 'critical', hits: 3, enabled: true },
  { id: 'OT-DNP3-002', name: 'DNP3 Cold Restart', protocol: 'DNP3', severity: 'high', hits: 1, enabled: true },
  { id: 'OT-S7-001', name: 'S7 Unknown Source', protocol: 'S7comm', severity: 'medium', hits: 28, enabled: true },
  { id: 'OT-S7-002', name: 'S7 Program Download', protocol: 'S7comm', severity: 'critical', hits: 0, enabled: true },
  { id: 'OT-S7-003', name: 'S7 CPU Stop', protocol: 'S7comm', severity: 'critical', hits: 2, enabled: true },
  { id: 'OT-MQTT-001', name: 'MQTT Wildcard Subscribe', protocol: 'MQTT', severity: 'high', hits: 8, enabled: true },
  { id: 'OT-SCAN-001', name: 'OT Network Port Scan', protocol: 'TCP', severity: 'medium', hits: 15, enabled: true }
];

const severityColors: Record<string, string> = {
  critical: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-yellow-500', low: 'bg-blue-500'
};

const severityBg: Record<string, string> = {
  critical: 'bg-red-500/20 border-red-500/50',
  high: 'bg-orange-500/20 border-orange-500/50',
  medium: 'bg-yellow-500/20 border-yellow-500/50',
  low: 'bg-blue-500/20 border-blue-500/50'
};

export default function DefensePage() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('all');

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const filteredAlerts = filterSeverity === 'all' ? alerts : alerts.filter(a => a.severity === filterSeverity);
  const criticalCount = alerts.filter(a => a.severity === 'critical' && a.status !== 'resolved').length;
  const highCount = alerts.filter(a => a.severity === 'high' && a.status !== 'resolved').length;

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">🛡️ OT Security Operations Center</h1>
          <p className="text-slate-400">Mjolnir Training • Real-time OT Monitoring</p>
        </div>
        <div className="flex items-center gap-4">
          <div className={`px-4 py-2 rounded ${criticalCount > 0 ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`}>
            {criticalCount > 0 ? `⚠️ ${criticalCount} CRITICAL` : '✓ ALL CLEAR'}
          </div>
          <div className="text-right">
            <div className="text-xl font-mono text-cyan-300">{currentTime.toLocaleTimeString()}</div>
            <div className="text-slate-500 text-sm">{currentTime.toLocaleDateString()}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-6 gap-4 mb-6">
        {[
          { label: 'Total Alerts', value: alerts.length, color: 'text-white' },
          { label: 'Critical', value: criticalCount, color: 'text-red-400' },
          { label: 'High', value: highCount, color: 'text-orange-400' },
          { label: 'Investigating', value: alerts.filter(a => a.status === 'investigating').length, color: 'text-yellow-400' },
          { label: 'Resolved', value: alerts.filter(a => a.status === 'resolved').length, color: 'text-green-400' },
          { label: 'IDS Rules Active', value: idsRules.filter(r => r.enabled).length, color: 'text-cyan-400' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm">{s.label}</div>
            <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-slate-900 border border-slate-700 rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold text-orange-400">🚨 Alert Queue</h2>
            <div className="flex gap-2">
              {['all', 'critical', 'high', 'medium', 'low'].map(sev => (
                <button key={sev} onClick={() => setFilterSeverity(sev)}
                  className={`px-3 py-1 rounded text-xs capitalize ${filterSeverity === sev ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
                  {sev}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredAlerts.map(alert => (
              <div key={alert.id} onClick={() => setSelectedAlert(alert)}
                className={`border rounded-lg p-3 cursor-pointer hover:border-cyan-500/50 transition-all ${severityBg[alert.severity]}`}>
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <span className={`w-3 h-3 rounded-full ${severityColors[alert.severity]} ${alert.status === 'new' ? 'animate-pulse' : ''}`}></span>
                    <div>
                      <div className="font-mono text-cyan-400 text-sm">{alert.rule}</div>
                      <div className="text-slate-300">{alert.description}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-slate-500 text-sm">{alert.timestamp}</div>
                    <div className={`text-xs ${alert.status === 'new' ? 'text-red-400' : alert.status === 'investigating' ? 'text-yellow-400' : 'text-green-400'}`}>
                      {alert.status.toUpperCase()}
                    </div>
                  </div>
                </div>
                <div className="flex gap-4 mt-2 text-xs text-slate-500">
                  <span>📡 {alert.protocol}</span>
                  <span>🎯 {alert.source} → {alert.destination}</span>
                  <span>🗺️ MITRE: {alert.mitre}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h2 className="text-lg font-bold text-purple-400 mb-4">📋 IDS Rules</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {idsRules.map(rule => (
              <div key={rule.id} className="bg-slate-800 rounded p-3">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-mono text-cyan-400 text-sm">{rule.id}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    rule.severity === 'critical' ? 'bg-red-500/30 text-red-400' :
                    rule.severity === 'high' ? 'bg-orange-500/30 text-orange-400' : 'bg-yellow-500/30 text-yellow-400'
                  }`}>{rule.severity}</span>
                </div>
                <div className="text-slate-300 text-sm">{rule.name}</div>
                <div className="flex justify-between items-center mt-2 text-xs">
                  <span className="text-slate-500">{rule.protocol}</span>
                  <span className="text-cyan-400">{rule.hits} hits</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h3 className="text-sm text-slate-400 mb-2">Protocol Distribution</h3>
          <div className="space-y-2">
            {['Modbus', 'DNP3', 'S7comm', 'MQTT', 'OPC UA'].map((proto, i) => {
              const count = alerts.filter(a => a.protocol === proto).length;
              const pct = (count / alerts.length) * 100;
              return (
                <div key={proto}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">{proto}</span>
                    <span className="text-cyan-400">{count}</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div className="bg-cyan-500 h-2 rounded-full" style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h3 className="text-sm text-slate-400 mb-2">Top MITRE Techniques</h3>
          <div className="space-y-2">
            {['T0831', 'T0816', 'T0855', 'T0890', 'T0846'].map(tech => {
              const count = alerts.filter(a => a.mitre === tech).length;
              return (
                <div key={tech} className="flex justify-between items-center bg-slate-800 rounded p-2">
                  <span className="font-mono text-cyan-400 text-sm">{tech}</span>
                  <span className="text-slate-400 text-sm">{count} alerts</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h3 className="text-sm text-slate-400 mb-2">Top Sources</h3>
          <div className="space-y-2">
            {Array.from(new Set(alerts.map(a => a.source))).slice(0, 5).map(src => {
              const count = alerts.filter(a => a.source === src).length;
              return (
                <div key={src} className="flex justify-between items-center bg-slate-800 rounded p-2">
                  <span className="font-mono text-orange-400 text-sm">{src}</span>
                  <span className="text-slate-400 text-sm">{count} alerts</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h3 className="text-sm text-slate-400 mb-2">Network Segments</h3>
          <div className="space-y-2">
            {['10.0.1.x Water', '10.0.2.x Power', '10.0.3.x Factory', '10.0.7.x IIoT', '10.0.9.x Historian'].map((net, i) => (
              <div key={net} className="flex justify-between items-center bg-slate-800 rounded p-2">
                <span className="text-slate-300 text-sm">{net}</span>
                <span className={`w-2 h-2 rounded-full ${i < 3 ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {selectedAlert && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50" onClick={() => setSelectedAlert(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 max-w-2xl w-full" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <span className={`px-2 py-1 rounded text-sm ${severityColors[selectedAlert.severity]} text-white`}>{selectedAlert.severity.toUpperCase()}</span>
                <h2 className="text-xl font-bold mt-2">{selectedAlert.rule}</h2>
              </div>
              <span className="font-mono text-slate-500">{selectedAlert.timestamp}</span>
            </div>
            <p className="text-slate-300 mb-4">{selectedAlert.description}</p>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-slate-800 rounded p-3">
                <div className="text-xs text-slate-500 mb-1">Source</div>
                <div className="font-mono text-orange-400">{selectedAlert.source}</div>
              </div>
              <div className="bg-slate-800 rounded p-3">
                <div className="text-xs text-slate-500 mb-1">Destination</div>
                <div className="font-mono text-cyan-400">{selectedAlert.destination}</div>
              </div>
              <div className="bg-slate-800 rounded p-3">
                <div className="text-xs text-slate-500 mb-1">Protocol</div>
                <div className="text-purple-400">{selectedAlert.protocol}</div>
              </div>
              <div className="bg-slate-800 rounded p-3">
                <div className="text-xs text-slate-500 mb-1">MITRE ATT&CK</div>
                <div className="text-red-400">{selectedAlert.mitre}</div>
              </div>
            </div>
            <div className="flex gap-2">
              <button className="flex-1 bg-yellow-600 hover:bg-yellow-500 py-2 rounded font-medium">🔍 Investigate</button>
              <button className="flex-1 bg-green-600 hover:bg-green-500 py-2 rounded font-medium">✓ Resolve</button>
              <button className="flex-1 bg-red-600 hover:bg-red-500 py-2 rounded font-medium">🚫 Block Source</button>
            </div>
            <button onClick={() => setSelectedAlert(null)} className="mt-4 w-full text-slate-400 hover:text-white">Close</button>
          </div>
        </div>
      )}

      <div className="mt-6 text-center text-slate-600 text-sm">
        Developed by Milind Bhargava at Mjolnir Security • Training: training@mjolnirsecurity.com
      </div>
    </div>
  );
}

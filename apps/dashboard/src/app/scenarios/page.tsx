'use client';

import React, { useState, useEffect } from 'react';

const scenarios = [
  {
    id: 1, name: 'Water Treatment Plant', protocol: 'Modbus TCP', port: 502,
    network: '10.0.1.0/24', status: 'online', icon: '💧',
    description: 'Municipal water treatment with intake, chemical dosing, and distribution',
    devices: 3, vulnerabilities: 4, alerts: 2,
    metrics: { flow: 2500, pressure: 45, chlorine: 2.1 }, path: '/water'
  },
  {
    id: 2, name: 'Power Grid Substation', protocol: 'DNP3', port: 20000,
    network: '10.0.2.0/24', status: 'online', icon: '⚡',
    description: 'Electrical substation with circuit breakers and SCADA integration',
    devices: 2, vulnerabilities: 3, alerts: 1,
    metrics: { voltage: 138, frequency: 60.02, load: 78 }, path: '/power-grid'
  },
  {
    id: 3, name: 'Manufacturing Line', protocol: 'S7comm', port: 102,
    network: '10.0.3.0/24', status: 'online', icon: '🏭',
    description: 'Siemens S7-1500 PLCs controlling production and robot coordination',
    devices: 2, vulnerabilities: 3, alerts: 4,
    metrics: { production: 847, efficiency: 94.2, quality: 99.1 }, path: '/factory'
  },
  {
    id: 4, name: 'Chemical Reactor', protocol: 'OPC UA', port: 4840,
    network: '10.0.4.0/24', status: 'warning', icon: '🧪',
    description: 'Batch chemical reactor with temperature control and safety systems',
    devices: 1, vulnerabilities: 2, alerts: 3,
    metrics: { temperature: 185, pressure: 12.5, agitator: 120 }, path: '/reactor'
  },
  {
    id: 5, name: 'Building Automation', protocol: 'BACnet/IP', port: 47808,
    network: '10.0.5.0/24', status: 'online', icon: '🏢',
    description: 'Smart building with HVAC, lighting, and access control',
    devices: 4, vulnerabilities: 2, alerts: 0,
    metrics: { temperature: 72, humidity: 45, occupancy: 234 }, path: '/building'
  },
  {
    id: 6, name: 'Packaging Line', protocol: 'EtherNet/IP', port: 44818,
    network: '10.0.6.0/24', status: 'online', icon: '📦',
    description: 'Allen-Bradley packaging with conveyors and labeling',
    devices: 2, vulnerabilities: 2, alerts: 1,
    metrics: { speed: 120, packaged: 12847, rejects: 23 }, path: '/packaging'
  },
  {
    id: 7, name: 'IIoT Smart Factory', protocol: 'MQTT', port: 1883,
    network: '10.0.7.0/24', status: 'online', icon: '📡',
    description: 'Edge gateways and sensors with cloud connectivity',
    devices: 20, vulnerabilities: 5, alerts: 2,
    metrics: { sensors: 17, gateways: 3, messages: 4521 }, path: '/iiot'
  },
  {
    id: 8, name: 'CNC Motion Control', protocol: 'PROFINET', port: 34964,
    network: '10.0.8.0/24', status: 'online', icon: '⚙️',
    description: '5-axis CNC machining center with servo drives',
    devices: 6, vulnerabilities: 2, alerts: 0,
    metrics: { spindle: 18000, feedrate: 5000, tool: 12 }, path: '/cnc'
  },
  {
    id: 9, name: 'OT Historian', protocol: 'HTTP API', port: 8443,
    network: '10.0.9.0/24', status: 'critical', icon: '📊',
    description: 'Process data historian with SQL-injectable API',
    devices: 1, vulnerabilities: 6, alerts: 5,
    metrics: { tags: 64, dataPoints: 2847291, storage: 78 }, path: '/historian'
  }
];

const statusColors: Record<string, string> = {
  online: 'bg-green-500', warning: 'bg-yellow-500', critical: 'bg-red-500', offline: 'bg-gray-500'
};

const statusBg: Record<string, string> = {
  online: 'bg-green-500/10 border-green-500/30', warning: 'bg-yellow-500/10 border-yellow-500/30',
  critical: 'bg-red-500/10 border-red-500/30', offline: 'bg-gray-500/10 border-gray-500/30'
};

export default function ScenariosPage() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [selectedScenario, setSelectedScenario] = useState<number | null>(null);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const totalDevices = scenarios.reduce((sum, s) => sum + s.devices, 0);
  const totalVulns = scenarios.reduce((sum, s) => sum + s.vulnerabilities, 0);
  const totalAlerts = scenarios.reduce((sum, s) => sum + s.alerts, 0);
  const onlineCount = scenarios.filter(s => s.status === 'online').length;

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-cyan-400">🔱 VULNOT Control Center</h1>
          <p className="text-slate-400 mt-1">Vulnerable OT Security Training Platform • Mjolnir Security</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-mono text-cyan-300">{currentTime.toLocaleTimeString()}</div>
          <div className="text-slate-400 text-sm">{currentTime.toLocaleDateString()}</div>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4 mb-8">
        {[
          { label: 'Scenarios', value: scenarios.length, sub: `${onlineCount} online`, color: 'text-white' },
          { label: 'Protocols', value: 8, sub: 'Industrial protocols', color: 'text-cyan-400' },
          { label: 'Devices', value: totalDevices, sub: 'Simulated PLCs/RTUs', color: 'text-blue-400' },
          { label: 'Vulnerabilities', value: totalVulns, sub: 'Exploitable flaws', color: 'text-orange-400' },
          { label: 'Active Alerts', value: totalAlerts, sub: 'Requires attention', color: 'text-red-400' }
        ].map((stat, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm">{stat.label}</div>
            <div className={`text-3xl font-bold ${stat.color}`}>{stat.value}</div>
            <div className="text-slate-500 text-sm">{stat.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {scenarios.map((scenario) => (
          <div key={scenario.id}
            className={`bg-slate-900 border rounded-lg p-5 cursor-pointer transition-all hover:scale-[1.02] hover:border-cyan-500/50 ${statusBg[scenario.status]}`}
            onClick={() => setSelectedScenario(selectedScenario === scenario.id ? null : scenario.id)}>
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{scenario.icon}</span>
                <div>
                  <h3 className="font-bold text-lg">{scenario.name}</h3>
                  <div className="flex items-center gap-2 text-sm text-slate-400">
                    <span className="text-cyan-400">{scenario.protocol}</span>
                    <span>•</span>
                    <span>Port {scenario.port}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${statusColors[scenario.status]} animate-pulse`}></span>
                <span className="text-xs uppercase text-slate-400">{scenario.status}</span>
              </div>
            </div>
            <p className="text-slate-400 text-sm mb-4">{scenario.description}</p>
            <div className="grid grid-cols-3 gap-3 mb-4">
              {[
                { value: scenario.devices, label: 'Devices', color: 'text-blue-400' },
                { value: scenario.vulnerabilities, label: 'Vulns', color: 'text-orange-400' },
                { value: scenario.alerts, label: 'Alerts', color: 'text-red-400' }
              ].map((m, i) => (
                <div key={i} className="bg-slate-800/50 rounded p-2 text-center">
                  <div className={`text-lg font-bold ${m.color}`}>{m.value}</div>
                  <div className="text-xs text-slate-500">{m.label}</div>
                </div>
              ))}
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-500">Network:</span>
              <code className="bg-slate-800 px-2 py-1 rounded text-cyan-300 font-mono text-xs">{scenario.network}</code>
            </div>
            {selectedScenario === scenario.id && (
              <div className="mt-4 pt-4 border-t border-slate-700">
                <div className="text-sm text-slate-400 mb-2">Live Metrics</div>
                <div className="grid grid-cols-3 gap-2">
                  {Object.entries(scenario.metrics).map(([key, value]) => (
                    <div key={key} className="bg-slate-800 rounded p-2">
                      <div className="text-xs text-slate-500 capitalize">{key}</div>
                      <div className="text-cyan-300 font-mono">{value}</div>
                    </div>
                  ))}
                </div>
                <button className="mt-4 w-full bg-cyan-600 hover:bg-cyan-500 text-white py-2 rounded font-medium">
                  Open Dashboard →
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-8 text-center text-slate-500 text-sm">
        <p>VULNOT v1.0 • Developed by Milind Bhargava at Mjolnir Security</p>
        <p className="mt-1">Training: <a href="mailto:training@mjolnirsecurity.com" className="text-cyan-400 hover:underline">training@mjolnirsecurity.com</a></p>
      </div>
    </div>
  );
}

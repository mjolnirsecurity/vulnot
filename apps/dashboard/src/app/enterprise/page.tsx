'use client';

import React, { useState, useEffect } from 'react';

interface Site {
  id: string; name: string; location: string; status: 'online' | 'degraded' | 'offline';
  riskScore: number; compliance: number; assets: number; vulnerabilities: number;
  protocols: string[]; lastIncident: string; alerts: number;
}

interface Incident {
  id: string; site: string; severity: 'critical' | 'high' | 'medium' | 'low';
  title: string; time: string; status: 'active' | 'investigating' | 'resolved';
}

const sites: Site[] = [
  { id: 'WTP-01', name: 'Water Treatment Plant', location: 'Denver, CO', status: 'online', riskScore: 72, compliance: 45, assets: 12, vulnerabilities: 4, protocols: ['Modbus', 'DNP3'], lastIncident: '2 days ago', alerts: 2 },
  { id: 'PSA-01', name: 'Power Substation Alpha', location: 'Phoenix, AZ', status: 'online', riskScore: 85, compliance: 38, assets: 8, vulnerabilities: 3, protocols: ['DNP3', 'IEC 61850'], lastIncident: '5 hours ago', alerts: 5 },
  { id: 'MFG-01', name: 'Manufacturing Facility', location: 'Detroit, MI', status: 'degraded', riskScore: 68, compliance: 52, assets: 24, vulnerabilities: 6, protocols: ['S7comm', 'EtherNet/IP'], lastIncident: '1 hour ago', alerts: 8 },
  { id: 'CHP-01', name: 'Chemical Processing', location: 'Houston, TX', status: 'online', riskScore: 91, compliance: 35, assets: 18, vulnerabilities: 7, protocols: ['OPC UA', 'Modbus'], lastIncident: '12 hours ago', alerts: 3 },
  { id: 'SOB-01', name: 'Smart Office Building', location: 'Seattle, WA', status: 'online', riskScore: 45, compliance: 68, assets: 32, vulnerabilities: 2, protocols: ['BACnet', 'MQTT'], lastIncident: '1 week ago', alerts: 0 },
  { id: 'PKD-01', name: 'Packaging & Distribution', location: 'Chicago, IL', status: 'online', riskScore: 58, compliance: 55, assets: 15, vulnerabilities: 3, protocols: ['EtherNet/IP', 'PROFINET'], lastIncident: '3 days ago', alerts: 1 }
];

const recentIncidents: Incident[] = [
  { id: 'INC-2024-042', site: 'MFG-01', severity: 'high', title: 'Unauthorized S7comm connection detected', time: '1 hour ago', status: 'investigating' },
  { id: 'INC-2024-041', site: 'PSA-01', severity: 'critical', title: 'DNP3 Direct Operate command from unknown source', time: '5 hours ago', status: 'active' },
  { id: 'INC-2024-040', site: 'CHP-01', severity: 'medium', title: 'OPC UA anonymous access attempt', time: '12 hours ago', status: 'resolved' },
  { id: 'INC-2024-039', site: 'WTP-01', severity: 'high', title: 'Modbus register manipulation detected', time: '2 days ago', status: 'resolved' },
  { id: 'INC-2024-038', site: 'PKD-01', severity: 'low', title: 'Unusual network traffic pattern', time: '3 days ago', status: 'resolved' }
];

const statusColors: Record<string, string> = {
  online: 'bg-green-500', degraded: 'bg-yellow-500', offline: 'bg-red-500'
};

const severityColors: Record<string, string> = {
  critical: 'bg-red-500 text-white', high: 'bg-orange-500 text-white',
  medium: 'bg-yellow-500 text-black', low: 'bg-blue-500 text-white'
};

export default function EnterprisePage() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [selectedSite, setSelectedSite] = useState<Site | null>(null);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const totalAssets = sites.reduce((sum, s) => sum + s.assets, 0);
  const totalVulns = sites.reduce((sum, s) => sum + s.vulnerabilities, 0);
  const avgRisk = Math.round(sites.reduce((sum, s) => sum + s.riskScore, 0) / sites.length);
  const avgCompliance = Math.round(sites.reduce((sum, s) => sum + s.compliance, 0) / sites.length);
  const totalAlerts = sites.reduce((sum, s) => sum + s.alerts, 0);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">🏢 Enterprise OT Security Dashboard</h1>
          <p className="text-slate-400">Mjolnir Training • Multi-Site Monitoring</p>
        </div>
        <div className="flex items-center gap-4">
          <div className={`px-4 py-2 rounded font-medium ${totalAlerts > 5 ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`}>
            {totalAlerts} Active Alerts
          </div>
          <div className="text-right">
            <div className="text-xl font-mono text-cyan-300">{currentTime.toLocaleTimeString()}</div>
            <div className="text-slate-500 text-sm">{currentTime.toLocaleDateString()}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-6 gap-4 mb-6">
        {[
          { label: 'Total Sites', value: sites.length, sub: `${sites.filter(s => s.status === 'online').length} online`, color: 'text-cyan-400' },
          { label: 'Total Assets', value: totalAssets, sub: 'Monitored devices', color: 'text-blue-400' },
          { label: 'Open Vulns', value: totalVulns, sub: 'Across all sites', color: 'text-orange-400' },
          { label: 'Avg Risk Score', value: avgRisk, sub: 'Enterprise risk', color: avgRisk > 70 ? 'text-red-400' : 'text-yellow-400' },
          { label: 'Avg Compliance', value: `${avgCompliance}%`, sub: 'IEC 62443', color: avgCompliance < 50 ? 'text-red-400' : 'text-green-400' },
          { label: 'Active Alerts', value: totalAlerts, sub: 'Requires attention', color: 'text-red-400' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm">{s.label}</div>
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-slate-500 text-xs">{s.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        <div className="col-span-2">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 mb-6">
            <h2 className="text-lg font-bold text-purple-400 mb-4">🗺️ Site Overview</h2>
            <div className="grid grid-cols-3 gap-4">
              {sites.map(site => (
                <div key={site.id} onClick={() => setSelectedSite(site)}
                  className={`bg-slate-800 border rounded-lg p-4 cursor-pointer transition-all hover:border-cyan-500/50 ${
                    selectedSite?.id === site.id ? 'border-cyan-500' : 'border-slate-700'
                  } ${site.status === 'degraded' ? 'border-yellow-500/50' : ''}`}>
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="font-bold text-white">{site.name}</div>
                      <div className="text-slate-400 text-sm">{site.location}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${statusColors[site.status]} ${site.status !== 'online' ? 'animate-pulse' : ''}`}></span>
                      <span className="text-xs text-slate-500 uppercase">{site.status}</span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    <div className="bg-slate-900 rounded p-2">
                      <div className="text-xs text-slate-500">Risk</div>
                      <div className={`font-bold ${site.riskScore > 80 ? 'text-red-400' : site.riskScore > 60 ? 'text-orange-400' : 'text-green-400'}`}>
                        {site.riskScore}
                      </div>
                    </div>
                    <div className="bg-slate-900 rounded p-2">
                      <div className="text-xs text-slate-500">Compliance</div>
                      <div className={`font-bold ${site.compliance < 50 ? 'text-red-400' : 'text-green-400'}`}>
                        {site.compliance}%
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">{site.assets} assets</span>
                    <span className="text-orange-400">{site.vulnerabilities} vulns</span>
                    {site.alerts > 0 && <span className="text-red-400">{site.alerts} alerts</span>}
                  </div>

                  <div className="flex gap-1 mt-2">
                    {site.protocols.map(p => (
                      <span key={p} className="bg-slate-700 text-cyan-400 px-2 py-0.5 rounded text-xs">{p}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h2 className="text-lg font-bold text-orange-400 mb-4">📊 Risk by Protocol</h2>
            <div className="space-y-3">
              {['Modbus TCP', 'DNP3', 'S7comm', 'OPC UA', 'BACnet', 'EtherNet/IP', 'MQTT', 'PROFINET'].map((proto, i) => {
                const risk = [85, 92, 78, 65, 45, 72, 58, 68][i];
                return (
                  <div key={proto}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-300">{proto}</span>
                      <span className={`${risk > 80 ? 'text-red-400' : risk > 60 ? 'text-orange-400' : 'text-green-400'}`}>
                        {risk}
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2">
                      <div className={`h-2 rounded-full ${risk > 80 ? 'bg-red-500' : risk > 60 ? 'bg-orange-500' : 'bg-green-500'}`}
                        style={{ width: `${risk}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h2 className="text-lg font-bold text-red-400 mb-4">🚨 Recent Incidents</h2>
            <div className="space-y-3">
              {recentIncidents.map(inc => (
                <div key={inc.id} className="bg-slate-800 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${severityColors[inc.severity]}`}>
                      {inc.severity.toUpperCase()}
                    </span>
                    <span className="text-slate-500 text-xs">{inc.time}</span>
                  </div>
                  <div className="text-slate-300 text-sm mb-1">{inc.title}</div>
                  <div className="flex justify-between items-center">
                    <span className="text-cyan-400 text-xs font-mono">{inc.site}</span>
                    <span className={`text-xs ${
                      inc.status === 'active' ? 'text-red-400' : 
                      inc.status === 'investigating' ? 'text-yellow-400' : 'text-green-400'
                    }`}>{inc.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {selectedSite && (
            <div className="bg-slate-900 border border-cyan-500/50 rounded-lg p-4">
              <h2 className="text-lg font-bold text-cyan-400 mb-4">📍 {selectedSite.name}</h2>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-slate-800 rounded p-2">
                    <div className="text-xs text-slate-500">Location</div>
                    <div className="text-white">{selectedSite.location}</div>
                  </div>
                  <div className="bg-slate-800 rounded p-2">
                    <div className="text-xs text-slate-500">Status</div>
                    <div className={`capitalize ${selectedSite.status === 'online' ? 'text-green-400' : 'text-yellow-400'}`}>
                      {selectedSite.status}
                    </div>
                  </div>
                </div>
                <div className="bg-slate-800 rounded p-2">
                  <div className="text-xs text-slate-500">Protocols</div>
                  <div className="flex gap-1 mt-1">
                    {selectedSite.protocols.map(p => (
                      <span key={p} className="bg-slate-700 text-cyan-400 px-2 py-0.5 rounded text-xs">{p}</span>
                    ))}
                  </div>
                </div>
                <div className="bg-slate-800 rounded p-2">
                  <div className="text-xs text-slate-500">Last Incident</div>
                  <div className="text-orange-400">{selectedSite.lastIncident}</div>
                </div>
                <button className="w-full bg-cyan-600 hover:bg-cyan-500 py-2 rounded font-medium">
                  View Site Dashboard →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="text-center text-slate-600 text-sm">
        Developed by Milind Bhargava at Mjolnir Security • Training: training@mjolnirsecurity.com
      </div>
    </div>
  );
}

'use client';

import React, { useState } from 'react';

interface HuntQuery {
  id: string; name: string; description: string; mitre: string; protocol: string;
  query: string; category: 'reconnaissance' | 'initial_access' | 'execution' | 'persistence' | 'collection' | 'impact';
  lastRun: string; findings: number; status: 'not_run' | 'running' | 'completed';
}

const huntQueries: HuntQuery[] = [
  { id: 'HUNT-001', name: 'Modbus Function Code Scan', description: 'Detect reconnaissance using multiple Modbus function codes', mitre: 'T0840', protocol: 'Modbus', query: 'modbus.func_code IN (1,2,3,4,5,6,15,16,43) | stats count by src_ip | where count > 10', category: 'reconnaissance', lastRun: '2 hours ago', findings: 3, status: 'completed' },
  { id: 'HUNT-002', name: 'DNP3 Unauthorized Source', description: 'Identify DNP3 traffic from non-whitelisted sources', mitre: 'T0886', protocol: 'DNP3', query: 'protocol="dnp3" | where NOT src_ip IN (authorized_masters) | stats count by src_ip, dst_ip', category: 'initial_access', lastRun: '1 hour ago', findings: 1, status: 'completed' },
  { id: 'HUNT-003', name: 'S7comm CPU State Change', description: 'Detect attempts to stop or start PLC CPUs', mitre: 'T0816', protocol: 'S7comm', query: 's7comm.param.func IN (0x28, 0x29) | stats count by src_ip, dst_ip, s7comm.param.func', category: 'impact', lastRun: '30 min ago', findings: 2, status: 'completed' },
  { id: 'HUNT-004', name: 'OPC UA Anonymous Session', description: 'Find anonymous OPC UA connections', mitre: 'T0888', protocol: 'OPC UA', query: 'opcua.security_mode=1 AND opcua.security_policy="None" | stats count by src_ip', category: 'initial_access', lastRun: 'Never', findings: 0, status: 'not_run' },
  { id: 'HUNT-005', name: 'MQTT Wildcard Subscription', description: 'Detect broad MQTT topic subscriptions', mitre: 'T0830', protocol: 'MQTT', query: 'mqtt.topic IN ("#", "+/#", "$SYS/#") | stats count by client_id, src_ip', category: 'collection', lastRun: '3 hours ago', findings: 5, status: 'completed' },
  { id: 'HUNT-006', name: 'Historian Query Anomaly', description: 'Detect unusual historian data access patterns', mitre: 'T0802', protocol: 'HTTP', query: 'uri CONTAINS "/api/query" | stats count, dc(tag_name) by src_ip | where count > 100', category: 'collection', lastRun: '15 min ago', findings: 1, status: 'completed' },
  { id: 'HUNT-007', name: 'Off-Hours OT Access', description: 'Identify OT protocol traffic outside business hours', mitre: 'T0859', protocol: 'Multiple', query: 'protocol IN ("modbus","dnp3","s7comm") | where hour NOT IN (7..18) | stats count by src_ip, protocol', category: 'persistence', lastRun: 'Running...', findings: 0, status: 'running' },
  { id: 'HUNT-008', name: 'PLC Program Transfer', description: 'Detect PLC program upload or download', mitre: 'T0843', protocol: 'S7comm', query: 's7comm.param.func IN (0x1a, 0x1b, 0x1c) | stats count by src_ip, dst_ip, direction', category: 'execution', lastRun: 'Never', findings: 0, status: 'not_run' }
];

const mitreMapping = {
  'T0840': 'Network Sniffing', 'T0886': 'Remote Services', 'T0816': 'Device Restart/Shutdown',
  'T0888': 'Remote System Information Discovery', 'T0830': 'Man in the Middle',
  'T0802': 'Automated Collection', 'T0859': 'Valid Accounts', 'T0843': 'Program Download'
};

const categoryColors: Record<string, string> = {
  reconnaissance: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
  initial_access: 'bg-purple-500/20 text-purple-400 border-purple-500/50',
  execution: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
  persistence: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
  collection: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50',
  impact: 'bg-red-500/20 text-red-400 border-red-500/50'
};

export default function HuntingPage() {
  const [selectedQuery, setSelectedQuery] = useState<HuntQuery | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');

  const filteredQueries = filterCategory === 'all' ? huntQueries : huntQueries.filter(q => q.category === filterCategory);
  const totalFindings = huntQueries.reduce((sum, q) => sum + q.findings, 0);
  const completedQueries = huntQueries.filter(q => q.status === 'completed').length;

  const runQuery = (query: HuntQuery) => {
    setSelectedQuery({ ...query, status: 'running' });
    setTimeout(() => {
      setSelectedQuery({ ...query, status: 'completed', findings: Math.floor(Math.random() * 5), lastRun: 'Just now' });
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">🎯 OT Threat Hunting</h1>
          <p className="text-slate-400">Mjolnir Training • Proactive Threat Detection</p>
        </div>
        <button className="bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded font-medium">
          + New Hunt Query
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Hunt Queries', value: huntQueries.length, color: 'text-cyan-400' },
          { label: 'Completed', value: completedQueries, color: 'text-green-400' },
          { label: 'Total Findings', value: totalFindings, color: 'text-orange-400' },
          { label: 'MITRE Techniques', value: Object.keys(mitreMapping).length, color: 'text-purple-400' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm">{s.label}</div>
            <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 mb-6">
        {['all', 'reconnaissance', 'initial_access', 'execution', 'persistence', 'collection', 'impact'].map(cat => (
          <button key={cat} onClick={() => setFilterCategory(cat)}
            className={`px-3 py-1 rounded text-sm capitalize ${
              filterCategory === cat ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}>
            {cat.replace('_', ' ')}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          {filteredQueries.map(query => (
            <div key={query.id} className="bg-slate-900 border border-slate-700 rounded-lg p-4 hover:border-cyan-500/50 transition-all">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-cyan-400">{query.id}</span>
                    <span className="font-bold text-white">{query.name}</span>
                    <span className={`px-2 py-0.5 rounded text-xs border ${categoryColors[query.category]}`}>
                      {query.category.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="text-slate-400 text-sm">{query.description}</div>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-2">
                    <span className="text-red-400 font-mono text-sm">{query.mitre}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      query.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                      query.status === 'running' ? 'bg-yellow-500/20 text-yellow-400 animate-pulse' :
                      'bg-slate-700 text-slate-400'
                    }`}>{query.status}</span>
                  </div>
                  <div className="text-slate-500 text-xs mt-1">{query.lastRun}</div>
                </div>
              </div>

              <div className="bg-slate-800 rounded p-3 mb-3">
                <code className="text-cyan-300 text-sm font-mono">{query.query}</code>
              </div>

              <div className="flex justify-between items-center">
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-purple-400">{query.protocol}</span>
                  {query.findings > 0 && (
                    <span className="text-orange-400">⚠️ {query.findings} findings</span>
                  )}
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setSelectedQuery(query)}
                    className="bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded text-sm">
                    View Results
                  </button>
                  <button onClick={() => runQuery(query)}
                    className="bg-cyan-600 hover:bg-cyan-500 px-3 py-1 rounded text-sm">
                    ▶ Run
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h2 className="text-lg font-bold text-purple-400 mb-4">🗺️ MITRE ATT&CK Coverage</h2>
            <div className="space-y-2">
              {Object.entries(mitreMapping).map(([id, name]) => {
                const query = huntQueries.find(q => q.mitre === id);
                return (
                  <div key={id} className="flex justify-between items-center bg-slate-800 rounded p-2">
                    <div>
                      <span className="font-mono text-red-400 text-sm">{id}</span>
                      <div className="text-slate-400 text-xs">{name}</div>
                    </div>
                    {query && (
                      <span className={`w-2 h-2 rounded-full ${
                        query.findings > 0 ? 'bg-orange-500' : 'bg-green-500'
                      }`}></span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h2 className="text-lg font-bold text-orange-400 mb-4">📊 Recent Findings</h2>
            <div className="space-y-2">
              {huntQueries.filter(q => q.findings > 0).map(q => (
                <div key={q.id} className="bg-slate-800 rounded p-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono text-cyan-400 text-sm">{q.id}</span>
                    <span className="text-orange-400 font-bold">{q.findings}</span>
                  </div>
                  <div className="text-slate-300 text-sm">{q.name}</div>
                  <div className="text-slate-500 text-xs mt-1">{q.lastRun}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {selectedQuery && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50" onClick={() => setSelectedQuery(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 max-w-3xl w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-xl font-bold">{selectedQuery.name}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="font-mono text-cyan-400">{selectedQuery.id}</span>
                  <span className="text-red-400">{selectedQuery.mitre}</span>
                  <span className="text-purple-400">{selectedQuery.protocol}</span>
                </div>
              </div>
              <span className={`px-3 py-1 rounded ${
                selectedQuery.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                selectedQuery.status === 'running' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-700 text-slate-400'
              }`}>{selectedQuery.status}</span>
            </div>

            <div className="bg-slate-800 rounded p-4 mb-4">
              <div className="text-xs text-slate-500 mb-2">Query</div>
              <code className="text-cyan-300 font-mono">{selectedQuery.query}</code>
            </div>

            {selectedQuery.status === 'running' && (
              <div className="text-center py-8">
                <div className="animate-spin text-4xl mb-4">⏳</div>
                <div className="text-slate-400">Running query...</div>
              </div>
            )}

            {selectedQuery.status === 'completed' && selectedQuery.findings > 0 && (
              <div className="bg-slate-800 rounded p-4">
                <div className="text-xs text-slate-500 mb-2">Results ({selectedQuery.findings} findings)</div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 text-left">
                      <th className="p-2">Source IP</th>
                      <th className="p-2">Destination</th>
                      <th className="p-2">Count</th>
                      <th className="p-2">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...Array(selectedQuery.findings)].map((_, i) => (
                      <tr key={i} className="border-t border-slate-700">
                        <td className="p-2 font-mono text-orange-400">192.168.1.{100 + i}</td>
                        <td className="p-2 font-mono text-cyan-400">10.0.{i + 1}.10</td>
                        <td className="p-2">{Math.floor(Math.random() * 50) + 10}</td>
                        <td className="p-2 text-slate-500">{new Date().toLocaleTimeString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="mt-4 flex gap-2">
              <button className="bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded font-medium">
                Create Alert Rule
              </button>
              <button className="bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded font-medium">
                Export Results
              </button>
              <button onClick={() => setSelectedQuery(null)} className="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mt-6 text-center text-slate-600 text-sm">
        Developed by Milind Bhargava at Mjolnir Security • Training: training@mjolnirsecurity.com
      </div>
    </div>
  );
}

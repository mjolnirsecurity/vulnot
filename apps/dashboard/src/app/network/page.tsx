'use client';

import React, { useState } from 'react';

interface NetworkNode {
  id: string; name: string; type: 'plc' | 'rtu' | 'hmi' | 'server' | 'switch' | 'firewall' | 'attacker';
  ip: string; network: string; protocols: string[]; status: 'online' | 'offline' | 'compromised';
  vulnerabilities: number;
}

interface Network {
  id: string; name: string; cidr: string; scenario: string; nodes: NetworkNode[];
}

const networks: Network[] = [
  { id: 'net-1', name: 'Water Treatment', cidr: '10.0.1.0/24', scenario: 'Scenario 1', nodes: [
    { id: 'plc-intake', name: 'PLC-INTAKE', type: 'plc', ip: '10.0.1.10', network: 'net-1', protocols: ['Modbus TCP'], status: 'online', vulnerabilities: 2 },
    { id: 'plc-treatment', name: 'PLC-TREATMENT', type: 'plc', ip: '10.0.1.11', network: 'net-1', protocols: ['Modbus TCP'], status: 'online', vulnerabilities: 2 },
    { id: 'plc-dist', name: 'PLC-DIST', type: 'plc', ip: '10.0.1.12', network: 'net-1', protocols: ['Modbus TCP'], status: 'online', vulnerabilities: 2 },
    { id: 'hmi-water', name: 'HMI-WATER', type: 'hmi', ip: '10.0.1.100', network: 'net-1', protocols: ['HTTP'], status: 'online', vulnerabilities: 1 }
  ]},
  { id: 'net-2', name: 'Power Grid', cidr: '10.0.2.0/24', scenario: 'Scenario 2', nodes: [
    { id: 'rtu-sub1', name: 'RTU-SUB1', type: 'rtu', ip: '10.0.2.10', network: 'net-2', protocols: ['DNP3'], status: 'online', vulnerabilities: 3 },
    { id: 'rtu-sub2', name: 'RTU-SUB2', type: 'rtu', ip: '10.0.2.11', network: 'net-2', protocols: ['DNP3'], status: 'online', vulnerabilities: 3 },
    { id: 'hmi-power', name: 'HMI-POWER', type: 'hmi', ip: '10.0.2.100', network: 'net-2', protocols: ['HTTP'], status: 'online', vulnerabilities: 1 }
  ]},
  { id: 'net-3', name: 'Manufacturing', cidr: '10.0.3.0/24', scenario: 'Scenario 3', nodes: [
    { id: 's7-line1', name: 'S7-1500-LINE1', type: 'plc', ip: '10.0.3.10', network: 'net-3', protocols: ['S7comm'], status: 'online', vulnerabilities: 3 },
    { id: 's7-line2', name: 'S7-1500-LINE2', type: 'plc', ip: '10.0.3.11', network: 'net-3', protocols: ['S7comm'], status: 'compromised', vulnerabilities: 3 },
    { id: 'hmi-factory', name: 'HMI-FACTORY', type: 'hmi', ip: '10.0.3.100', network: 'net-3', protocols: ['HTTP'], status: 'online', vulnerabilities: 1 }
  ]},
  { id: 'net-4', name: 'Chemical Reactor', cidr: '10.0.4.0/24', scenario: 'Scenario 4', nodes: [
    { id: 'opcua-server', name: 'OPCUA-SERVER', type: 'server', ip: '10.0.4.10', network: 'net-4', protocols: ['OPC UA'], status: 'online', vulnerabilities: 2 },
    { id: 'hmi-reactor', name: 'HMI-REACTOR', type: 'hmi', ip: '10.0.4.100', network: 'net-4', protocols: ['HTTP'], status: 'online', vulnerabilities: 1 }
  ]},
  { id: 'net-7', name: 'IIoT/MQTT', cidr: '10.0.7.0/24', scenario: 'Scenario 7', nodes: [
    { id: 'mqtt-broker', name: 'MQTT-BROKER', type: 'server', ip: '10.0.7.5', network: 'net-7', protocols: ['MQTT'], status: 'online', vulnerabilities: 5 },
    { id: 'edge-gw1', name: 'EDGE-GW-01', type: 'server', ip: '10.0.7.10', network: 'net-7', protocols: ['MQTT'], status: 'online', vulnerabilities: 2 },
    { id: 'edge-gw2', name: 'EDGE-GW-02', type: 'server', ip: '10.0.7.11', network: 'net-7', protocols: ['MQTT'], status: 'online', vulnerabilities: 2 }
  ]},
  { id: 'net-9', name: 'Historian', cidr: '10.0.9.0/24', scenario: 'Scenario 9', nodes: [
    { id: 'historian', name: 'HISTORIAN-01', type: 'server', ip: '10.0.9.10', network: 'net-9', protocols: ['HTTP', 'SQL'], status: 'compromised', vulnerabilities: 6 }
  ]},
  { id: 'net-attack', name: 'Attacker Network', cidr: '192.168.1.0/24', scenario: 'Red Team', nodes: [
    { id: 'redteam', name: 'REDTEAM-WS', type: 'attacker', ip: '192.168.1.100', network: 'net-attack', protocols: ['All'], status: 'online', vulnerabilities: 0 }
  ]}
];

const typeIcons: Record<string, string> = {
  plc: '🔧', rtu: '📡', hmi: '🖥️', server: '🖲️', switch: '🔀', firewall: '🛡️', attacker: '💀'
};

const typeColors: Record<string, string> = {
  plc: 'bg-blue-500/20 border-blue-500', rtu: 'bg-purple-500/20 border-purple-500',
  hmi: 'bg-green-500/20 border-green-500', server: 'bg-cyan-500/20 border-cyan-500',
  switch: 'bg-gray-500/20 border-gray-500', firewall: 'bg-orange-500/20 border-orange-500',
  attacker: 'bg-red-500/20 border-red-500'
};

const statusColors: Record<string, string> = {
  online: 'bg-green-500', offline: 'bg-gray-500', compromised: 'bg-red-500 animate-pulse'
};

export default function NetworkPage() {
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null);
  const [selectedNetwork, setSelectedNetwork] = useState<string>('all');

  const filteredNetworks = selectedNetwork === 'all' ? networks : networks.filter(n => n.id === selectedNetwork);
  const totalNodes = networks.reduce((sum, n) => sum + n.nodes.length, 0);
  const compromisedNodes = networks.reduce((sum, n) => sum + n.nodes.filter(node => node.status === 'compromised').length, 0);
  const totalVulns = networks.reduce((sum, n) => sum + n.nodes.reduce((s, node) => s + node.vulnerabilities, 0), 0);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">🌐 Network Topology</h1>
          <p className="text-slate-400">Mjolnir Training • VULNOT Network Map</p>
        </div>
        <div className="flex gap-2">
          <select value={selectedNetwork} onChange={e => setSelectedNetwork(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded px-4 py-2 text-white">
            <option value="all">All Networks</option>
            {networks.map(n => <option key={n.id} value={n.id}>{n.name} ({n.cidr})</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        {[
          { label: 'Networks', value: networks.length, color: 'text-cyan-400' },
          { label: 'Total Nodes', value: totalNodes, color: 'text-blue-400' },
          { label: 'Online', value: totalNodes - compromisedNodes, color: 'text-green-400' },
          { label: 'Compromised', value: compromisedNodes, color: 'text-red-400' },
          { label: 'Vulnerabilities', value: totalVulns, color: 'text-orange-400' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm">{s.label}</div>
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          {filteredNetworks.map(network => (
            <div key={network.id} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-lg font-bold text-cyan-400">{network.name}</h2>
                  <div className="flex items-center gap-2 text-sm text-slate-400">
                    <span className="font-mono">{network.cidr}</span>
                    <span>•</span>
                    <span>{network.scenario}</span>
                  </div>
                </div>
                <div className="text-slate-500 text-sm">{network.nodes.length} nodes</div>
              </div>

              <div className="grid grid-cols-4 gap-3">
                {network.nodes.map(node => (
                  <div key={node.id} onClick={() => setSelectedNode(node)}
                    className={`${typeColors[node.type]} border-2 rounded-lg p-3 cursor-pointer hover:opacity-80 transition-all ${
                      selectedNode?.id === node.id ? 'ring-2 ring-cyan-400' : ''
                    }`}>
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-2xl">{typeIcons[node.type]}</span>
                      <span className={`w-2 h-2 rounded-full ${statusColors[node.status]}`}></span>
                    </div>
                    <div className="font-medium text-white text-sm">{node.name}</div>
                    <div className="font-mono text-cyan-400 text-xs">{node.ip}</div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {node.protocols.map(p => (
                        <span key={p} className="bg-slate-800/50 text-slate-300 px-1.5 py-0.5 rounded text-xs">{p}</span>
                      ))}
                    </div>
                    {node.vulnerabilities > 0 && (
                      <div className="text-orange-400 text-xs mt-2">⚠️ {node.vulnerabilities} vulns</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-6">
          {selectedNode ? (
            <div className="bg-slate-900 border border-cyan-500/50 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl">{typeIcons[selectedNode.type]}</span>
                <div>
                  <h3 className="font-bold text-white">{selectedNode.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded capitalize ${
                    selectedNode.status === 'online' ? 'bg-green-500/20 text-green-400' :
                    selectedNode.status === 'compromised' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'
                  }`}>{selectedNode.status}</span>
                </div>
              </div>

              <div className="space-y-3">
                <div className="bg-slate-800 rounded p-3">
                  <div className="text-xs text-slate-500">IP Address</div>
                  <div className="font-mono text-cyan-400">{selectedNode.ip}</div>
                </div>
                <div className="bg-slate-800 rounded p-3">
                  <div className="text-xs text-slate-500">Network</div>
                  <div className="text-white">{networks.find(n => n.id === selectedNode.network)?.name}</div>
                </div>
                <div className="bg-slate-800 rounded p-3">
                  <div className="text-xs text-slate-500">Type</div>
                  <div className="text-purple-400 capitalize">{selectedNode.type}</div>
                </div>
                <div className="bg-slate-800 rounded p-3">
                  <div className="text-xs text-slate-500">Protocols</div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedNode.protocols.map(p => (
                      <span key={p} className="bg-slate-700 text-cyan-400 px-2 py-0.5 rounded text-sm">{p}</span>
                    ))}
                  </div>
                </div>
                {selectedNode.vulnerabilities > 0 && (
                  <div className="bg-orange-500/10 border border-orange-500/30 rounded p-3">
                    <div className="text-xs text-slate-500">Vulnerabilities</div>
                    <div className="text-orange-400 font-bold">{selectedNode.vulnerabilities} findings</div>
                  </div>
                )}
              </div>

              <div className="mt-4 flex gap-2">
                <button className="flex-1 bg-cyan-600 hover:bg-cyan-500 py-2 rounded text-sm font-medium">
                  🔍 Scan
                </button>
                <button className="flex-1 bg-red-600 hover:bg-red-500 py-2 rounded text-sm font-medium">
                  🎯 Attack
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-center text-slate-500">
              Select a node to view details
            </div>
          )}

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h3 className="font-bold text-purple-400 mb-3">📊 Protocol Distribution</h3>
            <div className="space-y-2">
              {['Modbus TCP', 'DNP3', 'S7comm', 'OPC UA', 'MQTT', 'HTTP'].map(proto => {
                const count = networks.reduce((sum, n) => sum + n.nodes.filter(node => node.protocols.includes(proto)).length, 0);
                const pct = (count / totalNodes) * 100;
                return (
                  <div key={proto}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">{proto}</span>
                      <span className="text-cyan-400">{count}</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5">
                      <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <h3 className="font-bold text-orange-400 mb-3">🎯 Legend</h3>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(typeIcons).map(([type, icon]) => (
                <div key={type} className="flex items-center gap-2 text-sm">
                  <span>{icon}</span>
                  <span className="text-slate-400 capitalize">{type}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 text-center text-slate-600 text-sm">
        Developed by Milind Bhargava at Mjolnir Security • Training: training@mjolnirsecurity.com
      </div>
    </div>
  );
}

'use client';

import React, { useState } from 'react';

interface Vulnerability {
  id: string; title: string; cvss: number; severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'in_progress' | 'mitigated' | 'accepted'; protocol: string;
  affectedAssets: string[]; cve: string; exploitAvailable: boolean;
  description: string; recommendation: string; discoveredDate: string;
}

const vulnerabilities: Vulnerability[] = [
  { id: 'VULN-001', title: 'Modbus TCP No Authentication', cvss: 9.8, severity: 'critical', status: 'open', protocol: 'Modbus', affectedAssets: ['PLC-INTAKE', 'PLC-TREATMENT', 'PLC-DIST'], cve: 'N/A', exploitAvailable: true, description: 'Modbus TCP protocol lacks authentication, allowing any network-connected attacker to read/write PLC registers.', recommendation: 'Implement network segmentation and deploy OT-aware firewall with allowlisting.', discoveredDate: '2024-12-20' },
  { id: 'VULN-002', title: 'DNP3 Secure Authentication Disabled', cvss: 9.5, severity: 'critical', status: 'open', protocol: 'DNP3', affectedAssets: ['RTU-SUB1', 'RTU-SUB2'], cve: 'N/A', exploitAvailable: true, description: 'DNP3 Secure Authentication (SA) is disabled, allowing unauthorized control commands.', recommendation: 'Enable DNP3 Secure Authentication Version 5 (SAv5) on all outstations.', discoveredDate: '2024-12-20' },
  { id: 'VULN-003', title: 'S7comm Weak Security Configuration', cvss: 9.1, severity: 'critical', status: 'in_progress', protocol: 'S7comm', affectedAssets: ['S7-1500-LINE1', 'S7-1500-LINE2'], cve: 'N/A', exploitAvailable: true, description: 'S7comm protection level set to 1 (no protection), allowing CPU stop and program modification.', recommendation: 'Increase protection level to 3 and implement password protection.', discoveredDate: '2024-12-21' },
  { id: 'VULN-004', title: 'MQTT Anonymous Access Enabled', cvss: 8.6, severity: 'high', status: 'open', protocol: 'MQTT', affectedAssets: ['MQTT-BROKER-01'], cve: 'N/A', exploitAvailable: true, description: 'MQTT broker allows anonymous connections and wildcard subscriptions.', recommendation: 'Disable anonymous access, implement authentication, and restrict topic ACLs.', discoveredDate: '2024-12-22' },
  { id: 'VULN-005', title: 'OPC UA Anonymous Access', cvss: 8.2, severity: 'high', status: 'mitigated', protocol: 'OPC UA', affectedAssets: ['OPCUA-SERVER-01'], cve: 'N/A', exploitAvailable: true, description: 'OPC UA server accepts anonymous connections with full read/write access.', recommendation: 'Disable anonymous authentication and implement certificate-based auth.', discoveredDate: '2024-12-19' },
  { id: 'VULN-006', title: 'Historian SQL Injection', cvss: 8.0, severity: 'high', status: 'open', protocol: 'HTTP', affectedAssets: ['HISTORIAN-01'], cve: 'CVE-2024-XXXXX', exploitAvailable: true, description: 'SQL injection vulnerability in historian API tag query endpoint.', recommendation: 'Apply vendor patch and implement parameterized queries.', discoveredDate: '2024-12-23' },
  { id: 'VULN-007', title: 'Default Credentials on HMI', cvss: 7.8, severity: 'high', status: 'in_progress', protocol: 'Multiple', affectedAssets: ['HMI-WATER', 'HMI-POWER', 'HMI-FACTORY'], cve: 'N/A', exploitAvailable: true, description: 'Default vendor credentials still in use on HMI systems.', recommendation: 'Change all default credentials to strong unique passwords.', discoveredDate: '2024-12-20' },
  { id: 'VULN-008', title: 'BACnet No Encryption', cvss: 6.5, severity: 'medium', status: 'accepted', protocol: 'BACnet', affectedAssets: ['BACNET-CTRL-01'], cve: 'N/A', exploitAvailable: false, description: 'BACnet/IP traffic is unencrypted, allowing eavesdropping.', recommendation: 'Implement BACnet Secure Connect (BACnet/SC) where supported.', discoveredDate: '2024-12-18' },
  { id: 'VULN-009', title: 'No Network Segmentation', cvss: 7.5, severity: 'high', status: 'open', protocol: 'Network', affectedAssets: ['ALL'], cve: 'N/A', exploitAvailable: false, description: 'IT and OT networks are not properly segmented.', recommendation: 'Implement Purdue Model zones with firewalls at each level.', discoveredDate: '2024-12-15' },
  { id: 'VULN-010', title: 'Missing OT IDS/IPS', cvss: 5.5, severity: 'medium', status: 'mitigated', protocol: 'Network', affectedAssets: ['ALL'], cve: 'N/A', exploitAvailable: false, description: 'No intrusion detection system monitoring OT network traffic.', recommendation: 'Deploy OT-aware IDS with protocol-specific detection rules.', discoveredDate: '2024-12-16' }
];

const severityColors: Record<string, string> = {
  critical: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-yellow-500', low: 'bg-blue-500'
};

const statusColors: Record<string, string> = {
  open: 'bg-red-500/20 text-red-400 border-red-500/50',
  in_progress: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
  mitigated: 'bg-green-500/20 text-green-400 border-green-500/50',
  accepted: 'bg-blue-500/20 text-blue-400 border-blue-500/50'
};

export default function VulnerabilitiesPage() {
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [expandedVuln, setExpandedVuln] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredVulns = vulnerabilities.filter(v => {
    if (filterSeverity !== 'all' && v.severity !== filterSeverity) return false;
    if (filterStatus !== 'all' && v.status !== filterStatus) return false;
    if (searchTerm && !v.title.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !v.id.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  const criticalCount = vulnerabilities.filter(v => v.severity === 'critical' && v.status !== 'mitigated').length;
  const highCount = vulnerabilities.filter(v => v.severity === 'high' && v.status !== 'mitigated').length;
  const openCount = vulnerabilities.filter(v => v.status === 'open').length;
  const exploitableCount = vulnerabilities.filter(v => v.exploitAvailable && v.status !== 'mitigated').length;

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">🔓 Vulnerability Management</h1>
          <p className="text-slate-400">Mjolnir Training • OT Vulnerability Tracking</p>
        </div>
        <button className="bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded font-medium">
          📥 Export Report
        </button>
      </div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        {[
          { label: 'Total Vulnerabilities', value: vulnerabilities.length, color: 'text-white' },
          { label: 'Critical', value: criticalCount, color: 'text-red-400' },
          { label: 'High', value: highCount, color: 'text-orange-400' },
          { label: 'Open', value: openCount, color: 'text-yellow-400' },
          { label: 'Exploitable', value: exploitableCount, color: 'text-red-400' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm">{s.label}</div>
            <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-4 mb-6">
        <input type="text" placeholder="Search vulnerabilities..." value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          className="flex-1 bg-slate-900 border border-slate-700 rounded px-4 py-2 text-white" />
        <div className="flex gap-2">
          <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded px-4 py-2 text-white">
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded px-4 py-2 text-white">
            <option value="all">All Status</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="mitigated">Mitigated</option>
            <option value="accepted">Accepted</option>
          </select>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
        <div className="space-y-2 p-4">
          {filteredVulns.map(vuln => (
            <div key={vuln.id} className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
              <div className="p-4 cursor-pointer hover:bg-slate-700/50" 
                onClick={() => setExpandedVuln(expandedVuln === vuln.id ? null : vuln.id)}>
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-4">
                    <div className={`w-1 h-12 rounded ${severityColors[vuln.severity]}`}></div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-cyan-400">{vuln.id}</span>
                        <span className="font-bold text-white">{vuln.title}</span>
                        {vuln.exploitAvailable && (
                          <span className="bg-red-500/20 text-red-400 px-2 py-0.5 rounded text-xs">
                            🎯 Exploit Available
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-sm">
                        <span className="text-slate-400">CVSS: <span className={`font-bold ${vuln.cvss >= 9 ? 'text-red-400' : vuln.cvss >= 7 ? 'text-orange-400' : 'text-yellow-400'}`}>{vuln.cvss}</span></span>
                        <span className="text-purple-400">{vuln.protocol}</span>
                        <span className="text-slate-500">{vuln.affectedAssets.length} assets</span>
                        {vuln.cve !== 'N/A' && <span className="text-orange-400">{vuln.cve}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded text-sm border ${statusColors[vuln.status]}`}>
                      {vuln.status.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="text-slate-500 text-sm">{vuln.discoveredDate}</span>
                  </div>
                </div>
              </div>

              {expandedVuln === vuln.id && (
                <div className="px-4 pb-4 border-t border-slate-700 pt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-slate-500 mb-1">Description</div>
                      <div className="text-slate-300 text-sm">{vuln.description}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-1">Recommendation</div>
                      <div className="text-green-400 text-sm">{vuln.recommendation}</div>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="text-xs text-slate-500 mb-2">Affected Assets</div>
                    <div className="flex flex-wrap gap-2">
                      {vuln.affectedAssets.map(asset => (
                        <span key={asset} className="bg-slate-700 text-cyan-400 px-2 py-1 rounded text-sm font-mono">
                          {asset}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <button className="bg-yellow-600 hover:bg-yellow-500 px-3 py-1 rounded text-sm">
                      Mark In Progress
                    </button>
                    <button className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-sm">
                      Mark Mitigated
                    </button>
                    <button className="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm">
                      Accept Risk
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 text-center text-slate-600 text-sm">
        Developed by Milind Bhargava at Mjolnir Security • Training: training@mjolnirsecurity.com
      </div>
    </div>
  );
}

'use client';

import React, { useState } from 'react';

interface Requirement {
  id: string; name: string; category: string; description: string;
  status: 'compliant' | 'partial' | 'non_compliant' | 'not_assessed';
  evidence: string; securityLevel: number;
}

const frameworks = [
  { id: 'iec62443', name: 'IEC 62443-3-3', description: 'Industrial Automation Security' },
  { id: 'nist_csf', name: 'NIST CSF', description: 'Cybersecurity Framework' },
  { id: 'nerc_cip', name: 'NERC CIP', description: 'Critical Infrastructure Protection' }
];

const requirements: Requirement[] = [
  { id: 'SR 1.1', name: 'Human user identification and authentication', category: 'FR1 - Identification & Authentication', description: 'All human users shall be identified and authenticated', status: 'non_compliant', evidence: 'Modbus TCP allows anonymous access', securityLevel: 1 },
  { id: 'SR 1.2', name: 'Software process and device identification', category: 'FR1 - Identification & Authentication', description: 'Software processes and devices shall be identified', status: 'partial', evidence: 'Some devices use default credentials', securityLevel: 1 },
  { id: 'SR 1.5', name: 'Authenticator management', category: 'FR1 - Identification & Authentication', description: 'Authenticators shall be managed securely', status: 'non_compliant', evidence: 'Default passwords in use', securityLevel: 1 },
  { id: 'SR 1.7', name: 'Strength of password-based authentication', category: 'FR1 - Identification & Authentication', description: 'Password strength requirements', status: 'non_compliant', evidence: 'Weak passwords detected', securityLevel: 2 },
  { id: 'SR 2.1', name: 'Authorization enforcement', category: 'FR2 - Use Control', description: 'Authorization shall be enforced', status: 'partial', evidence: 'Limited access controls on PLCs', securityLevel: 1 },
  { id: 'SR 2.8', name: 'Auditable events', category: 'FR2 - Use Control', description: 'System shall generate audit records', status: 'compliant', evidence: 'Historian logs all events', securityLevel: 1 },
  { id: 'SR 3.1', name: 'Communication integrity', category: 'FR3 - System Integrity', description: 'Communications shall be protected', status: 'non_compliant', evidence: 'No TLS on OT protocols', securityLevel: 1 },
  { id: 'SR 3.5', name: 'Input validation', category: 'FR3 - System Integrity', description: 'Inputs shall be validated', status: 'non_compliant', evidence: 'SQL injection in historian', securityLevel: 2 },
  { id: 'SR 4.1', name: 'Information confidentiality', category: 'FR4 - Data Confidentiality', description: 'Information shall be protected', status: 'partial', evidence: 'Some data encrypted at rest', securityLevel: 2 },
  { id: 'SR 4.3', name: 'Use of cryptography', category: 'FR4 - Data Confidentiality', description: 'Cryptography shall be used appropriately', status: 'non_compliant', evidence: 'No encryption on OT traffic', securityLevel: 2 },
  { id: 'SR 5.1', name: 'Network segmentation', category: 'FR5 - Restricted Data Flow', description: 'Network shall be segmented', status: 'non_compliant', evidence: 'Flat network architecture', securityLevel: 1 },
  { id: 'SR 5.2', name: 'Zone boundary protection', category: 'FR5 - Restricted Data Flow', description: 'Zone boundaries shall be protected', status: 'non_compliant', evidence: 'No firewalls between zones', securityLevel: 1 },
  { id: 'SR 6.1', name: 'Audit log accessibility', category: 'FR6 - Timely Response', description: 'Audit logs shall be accessible', status: 'compliant', evidence: 'Centralized logging enabled', securityLevel: 1 },
  { id: 'SR 6.2', name: 'Continuous monitoring', category: 'FR6 - Timely Response', description: 'Systems shall be continuously monitored', status: 'partial', evidence: 'IDS deployed but limited coverage', securityLevel: 2 },
  { id: 'SR 7.1', name: 'Denial of service protection', category: 'FR7 - Resource Availability', description: 'Protection against DoS attacks', status: 'not_assessed', evidence: 'Not tested', securityLevel: 2 },
  { id: 'SR 7.6', name: 'Network and security configuration', category: 'FR7 - Resource Availability', description: 'Secure configuration management', status: 'partial', evidence: 'Some hardening applied', securityLevel: 1 }
];

const statusColors: Record<string, string> = {
  compliant: 'bg-green-500', partial: 'bg-yellow-500', non_compliant: 'bg-red-500', not_assessed: 'bg-gray-500'
};

const statusLabels: Record<string, string> = {
  compliant: 'Compliant', partial: 'Partial', non_compliant: 'Non-Compliant', not_assessed: 'Not Assessed'
};

export default function CompliancePage() {
  const [selectedFramework, setSelectedFramework] = useState('iec62443');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [expandedReq, setExpandedReq] = useState<string | null>(null);

  const filteredReqs = filterStatus === 'all' ? requirements : requirements.filter(r => r.status === filterStatus);
  
  const compliantCount = requirements.filter(r => r.status === 'compliant').length;
  const partialCount = requirements.filter(r => r.status === 'partial').length;
  const nonCompliantCount = requirements.filter(r => r.status === 'non_compliant').length;
  const notAssessedCount = requirements.filter(r => r.status === 'not_assessed').length;
  
  const overallScore = Math.round(((compliantCount * 1 + partialCount * 0.5) / (requirements.length - notAssessedCount)) * 100);

  const categories = Array.from(new Set(requirements.map(r => r.category)));
  const categoryScores = categories.map(cat => {
    const catReqs = requirements.filter(r => r.category === cat);
    const score = Math.round(((catReqs.filter(r => r.status === 'compliant').length * 1 + 
      catReqs.filter(r => r.status === 'partial').length * 0.5) / catReqs.length) * 100);
    return { category: cat.split(' - ')[0], name: cat.split(' - ')[1], score, total: catReqs.length };
  });

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">📋 Compliance Assessment</h1>
          <p className="text-slate-400">Mjolnir Training • OT Security Framework Compliance</p>
        </div>
        <div className="flex gap-2">
          {frameworks.map(fw => (
            <button key={fw.id} onClick={() => setSelectedFramework(fw.id)}
              className={`px-4 py-2 rounded ${selectedFramework === fw.id ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>
              {fw.name}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 col-span-1">
          <div className="text-slate-400 text-sm">Overall Score</div>
          <div className="relative pt-4">
            <svg className="w-full h-32" viewBox="0 0 100 60">
              <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#334155" strokeWidth="8" strokeLinecap="round"/>
              <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" 
                stroke={overallScore >= 70 ? '#22c55e' : overallScore >= 40 ? '#eab308' : '#ef4444'} 
                strokeWidth="8" strokeLinecap="round"
                strokeDasharray={`${overallScore * 1.26} 126`}/>
              <text x="50" y="45" textAnchor="middle" className="text-2xl font-bold fill-white">{overallScore}%</text>
            </svg>
          </div>
          <div className="text-center text-sm text-slate-500">IEC 62443 SL2 Target</div>
        </div>

        {[
          { label: 'Compliant', value: compliantCount, color: 'text-green-400', bg: 'bg-green-500' },
          { label: 'Partial', value: partialCount, color: 'text-yellow-400', bg: 'bg-yellow-500' },
          { label: 'Non-Compliant', value: nonCompliantCount, color: 'text-red-400', bg: 'bg-red-500' },
          { label: 'Not Assessed', value: notAssessedCount, color: 'text-gray-400', bg: 'bg-gray-500' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm">{s.label}</div>
            <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
            <div className="flex items-center gap-2 mt-2">
              <span className={`w-3 h-3 rounded-full ${s.bg}`}></span>
              <span className="text-slate-500 text-sm">{Math.round((s.value / requirements.length) * 100)}%</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        <div className="col-span-1 bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h2 className="text-lg font-bold text-purple-400 mb-4">📊 Category Scores</h2>
          <div className="space-y-3">
            {categoryScores.map(cat => (
              <div key={cat.category}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-cyan-400">{cat.category}</span>
                  <span className={`${cat.score >= 70 ? 'text-green-400' : cat.score >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {cat.score}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2">
                  <div className={`h-2 rounded-full ${cat.score >= 70 ? 'bg-green-500' : cat.score >= 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${cat.score}%` }}></div>
                </div>
                <div className="text-xs text-slate-500 mt-1">{cat.name}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-2 bg-slate-900 border border-slate-700 rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-bold text-orange-400">📝 Requirements</h2>
            <div className="flex gap-2">
              {['all', 'compliant', 'partial', 'non_compliant', 'not_assessed'].map(status => (
                <button key={status} onClick={() => setFilterStatus(status)}
                  className={`px-3 py-1 rounded text-xs capitalize ${filterStatus === status ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
                  {status === 'non_compliant' ? 'Non-Compliant' : status === 'not_assessed' ? 'Not Assessed' : status}
                </button>
              ))}
            </div>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredReqs.map(req => (
              <div key={req.id} className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
                <div className="p-3 cursor-pointer hover:bg-slate-700/50" onClick={() => setExpandedReq(expandedReq === req.id ? null : req.id)}>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <span className={`w-3 h-3 rounded-full ${statusColors[req.status]}`}></span>
                      <span className="font-mono text-cyan-400 text-sm">{req.id}</span>
                      <span className="text-slate-300">{req.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500">SL{req.securityLevel}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        req.status === 'compliant' ? 'bg-green-500/20 text-green-400' :
                        req.status === 'partial' ? 'bg-yellow-500/20 text-yellow-400' :
                        req.status === 'non_compliant' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'
                      }`}>{statusLabels[req.status]}</span>
                    </div>
                  </div>
                </div>
                {expandedReq === req.id && (
                  <div className="px-3 pb-3 border-t border-slate-700 pt-3">
                    <div className="text-slate-400 text-sm mb-2">{req.description}</div>
                    <div className="text-xs text-slate-500 mb-1">Category</div>
                    <div className="text-purple-400 text-sm mb-2">{req.category}</div>
                    <div className="text-xs text-slate-500 mb-1">Evidence/Finding</div>
                    <div className={`text-sm ${req.status === 'compliant' ? 'text-green-400' : 'text-red-400'}`}>{req.evidence}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
        <h2 className="text-lg font-bold text-red-400 mb-4">⚠️ Top Gaps</h2>
        <div className="grid grid-cols-3 gap-4">
          {requirements.filter(r => r.status === 'non_compliant').slice(0, 6).map(req => (
            <div key={req.id} className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-mono text-cyan-400 text-sm">{req.id}</span>
                <span className="text-white font-medium">{req.name}</span>
              </div>
              <div className="text-red-400 text-sm">{req.evidence}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 flex justify-between items-center">
        <div className="text-slate-600 text-sm">
          Developed by Milind Bhargava at Mjolnir Security • Training: training@mjolnirsecurity.com
        </div>
        <button className="bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded font-medium">📥 Export Report</button>
      </div>
    </div>
  );
}

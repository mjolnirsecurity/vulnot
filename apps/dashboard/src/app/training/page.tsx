'use client';

import React, { useState } from 'react';

interface Lab {
  id: number; title: string; description: string; duration: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  protocols: string[]; objectives: string[]; prerequisites: string[];
  status: 'not_started' | 'in_progress' | 'completed'; progress: number; score: number;
}

const labs: Lab[] = [
  { id: 1, title: 'Modbus Protocol Discovery', description: 'Learn to enumerate and identify Modbus TCP devices on an OT network.', duration: '45 min', difficulty: 'beginner', protocols: ['Modbus TCP'], objectives: ['Scan for Modbus devices', 'Read device information', 'Map register addresses', 'Document findings'], prerequisites: [], status: 'completed', progress: 100, score: 95 },
  { id: 2, title: 'Modbus Register Exploitation', description: 'Practice reading and writing Modbus registers to manipulate process values.', duration: '60 min', difficulty: 'beginner', protocols: ['Modbus TCP'], objectives: ['Read holding registers', 'Write to coils', 'Modify setpoints', 'Observe process impact'], prerequisites: ['Lab 1'], status: 'completed', progress: 100, score: 88 },
  { id: 3, title: 'DNP3 Substation Attack', description: 'Simulate attacks on electrical substation using DNP3 protocol.', duration: '75 min', difficulty: 'intermediate', protocols: ['DNP3'], objectives: ['Enumerate outstations', 'Issue Direct Operate commands', 'Manipulate binary outputs', 'Simulate breaker attacks'], prerequisites: ['Lab 1', 'Lab 2'], status: 'in_progress', progress: 65, score: 0 },
  { id: 4, title: 'S7comm Manufacturing Sabotage', description: 'Exploit Siemens S7 PLCs in a manufacturing environment.', duration: '90 min', difficulty: 'intermediate', protocols: ['S7comm'], objectives: ['Identify S7 PLCs', 'Stop CPU remotely', 'Read/write data blocks', 'Extract production data'], prerequisites: ['Lab 1', 'Lab 2'], status: 'not_started', progress: 0, score: 0 },
  { id: 5, title: 'OPC UA Reactor Compromise', description: 'Attack OPC UA servers controlling chemical reactor systems.', duration: '90 min', difficulty: 'intermediate', protocols: ['OPC UA'], objectives: ['Browse address space', 'Exploit anonymous access', 'Modify safety parameters', 'Understand TRITON-style attacks'], prerequisites: ['Lab 3', 'Lab 4'], status: 'not_started', progress: 0, score: 0 },
  { id: 6, title: 'BACnet Building Takeover', description: 'Compromise building automation systems using BACnet protocol.', duration: '75 min', difficulty: 'intermediate', protocols: ['BACnet/IP'], objectives: ['Discover BACnet devices', 'Read property values', 'Control HVAC systems', 'Manipulate access control'], prerequisites: ['Lab 1'], status: 'not_started', progress: 0, score: 0 },
  { id: 7, title: 'MQTT/IIoT Supply Chain', description: 'Attack IIoT infrastructure through MQTT broker exploitation.', duration: '90 min', difficulty: 'advanced', protocols: ['MQTT'], objectives: ['Enumerate topics', 'Spoof sensor data', 'Compromise edge gateways', 'Inject firmware updates'], prerequisites: ['Lab 4', 'Lab 5'], status: 'not_started', progress: 0, score: 0 },
  { id: 8, title: 'Historian Attacks & Forensics', description: 'SQL injection on historians and OT forensic investigation.', duration: '120 min', difficulty: 'expert', protocols: ['HTTP', 'SQL'], objectives: ['Exploit SQL injection', 'Extract historical data', 'Cover tracks', 'Perform forensic analysis'], prerequisites: ['Lab 6', 'Lab 7'], status: 'not_started', progress: 0, score: 0 },
  { id: 9, title: 'Capstone Assessment', description: 'Comprehensive OT security assessment covering all scenarios.', duration: '4-8 hrs', difficulty: 'expert', protocols: ['All'], objectives: ['Full reconnaissance', 'Vulnerability assessment', 'Exploitation chain', 'Forensic analysis', 'Compliance mapping', 'Professional reporting'], prerequisites: ['All previous labs'], status: 'not_started', progress: 0, score: 0 }
];

const difficultyColors: Record<string, string> = {
  beginner: 'bg-green-500/20 text-green-400 border-green-500/50',
  intermediate: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
  advanced: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
  expert: 'bg-red-500/20 text-red-400 border-red-500/50'
};

const statusColors: Record<string, string> = {
  not_started: 'bg-slate-700 text-slate-400',
  in_progress: 'bg-yellow-500/20 text-yellow-400',
  completed: 'bg-green-500/20 text-green-400'
};

export default function TrainingPage() {
  const [selectedLab, setSelectedLab] = useState<Lab | null>(null);
  const [filterDifficulty, setFilterDifficulty] = useState<string>('all');

  const filteredLabs = filterDifficulty === 'all' ? labs : labs.filter(l => l.difficulty === filterDifficulty);
  const completedLabs = labs.filter(l => l.status === 'completed').length;
  const totalProgress = Math.round(labs.reduce((sum, l) => sum + l.progress, 0) / labs.length);
  const avgScore = labs.filter(l => l.score > 0).reduce((sum, l) => sum + l.score, 0) / (labs.filter(l => l.score > 0).length || 1);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">📚 VULNOT Training Labs</h1>
          <p className="text-slate-400">Mjolnir Training • Hands-on OT Security Training</p>
        </div>
        <div className="bg-slate-900 border border-cyan-500/50 rounded-lg px-4 py-2">
          <span className="text-slate-400 text-sm">Training Inquiries:</span>
          <a href="mailto:training@mjolnirsecurity.com" className="text-cyan-400 ml-2 hover:underline">
            training@mjolnirsecurity.com
          </a>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Labs', value: labs.length, color: 'text-cyan-400' },
          { label: 'Completed', value: `${completedLabs}/${labs.length}`, color: 'text-green-400' },
          { label: 'Overall Progress', value: `${totalProgress}%`, color: 'text-purple-400' },
          { label: 'Average Score', value: `${Math.round(avgScore)}%`, color: 'text-orange-400' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm">{s.label}</div>
            <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 mb-6">
        {['all', 'beginner', 'intermediate', 'advanced', 'expert'].map(diff => (
          <button key={diff} onClick={() => setFilterDifficulty(diff)}
            className={`px-4 py-2 rounded capitalize ${
              filterDifficulty === diff ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}>
            {diff}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {filteredLabs.map(lab => (
          <div key={lab.id} className={`bg-slate-900 border rounded-lg overflow-hidden transition-all hover:border-cyan-500/50 ${
            lab.status === 'completed' ? 'border-green-500/30' : lab.status === 'in_progress' ? 'border-yellow-500/30' : 'border-slate-700'
          }`}>
            <div className="p-5">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <span className="bg-slate-800 text-cyan-400 w-8 h-8 rounded-full flex items-center justify-center font-bold">
                    {lab.id}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-xs border ${difficultyColors[lab.difficulty]}`}>
                    {lab.difficulty}
                  </span>
                </div>
                <span className={`px-2 py-1 rounded text-xs ${statusColors[lab.status]}`}>
                  {lab.status.replace('_', ' ')}
                </span>
              </div>

              <h3 className="font-bold text-lg text-white mb-2">{lab.title}</h3>
              <p className="text-slate-400 text-sm mb-4">{lab.description}</p>

              <div className="flex flex-wrap gap-1 mb-4">
                {lab.protocols.map(p => (
                  <span key={p} className="bg-slate-800 text-purple-400 px-2 py-0.5 rounded text-xs">{p}</span>
                ))}
              </div>

              <div className="flex justify-between items-center text-sm mb-3">
                <span className="text-slate-500">⏱️ {lab.duration}</span>
                {lab.score > 0 && <span className="text-green-400">Score: {lab.score}%</span>}
              </div>

              {lab.status !== 'not_started' && (
                <div className="mb-4">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-500">Progress</span>
                    <span className="text-cyan-400">{lab.progress}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div className={`h-2 rounded-full ${lab.status === 'completed' ? 'bg-green-500' : 'bg-cyan-500'}`}
                      style={{ width: `${lab.progress}%` }}></div>
                  </div>
                </div>
              )}

              <button onClick={() => setSelectedLab(lab)}
                className={`w-full py-2 rounded font-medium ${
                  lab.status === 'completed' ? 'bg-green-600 hover:bg-green-500' :
                  lab.status === 'in_progress' ? 'bg-yellow-600 hover:bg-yellow-500' :
                  'bg-cyan-600 hover:bg-cyan-500'
                }`}>
                {lab.status === 'completed' ? 'Review Lab' : lab.status === 'in_progress' ? 'Continue Lab' : 'Start Lab'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedLab && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50" onClick={() => setSelectedLab(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 max-w-2xl w-full" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="bg-cyan-600 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold">
                    {selectedLab.id}
                  </span>
                  <h2 className="text-xl font-bold">{selectedLab.title}</h2>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs border ${difficultyColors[selectedLab.difficulty]}`}>
                    {selectedLab.difficulty}
                  </span>
                  <span className="text-slate-500 text-sm">⏱️ {selectedLab.duration}</span>
                </div>
              </div>
              <span className={`px-3 py-1 rounded ${statusColors[selectedLab.status]}`}>
                {selectedLab.status.replace('_', ' ')}
              </span>
            </div>

            <p className="text-slate-300 mb-4">{selectedLab.description}</p>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-slate-800 rounded p-4">
                <div className="text-sm text-slate-400 mb-2">Learning Objectives</div>
                <ul className="space-y-1">
                  {selectedLab.objectives.map((obj, i) => (
                    <li key={i} className="text-cyan-400 text-sm flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full"></span>
                      {obj}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-slate-800 rounded p-4">
                <div className="text-sm text-slate-400 mb-2">Protocols Covered</div>
                <div className="flex flex-wrap gap-2">
                  {selectedLab.protocols.map(p => (
                    <span key={p} className="bg-slate-700 text-purple-400 px-3 py-1 rounded">{p}</span>
                  ))}
                </div>
                {selectedLab.prerequisites.length > 0 && (
                  <>
                    <div className="text-sm text-slate-400 mt-4 mb-2">Prerequisites</div>
                    <div className="text-orange-400 text-sm">{selectedLab.prerequisites.join(', ')}</div>
                  </>
                )}
              </div>
            </div>

            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-4 mb-4">
              <div className="text-yellow-400 font-medium mb-1">📧 Official Training Available</div>
              <div className="text-slate-300 text-sm">
                For instructor-led training with certification, contact Mjolnir Training at{' '}
                <a href="mailto:training@mjolnirsecurity.com" className="text-cyan-400 hover:underline">
                  training@mjolnirsecurity.com
                </a>
              </div>
            </div>

            <div className="flex gap-2">
              <button className="flex-1 bg-cyan-600 hover:bg-cyan-500 py-2 rounded font-medium">
                {selectedLab.status === 'completed' ? 'Review Lab' : selectedLab.status === 'in_progress' ? 'Continue' : 'Start Lab'}
              </button>
              <button onClick={() => setSelectedLab(null)} className="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mt-8 bg-slate-900 border border-cyan-500/30 rounded-lg p-6">
        <div className="flex items-center gap-4">
          <div className="text-4xl">🏆</div>
          <div>
            <h3 className="text-xl font-bold text-cyan-400">VULNOT Certification</h3>
            <p className="text-slate-400">Complete all labs and the capstone assessment to earn your VULNOT OT Security Practitioner certification.</p>
            <p className="text-slate-500 text-sm mt-2">
              For official certification programs, contact Mjolnir Training at{' '}
              <a href="mailto:training@mjolnirsecurity.com" className="text-cyan-400 hover:underline">training@mjolnirsecurity.com</a>
            </p>
          </div>
        </div>
      </div>

      <div className="mt-6 text-center text-slate-600 text-sm">
        Developed by Milind Bhargava at Mjolnir Security • Training: training@mjolnirsecurity.com
      </div>
    </div>
  );
}

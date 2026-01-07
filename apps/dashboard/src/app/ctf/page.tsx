'use client';

import React, { useState } from 'react';

interface Challenge {
  id: string; name: string; category: string; protocol: string; points: number;
  difficulty: 'easy' | 'medium' | 'hard' | 'expert'; description: string;
  hint: string; solves: number; solved: boolean; hasExploit: boolean;
}

interface Team { rank: number; name: string; score: number; solves: number; lastSolve: string; }

const challenges: Challenge[] = [
  { id: 'MOD-01', name: 'First Contact', category: 'Modbus', protocol: 'Modbus TCP', points: 50, difficulty: 'easy', description: 'Find the Modbus device and read holding register 0. Submit the value as the flag.', hint: 'Use vulnot-scan to discover devices on 10.0.1.0/24', solves: 47, solved: false, hasExploit: true },
  { id: 'MOD-02', name: 'Tank Overflow', category: 'Modbus', protocol: 'Modbus TCP', points: 100, difficulty: 'easy', description: 'Modify the tank level setpoint to trigger a high-level alarm. Flag appears in alarm console.', hint: 'Write to holding register 1', solves: 38, solved: false, hasExploit: true },
  { id: 'MOD-03', name: 'Pump Stopper', category: 'Modbus', protocol: 'Modbus TCP', points: 150, difficulty: 'medium', description: 'Stop all pumps in the water treatment plant. Find the flag in the process logs.', hint: 'Coils control pump states', solves: 24, solved: true, hasExploit: true },
  { id: 'MOD-04', name: 'Chemical Chaos', category: 'Modbus', protocol: 'Modbus TCP', points: 300, difficulty: 'hard', description: 'Manipulate chlorine dosing to dangerous levels while bypassing alarm triggers.', hint: 'Multiple registers need modification', solves: 8, solved: false, hasExploit: true },
  { id: 'DNP3-01', name: 'Grid Discovery', category: 'DNP3', protocol: 'DNP3', points: 100, difficulty: 'easy', description: 'Enumerate DNP3 outstations and find the flag in device configuration.', hint: 'Check device addresses 1-10', solves: 35, solved: false, hasExploit: true },
  { id: 'DNP3-02', name: 'Breaker Flip', category: 'DNP3', protocol: 'DNP3', points: 200, difficulty: 'medium', description: 'Open circuit breaker CB-101 using DNP3 Direct Operate commands.', hint: 'Control relay output point 0', solves: 19, solved: false, hasExploit: true },
  { id: 'DNP3-03', name: 'Blackout', category: 'DNP3', protocol: 'DNP3', points: 350, difficulty: 'hard', description: 'Coordinate attack to trip all breakers simultaneously. Flag in event buffer.', hint: 'Timing is everything', solves: 6, solved: false, hasExploit: true },
  { id: 'DNP3-04', name: 'Ukraine Replay', category: 'DNP3', protocol: 'DNP3', points: 500, difficulty: 'expert', description: 'Replicate the 2015 Ukraine attack pattern. Full APT chain required.', hint: 'Study the APT campaign module', solves: 2, solved: false, hasExploit: true },
  { id: 'S7-01', name: 'PLC Hunter', category: 'S7comm', protocol: 'S7comm', points: 100, difficulty: 'easy', description: 'Identify S7-1500 PLCs and extract CPU information. Flag in module serial.', hint: 'Use vulnot-s7 info command', solves: 31, solved: true, hasExploit: true },
  { id: 'S7-02', name: 'Production Stop', category: 'S7comm', protocol: 'S7comm', points: 200, difficulty: 'medium', description: 'Stop the PLC CPU remotely. Flag appears when production halts.', hint: 'CPU stop function code', solves: 22, solved: false, hasExploit: true },
  { id: 'S7-03', name: 'Recipe Thief', category: 'S7comm', protocol: 'S7comm', points: 300, difficulty: 'hard', description: 'Extract production recipes from DB1. Flag is hidden in recipe data.', hint: 'Data blocks contain secrets', solves: 11, solved: false, hasExploit: true },
  { id: 'S7-04', name: 'Stuxnet Jr', category: 'S7comm', protocol: 'S7comm', points: 450, difficulty: 'expert', description: 'Modify PLC program to alter process behavior while hiding changes.', hint: 'Program injection requires deep knowledge', solves: 1, solved: false, hasExploit: false },
  { id: 'OPCUA-01', name: 'Browse Master', category: 'OPC UA', protocol: 'OPC UA', points: 100, difficulty: 'easy', description: 'Browse the OPC UA address space and find the hidden flag node.', hint: 'Anonymous access is enabled', solves: 28, solved: false, hasExploit: true },
  { id: 'OPCUA-02', name: 'Reactor Override', category: 'OPC UA', protocol: 'OPC UA', points: 250, difficulty: 'medium', description: 'Modify reactor temperature setpoint beyond safety limits.', hint: 'Find the Setpoint node', solves: 15, solved: false, hasExploit: true },
  { id: 'OPCUA-03', name: 'TRITON Lite', category: 'OPC UA', protocol: 'OPC UA', points: 400, difficulty: 'expert', description: 'Bypass safety instrumented system and trigger unsafe condition.', hint: 'Safety nodes have special protections', solves: 3, solved: false, hasExploit: true },
  { id: 'MQTT-01', name: 'Topic Hunter', category: 'MQTT', protocol: 'MQTT', points: 75, difficulty: 'easy', description: 'Subscribe to all topics and find the flag in sensor data.', hint: 'Use # wildcard', solves: 42, solved: true, hasExploit: true },
  { id: 'MQTT-02', name: 'Sensor Spoof', category: 'MQTT', protocol: 'MQTT', points: 150, difficulty: 'medium', description: 'Publish fake sensor data to trigger false alarms.', hint: 'Observe the topic structure first', solves: 26, solved: false, hasExploit: true },
  { id: 'MQTT-03', name: 'Gateway Takeover', category: 'MQTT', protocol: 'MQTT', points: 250, difficulty: 'hard', description: 'Compromise edge gateway using exposed configuration topics.', hint: 'Config topics contain secrets', solves: 9, solved: false, hasExploit: true },
  { id: 'MQTT-04', name: 'Firmware Injection', category: 'MQTT', protocol: 'MQTT', points: 350, difficulty: 'expert', description: 'Inject malicious firmware update via OTA topic.', hint: 'Understand the update protocol', solves: 4, solved: false, hasExploit: false },
  { id: 'HIST-01', name: 'SQL Injection 101', category: 'Historian', protocol: 'HTTP', points: 150, difficulty: 'medium', description: 'Exploit SQL injection in historian API to extract flag.', hint: 'Try the tag query endpoint', solves: 33, solved: false, hasExploit: true },
  { id: 'HIST-02', name: 'Data Exfil', category: 'Historian', protocol: 'HTTP', points: 250, difficulty: 'hard', description: 'Extract 24 hours of process data. Flag in oldest record.', hint: 'UNION-based injection', solves: 14, solved: false, hasExploit: true },
  { id: 'HIST-03', name: 'Evidence Destroyer', category: 'Historian', protocol: 'HTTP', points: 400, difficulty: 'expert', description: 'Delete specific historical records without detection.', hint: 'Avoid triggering audit logs', solves: 5, solved: false, hasExploit: true },
  { id: 'FOR-01', name: 'Timeline Builder', category: 'Forensics', protocol: 'Multiple', points: 200, difficulty: 'medium', description: 'Build attack timeline from provided evidence. Submit timestamp of initial access.', hint: 'Correlate logs across systems', solves: 18, solved: false, hasExploit: false },
  { id: 'FOR-02', name: 'IOC Extractor', category: 'Forensics', protocol: 'Multiple', points: 250, difficulty: 'medium', description: 'Extract all indicators of compromise from attack evidence.', hint: 'Look for unusual patterns', solves: 12, solved: false, hasExploit: false },
  { id: 'FOR-03', name: 'APT Attribution', category: 'Forensics', protocol: 'Multiple', points: 300, difficulty: 'expert', description: 'Identify the APT campaign from TTPs. Flag is campaign name.', hint: 'MITRE ATT&CK mapping helps', solves: 7, solved: false, hasExploit: false }
];

const teams: Team[] = [
  { rank: 1, name: 'OT_Pwners', score: 3250, solves: 18, lastSolve: '14:32' },
  { rank: 2, name: 'GridHackers', score: 2800, solves: 15, lastSolve: '14:28' },
  { rank: 3, name: 'SCADA_Squad', score: 2450, solves: 14, lastSolve: '14:15' },
  { rank: 4, name: 'ICS_Ninjas', score: 2100, solves: 12, lastSolve: '13:58' },
  { rank: 5, name: 'PLCBreakers', score: 1850, solves: 11, lastSolve: '13:45' }
];

const achievements = [
  { id: 'first_blood', name: 'First Blood', description: 'First to solve a challenge', icon: '🩸', unlocked: true },
  { id: 'protocol_master', name: 'Protocol Master', description: 'Solve all challenges in one protocol', icon: '🎓', unlocked: false },
  { id: 'hard_hitter', name: 'Hard Hitter', description: 'Solve 5 hard challenges', icon: '💪', unlocked: false },
  { id: 'elite', name: 'Elite Hacker', description: 'Solve an expert challenge', icon: '👑', unlocked: false },
  { id: 'completionist', name: 'Completionist', description: 'Solve all challenges', icon: '🏆', unlocked: false }
];

const difficultyColors: Record<string, string> = {
  easy: 'bg-green-500/20 text-green-400 border-green-500/50',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
  hard: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
  expert: 'bg-red-500/20 text-red-400 border-red-500/50'
};

const categoryColors: Record<string, string> = {
  'Modbus': 'text-blue-400', 'DNP3': 'text-yellow-400', 'S7comm': 'text-orange-400',
  'OPC UA': 'text-purple-400', 'MQTT': 'text-green-400', 'Historian': 'text-cyan-400', 'Forensics': 'text-pink-400'
};

export default function CTFPage() {
  const [activeTab, setActiveTab] = useState<'challenges' | 'leaderboard' | 'progress'>('challenges');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [flagInput, setFlagInput] = useState<string>('');
  const [selectedChallenge, setSelectedChallenge] = useState<Challenge | null>(null);

  const categories = ['All', ...Array.from(new Set(challenges.map(c => c.category)))];
  const filteredChallenges = selectedCategory === 'All' ? challenges : challenges.filter(c => c.category === selectedCategory);
  
  const userScore = challenges.filter(c => c.solved).reduce((sum, c) => sum + c.points, 0);
  const userSolves = challenges.filter(c => c.solved).length;

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">🏁 VULNOT CTF</h1>
          <p className="text-slate-400">Capture The Flag • OT Security Challenges • Mjolnir Training</p>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-cyan-400">{userScore}</div>
            <div className="text-xs text-slate-500">Your Score</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">{userSolves}/{challenges.length}</div>
            <div className="text-xs text-slate-500">Solved</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">#4</div>
            <div className="text-xs text-slate-500">Rank</div>
          </div>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        {['challenges', 'leaderboard', 'progress'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab as typeof activeTab)}
            className={`px-4 py-2 rounded font-medium capitalize ${activeTab === tab ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'challenges' && (
        <>
          <div className="flex gap-2 mb-4 flex-wrap">
            {categories.map(cat => (
              <button key={cat} onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 rounded text-sm ${selectedCategory === cat ? 'bg-cyan-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}`}>
                {cat}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-3 gap-4">
            {filteredChallenges.map(challenge => (
              <div key={challenge.id} onClick={() => setSelectedChallenge(challenge)}
                className={`bg-slate-900 border rounded-lg p-4 cursor-pointer transition-all hover:border-cyan-500/50 ${challenge.solved ? 'border-green-500/50 opacity-75' : 'border-slate-700'}`}>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className={`text-sm font-mono ${categoryColors[challenge.category]}`}>{challenge.id}</span>
                    <h3 className="font-bold text-lg">{challenge.name}</h3>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-cyan-400">{challenge.points}</div>
                    <div className="text-xs text-slate-500">points</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`px-2 py-0.5 rounded text-xs border ${difficultyColors[challenge.difficulty]}`}>
                    {challenge.difficulty}
                  </span>
                  <span className="text-xs text-slate-500">{challenge.protocol}</span>
                  {challenge.hasExploit && <span className="text-xs text-green-400">🛠️ Exploit</span>}
                </div>
                <p className="text-slate-400 text-sm mb-3 line-clamp-2">{challenge.description}</p>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500">{challenge.solves} solves</span>
                  {challenge.solved && <span className="text-green-400 text-sm">✓ Solved</span>}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === 'leaderboard' && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-800">
              <tr>
                <th className="p-4 text-left text-slate-400">Rank</th>
                <th className="p-4 text-left text-slate-400">Team</th>
                <th className="p-4 text-right text-slate-400">Score</th>
                <th className="p-4 text-right text-slate-400">Solves</th>
                <th className="p-4 text-right text-slate-400">Last Solve</th>
              </tr>
            </thead>
            <tbody>
              {teams.map(team => (
                <tr key={team.rank} className="border-t border-slate-700 hover:bg-slate-800/50">
                  <td className="p-4">
                    <span className={`font-bold ${team.rank === 1 ? 'text-yellow-400' : team.rank === 2 ? 'text-slate-300' : team.rank === 3 ? 'text-orange-400' : 'text-slate-500'}`}>
                      {team.rank === 1 ? '🥇' : team.rank === 2 ? '🥈' : team.rank === 3 ? '🥉' : `#${team.rank}`}
                    </span>
                  </td>
                  <td className="p-4 font-bold text-cyan-400">{team.name}</td>
                  <td className="p-4 text-right font-mono text-green-400">{team.score}</td>
                  <td className="p-4 text-right text-slate-400">{team.solves}</td>
                  <td className="p-4 text-right font-mono text-slate-500">{team.lastSolve}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'progress' && (
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h2 className="text-lg font-bold text-cyan-400 mb-4">📊 Category Progress</h2>
            {categories.filter(c => c !== 'All').map(cat => {
              const catChallenges = challenges.filter(c => c.category === cat);
              const solved = catChallenges.filter(c => c.solved).length;
              const progress = (solved / catChallenges.length) * 100;
              return (
                <div key={cat} className="mb-4">
                  <div className="flex justify-between mb-1">
                    <span className={categoryColors[cat]}>{cat}</span>
                    <span className="text-slate-400">{solved}/{catChallenges.length}</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div className="bg-cyan-500 h-2 rounded-full" style={{ width: `${progress}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
            <h2 className="text-lg font-bold text-purple-400 mb-4">🏆 Achievements</h2>
            <div className="grid grid-cols-2 gap-3">
              {achievements.map(ach => (
                <div key={ach.id} className={`p-3 rounded-lg border ${ach.unlocked ? 'bg-purple-500/20 border-purple-500/50' : 'bg-slate-800 border-slate-700 opacity-50'}`}>
                  <div className="text-2xl mb-1">{ach.icon}</div>
                  <div className="font-bold text-sm">{ach.name}</div>
                  <div className="text-xs text-slate-400">{ach.description}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {selectedChallenge && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50" onClick={() => setSelectedChallenge(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 max-w-lg w-full" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <span className={`text-sm font-mono ${categoryColors[selectedChallenge.category]}`}>{selectedChallenge.id}</span>
                <h2 className="text-xl font-bold">{selectedChallenge.name}</h2>
              </div>
              <div className="text-2xl font-bold text-cyan-400">{selectedChallenge.points} pts</div>
            </div>
            <div className="flex gap-2 mb-4">
              <span className={`px-2 py-0.5 rounded text-xs border ${difficultyColors[selectedChallenge.difficulty]}`}>{selectedChallenge.difficulty}</span>
              <span className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-400">{selectedChallenge.protocol}</span>
            </div>
            <p className="text-slate-300 mb-4">{selectedChallenge.description}</p>
            <div className="bg-slate-800 rounded p-3 mb-4">
              <div className="text-xs text-slate-500 mb-1">💡 Hint (-25% points)</div>
              <div className="text-slate-400 text-sm blur-sm hover:blur-none transition-all cursor-pointer">{selectedChallenge.hint}</div>
            </div>
            <div className="flex gap-2">
              <input type="text" placeholder="Enter flag..." value={flagInput} onChange={e => setFlagInput(e.target.value)}
                className="flex-1 bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white" />
              <button className="bg-cyan-600 hover:bg-cyan-500 px-4 py-2 rounded font-medium">Submit</button>
            </div>
            <button onClick={() => setSelectedChallenge(null)} className="mt-4 w-full text-slate-400 hover:text-white">Close</button>
          </div>
        </div>
      )}

      <div className="mt-6 text-center text-slate-600 text-sm">
        Developed by Milind Bhargava at Mjolnir Security • Training: training@mjolnirsecurity.com
      </div>
    </div>
  );
}

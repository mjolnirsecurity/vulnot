'use client';

import React, { useState, useEffect } from 'react';

interface PLCData {
  id: string; name: string; status: 'RUN' | 'STOP' | 'ERROR'; cpu: number; memory: number; cycleTime: number;
}

interface ProductionData {
  plcs: PLCData[];
  production: { total: number; target: number; rate: number; efficiency: number; quality: number; rejects: number };
  conveyors: Array<{ id: string; speed: number; status: boolean }>;
  robots: Array<{ id: string; status: 'WORKING' | 'IDLE' | 'ERROR'; position: string; cycles: number }>;
  alarms: Array<{ id: number; severity: string; message: string; time: string }>;
}

const initialData: ProductionData = {
  plcs: [
    { id: 'S7-1500-LINE1', name: 'Production Line 1', status: 'RUN', cpu: 45, memory: 62, cycleTime: 12 },
    { id: 'S7-1500-LINE2', name: 'Production Line 2', status: 'RUN', cpu: 52, memory: 58, cycleTime: 14 }
  ],
  production: { total: 847, target: 1000, rate: 120, efficiency: 94.2, quality: 99.1, rejects: 8 },
  conveyors: [
    { id: 'CONV-01', speed: 1.2, status: true },
    { id: 'CONV-02', speed: 1.5, status: true },
    { id: 'CONV-03', speed: 1.2, status: true }
  ],
  robots: [
    { id: 'ROBOT-A1', status: 'WORKING', position: 'X:150 Y:200 Z:50', cycles: 4521 },
    { id: 'ROBOT-A2', status: 'WORKING', position: 'X:300 Y:150 Z:75', cycles: 4518 },
    { id: 'ROBOT-B1', status: 'IDLE', position: 'HOME', cycles: 3892 }
  ],
  alarms: [
    { id: 1, severity: 'info', message: 'Shift change in 30 minutes', time: '14:30' },
    { id: 2, severity: 'warning', message: 'ROBOT-B1 waiting for parts', time: '14:15' }
  ]
};

const PLCCard = ({ plc, onStop }: { plc: PLCData; onStop: () => void }) => {
  const statusColors = { RUN: 'bg-green-500', STOP: 'bg-red-500', ERROR: 'bg-yellow-500 animate-pulse' };
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-lg p-4">
      <div className="flex justify-between items-center mb-3">
        <div>
          <div className="font-mono text-cyan-400 text-sm">{plc.id}</div>
          <div className="text-slate-300">{plc.name}</div>
        </div>
        <div className={`px-3 py-1 rounded text-xs font-bold text-white ${statusColors[plc.status]}`}>{plc.status}</div>
      </div>
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="text-center">
          <div className="text-xs text-slate-500">CPU</div>
          <div className="text-cyan-300 font-mono">{plc.cpu}%</div>
          <div className="w-full bg-slate-700 rounded-full h-1 mt-1">
            <div className="bg-cyan-500 h-1 rounded-full" style={{ width: `${plc.cpu}%` }}></div>
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-500">Memory</div>
          <div className="text-cyan-300 font-mono">{plc.memory}%</div>
          <div className="w-full bg-slate-700 rounded-full h-1 mt-1">
            <div className="bg-purple-500 h-1 rounded-full" style={{ width: `${plc.memory}%` }}></div>
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-500">Cycle</div>
          <div className="text-cyan-300 font-mono">{plc.cycleTime}ms</div>
        </div>
      </div>
      <button onClick={onStop} className={`w-full py-2 rounded text-sm font-medium ${
        plc.status === 'RUN' ? 'bg-red-600 hover:bg-red-500' : 'bg-green-600 hover:bg-green-500'
      }`}>
        {plc.status === 'RUN' ? '⏹ STOP CPU' : '▶ START CPU'}
      </button>
    </div>
  );
};

const ConveyorAnimation = ({ conveyor }: { conveyor: { id: string; speed: number; status: boolean } }) => (
  <div className="bg-slate-800 rounded p-3">
    <div className="flex justify-between items-center mb-2">
      <span className="text-sm font-mono text-cyan-400">{conveyor.id}</span>
      <span className={`text-xs ${conveyor.status ? 'text-green-400' : 'text-red-400'}`}>
        {conveyor.status ? 'RUNNING' : 'STOPPED'}
      </span>
    </div>
    <div className="h-6 bg-slate-700 rounded overflow-hidden relative">
      {conveyor.status && (
        <div className="absolute inset-0 flex">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="w-4 h-full border-r border-slate-600 animate-conveyor"
              style={{ animationDuration: `${2 / conveyor.speed}s` }}></div>
          ))}
        </div>
      )}
    </div>
    <div className="text-center text-xs text-slate-500 mt-1">{conveyor.speed} m/s</div>
  </div>
);

const RobotStatus = ({ robot }: { robot: { id: string; status: string; position: string; cycles: number } }) => {
  const statusColors: Record<string, string> = { WORKING: 'text-green-400', IDLE: 'text-yellow-400', ERROR: 'text-red-400' };
  return (
    <div className="bg-slate-800 rounded p-3">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-mono text-cyan-400">{robot.id}</span>
        <span className={`text-xs font-bold ${statusColors[robot.status]}`}>{robot.status}</span>
      </div>
      <div className="text-xs text-slate-500">Position</div>
      <div className="text-cyan-300 font-mono text-xs mb-2">{robot.position}</div>
      <div className="flex justify-between text-xs">
        <span className="text-slate-500">Cycles:</span>
        <span className="text-cyan-300">{robot.cycles.toLocaleString()}</span>
      </div>
    </div>
  );
};

export default function FactoryPage() {
  const [data, setData] = useState<ProductionData>(initialData);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [attackMode, setAttackMode] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
      setData(prev => ({
        ...prev,
        production: {
          ...prev.production,
          total: prev.plcs.some(p => p.status === 'RUN') ? prev.production.total + Math.floor(Math.random() * 3) : prev.production.total,
          rate: prev.plcs.some(p => p.status === 'RUN') ? 115 + Math.random() * 10 : 0,
          efficiency: 93 + Math.random() * 3
        },
        plcs: prev.plcs.map(p => ({
          ...p,
          cpu: p.status === 'RUN' ? Math.max(20, Math.min(80, p.cpu + (Math.random() - 0.5) * 10)) : 5,
          cycleTime: p.status === 'RUN' ? Math.max(8, Math.min(20, p.cycleTime + (Math.random() - 0.5) * 2)) : 0
        })),
        robots: prev.robots.map(r => ({
          ...r,
          cycles: r.status === 'WORKING' ? r.cycles + 1 : r.cycles
        }))
      }));
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  const togglePLC = (id: string) => {
    setData(prev => ({
      ...prev,
      plcs: prev.plcs.map(p => p.id === id ? { ...p, status: p.status === 'RUN' ? 'STOP' as const : 'RUN' as const } : p),
      alarms: [{ id: Date.now(), severity: 'warning', message: `PLC ${id} state changed`, time: currentTime.toLocaleTimeString() }, ...prev.alarms]
    }));
  };

  const simulateAttack = () => {
    setAttackMode(true);
    setData(prev => ({
      ...prev,
      alarms: [
        { id: Date.now(), severity: 'critical', message: '⚠️ UNAUTHORIZED S7COMM CONNECTION DETECTED', time: currentTime.toLocaleTimeString() },
        { id: Date.now() + 1, severity: 'critical', message: '⚠️ CPU STOP COMMAND RECEIVED FROM UNKNOWN SOURCE', time: currentTime.toLocaleTimeString() },
        ...prev.alarms
      ]
    }));
    setTimeout(() => {
      setData(prev => ({
        ...prev,
        plcs: prev.plcs.map(p => ({ ...p, status: 'STOP' as const })),
        conveyors: prev.conveyors.map(c => ({ ...c, status: false })),
        robots: prev.robots.map(r => ({ ...r, status: 'IDLE' as const }))
      }));
      setAttackMode(false);
    }, 2000);
  };

  const progress = (data.production.total / data.production.target) * 100;

  return (
    <div className={`min-h-screen bg-slate-950 text-white p-6 ${attackMode ? 'bg-red-950 animate-pulse' : ''}`}>
      <style jsx>{`
        @keyframes conveyor { from { transform: translateX(0); } to { transform: translateX(-16px); } }
        .animate-conveyor { animation: conveyor linear infinite; }
      `}</style>

      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">🏭 Manufacturing Line - HMI</h1>
          <p className="text-slate-400">Mjolnir Training • Scenario 3 • S7comm :102</p>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={simulateAttack} className="bg-red-600 hover:bg-red-500 px-4 py-2 rounded text-sm font-medium">
            🎯 Simulate Attack
          </button>
          <div className="text-right">
            <div className="text-xl font-mono text-cyan-300">{currentTime.toLocaleTimeString()}</div>
            <div className="text-slate-500 text-sm">Network: 10.0.3.0/24</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-6 gap-4 mb-6">
        {[
          { label: 'Production', value: data.production.total.toLocaleString(), sub: `Target: ${data.production.target}`, color: 'text-cyan-400' },
          { label: 'Rate', value: `${data.production.rate.toFixed(0)}/hr`, sub: 'Units per hour', color: 'text-green-400' },
          { label: 'Efficiency', value: `${data.production.efficiency.toFixed(1)}%`, sub: 'OEE', color: 'text-purple-400' },
          { label: 'Quality', value: `${data.production.quality.toFixed(1)}%`, sub: 'First pass', color: 'text-blue-400' },
          { label: 'Rejects', value: data.production.rejects.toString(), sub: 'This shift', color: 'text-orange-400' },
          { label: 'PLCs Online', value: `${data.plcs.filter(p => p.status === 'RUN').length}/${data.plcs.length}`, sub: 'Status', color: data.plcs.every(p => p.status === 'RUN') ? 'text-green-400' : 'text-red-400' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-3">
            <div className="text-slate-400 text-xs">{s.label}</div>
            <div className={`text-xl font-bold font-mono ${s.color}`}>{s.value}</div>
            <div className="text-slate-500 text-xs">{s.sub}</div>
          </div>
        ))}
      </div>

      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-slate-400">Production Progress</span>
          <span className="text-cyan-400">{progress.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-4 overflow-hidden">
          <div className="bg-gradient-to-r from-cyan-500 to-green-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, progress)}%` }}></div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h2 className="text-lg font-bold text-orange-400 mb-4">🖥️ PLC Controllers</h2>
          <div className="space-y-4">
            {data.plcs.map(plc => <PLCCard key={plc.id} plc={plc} onStop={() => togglePLC(plc.id)} />)}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h2 className="text-lg font-bold text-blue-400 mb-4">🛤️ Conveyor System</h2>
          <div className="space-y-4">
            {data.conveyors.map(conv => <ConveyorAnimation key={conv.id} conveyor={conv} />)}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h2 className="text-lg font-bold text-purple-400 mb-4">🤖 Robot Arms</h2>
          <div className="space-y-4">
            {data.robots.map(robot => <RobotStatus key={robot.id} robot={robot} />)}
          </div>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
        <h2 className="text-lg font-bold text-red-400 mb-4">🚨 Alarm Log</h2>
        <div className="space-y-2 max-h-32 overflow-y-auto">
          {data.alarms.slice(0, 8).map(alarm => (
            <div key={alarm.id} className={`flex justify-between items-center p-2 rounded text-sm ${
              alarm.severity === 'critical' ? 'bg-red-500/20' : alarm.severity === 'warning' ? 'bg-yellow-500/20' : 'bg-blue-500/20'
            }`}>
              <span className="text-slate-300">{alarm.message}</span>
              <span className="text-slate-500 font-mono">{alarm.time}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 text-center text-slate-600 text-sm">
        Developed by Milind Bhargava at Mjolnir Security • Training: training@mjolnirsecurity.com
      </div>
    </div>
  );
}

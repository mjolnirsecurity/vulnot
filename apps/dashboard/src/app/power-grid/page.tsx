'use client';

import React, { useState, useEffect } from 'react';

interface Breaker {
  id: string; name: string; status: 'CLOSED' | 'OPEN' | 'TRIP'; voltage: number; current: number; power: number;
}

interface SubstationData {
  breakers: Breaker[];
  frequency: number; load: number; temperature: number;
  alarms: Array<{ id: number; severity: string; message: string; time: string }>;
}

const initialData: SubstationData = {
  breakers: [
    { id: 'CB-101', name: 'Main Feeder 1', status: 'CLOSED', voltage: 138.2, current: 245, power: 33.8 },
    { id: 'CB-102', name: 'Main Feeder 2', status: 'CLOSED', voltage: 137.8, current: 198, power: 27.3 },
    { id: 'CB-201', name: 'Bus Tie', status: 'OPEN', voltage: 0, current: 0, power: 0 },
    { id: 'CB-301', name: 'Distribution 1', status: 'CLOSED', voltage: 13.8, current: 520, power: 7.2 },
    { id: 'CB-302', name: 'Distribution 2', status: 'CLOSED', voltage: 13.8, current: 485, power: 6.7 },
    { id: 'CB-303', name: 'Distribution 3', status: 'CLOSED', voltage: 13.8, current: 410, power: 5.7 }
  ],
  frequency: 60.02, load: 78, temperature: 45,
  alarms: [
    { id: 1, severity: 'info', message: 'Routine maintenance scheduled for CB-201', time: '08:00' },
    { id: 2, severity: 'warning', message: 'CB-301 current approaching limit', time: '14:22' }
  ]
};

const BreakerSymbol = ({ breaker, onToggle }: { breaker: Breaker; onToggle: () => void }) => {
  const statusColors = { CLOSED: 'text-green-400', OPEN: 'text-red-400', TRIP: 'text-yellow-400 animate-pulse' };
  const bgColors = { CLOSED: 'bg-green-500/20 border-green-500', OPEN: 'bg-red-500/20 border-red-500', TRIP: 'bg-yellow-500/20 border-yellow-500' };
  
  return (
    <div className={`bg-slate-800 border-2 ${bgColors[breaker.status]} rounded-lg p-4 cursor-pointer hover:opacity-80 transition-all`}
      onClick={onToggle}>
      <div className="flex justify-between items-center mb-2">
        <span className="font-mono text-cyan-400">{breaker.id}</span>
        <span className={`text-sm font-bold ${statusColors[breaker.status]}`}>{breaker.status}</span>
      </div>
      <div className="text-sm text-slate-300 mb-3">{breaker.name}</div>
      <div className="flex justify-center mb-3">
        <svg width="60" height="40" viewBox="0 0 60 40">
          <line x1="5" y1="20" x2="20" y2="20" stroke="#06b6d4" strokeWidth="3"/>
          <line x1="40" y1="20" x2="55" y2="20" stroke="#06b6d4" strokeWidth="3"/>
          {breaker.status === 'CLOSED' ? (
            <line x1="20" y1="20" x2="40" y2="20" stroke="#22c55e" strokeWidth="3"/>
          ) : (
            <line x1="20" y1="20" x2="35" y2="8" stroke="#ef4444" strokeWidth="3"/>
          )}
          <circle cx="20" cy="20" r="4" fill={breaker.status === 'CLOSED' ? '#22c55e' : '#ef4444'}/>
          <circle cx="40" cy="20" r="4" fill={breaker.status === 'CLOSED' ? '#22c55e' : '#ef4444'}/>
        </svg>
      </div>
      <div className="grid grid-cols-3 gap-1 text-xs">
        <div className="text-center"><div className="text-slate-500">V</div><div className="text-cyan-300">{breaker.voltage.toFixed(1)}</div></div>
        <div className="text-center"><div className="text-slate-500">A</div><div className="text-cyan-300">{breaker.current}</div></div>
        <div className="text-center"><div className="text-slate-500">MW</div><div className="text-cyan-300">{breaker.power.toFixed(1)}</div></div>
      </div>
    </div>
  );
};

export default function PowerGridPage() {
  const [data, setData] = useState<SubstationData>(initialData);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [attackActive, setAttackActive] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
      setData(prev => ({
        ...prev,
        frequency: 59.95 + Math.random() * 0.1,
        load: Math.max(50, Math.min(95, prev.load + (Math.random() - 0.5) * 2)),
        temperature: Math.max(30, Math.min(60, prev.temperature + (Math.random() - 0.5))),
        breakers: prev.breakers.map(b => ({
          ...b,
          current: b.status === 'CLOSED' ? Math.max(0, b.current + (Math.random() - 0.5) * 20) : 0,
          voltage: b.status === 'CLOSED' ? b.id.startsWith('CB-1') ? 137 + Math.random() * 2 : 13.5 + Math.random() * 0.5 : 0
        }))
      }));
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  const toggleBreaker = (id: string) => {
    setData(prev => ({
      ...prev,
      breakers: prev.breakers.map(b => b.id === id ? { ...b, status: b.status === 'CLOSED' ? 'OPEN' : 'CLOSED' } : b),
      alarms: [{ id: Date.now(), severity: 'warning', message: `Breaker ${id} state change`, time: currentTime.toLocaleTimeString() }, ...prev.alarms]
    }));
  };

  const simulateUkraineAttack = () => {
    setAttackActive(true);
    setData(prev => ({
      ...prev,
      alarms: [
        { id: Date.now(), severity: 'critical', message: '⚠️ UNAUTHORIZED DNP3 DIRECT OPERATE COMMAND DETECTED', time: currentTime.toLocaleTimeString() },
        { id: Date.now() + 1, severity: 'critical', message: '⚠️ MULTIPLE BREAKER TRIP COMMANDS RECEIVED', time: currentTime.toLocaleTimeString() },
        ...prev.alarms
      ]
    }));
    setTimeout(() => {
      setData(prev => ({
        ...prev,
        breakers: prev.breakers.map(b => ({ ...b, status: 'TRIP' as const }))
      }));
    }, 1000);
    setTimeout(() => {
      setData(prev => ({
        ...prev,
        alarms: [{ id: Date.now(), severity: 'critical', message: '🔴 BLACKOUT - ALL BREAKERS TRIPPED', time: currentTime.toLocaleTimeString() }, ...prev.alarms]
      }));
      setAttackActive(false);
    }, 2000);
  };

  const totalPower = data.breakers.filter(b => b.status === 'CLOSED').reduce((sum, b) => sum + b.power, 0);

  return (
    <div className={`min-h-screen bg-slate-950 text-white p-6 ${attackActive ? 'bg-red-950' : ''}`}>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">⚡ Power Grid Substation - SCADA</h1>
          <p className="text-slate-400">Mjolnir Training • Scenario 2 • DNP3 :20000</p>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={simulateUkraineAttack} disabled={attackActive}
            className="bg-red-600 hover:bg-red-500 disabled:opacity-50 px-4 py-2 rounded text-sm font-medium">
            🎯 Ukraine 2015 Attack
          </button>
          <div className="text-right">
            <div className="text-xl font-mono text-cyan-300">{currentTime.toLocaleTimeString()}</div>
            <div className="text-slate-500 text-sm">Network: 10.0.2.0/24</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        {[
          { label: 'System Frequency', value: `${data.frequency.toFixed(2)} Hz`, color: Math.abs(data.frequency - 60) > 0.05 ? 'text-yellow-400' : 'text-green-400' },
          { label: 'Total Load', value: `${data.load.toFixed(1)}%`, color: data.load > 90 ? 'text-red-400' : 'text-cyan-400' },
          { label: 'Total Power', value: `${totalPower.toFixed(1)} MW`, color: 'text-purple-400' },
          { label: 'Transformer Temp', value: `${data.temperature.toFixed(0)}°C`, color: data.temperature > 55 ? 'text-orange-400' : 'text-green-400' },
          { label: 'Active Alarms', value: data.alarms.filter(a => a.severity === 'critical').length.toString(), color: 'text-red-400' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm">{s.label}</div>
            <div className={`text-2xl font-bold font-mono ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
          <h2 className="text-lg font-bold text-yellow-400 mb-4">🔌 138kV High Voltage Bus</h2>
          <div className="grid grid-cols-3 gap-4">
            {data.breakers.filter(b => b.id.startsWith('CB-1') || b.id.startsWith('CB-2')).map(breaker => (
              <BreakerSymbol key={breaker.id} breaker={breaker} onToggle={() => toggleBreaker(breaker.id)} />
            ))}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
          <h2 className="text-lg font-bold text-green-400 mb-4">🏠 13.8kV Distribution Bus</h2>
          <div className="grid grid-cols-3 gap-4">
            {data.breakers.filter(b => b.id.startsWith('CB-3')).map(breaker => (
              <BreakerSymbol key={breaker.id} breaker={breaker} onToggle={() => toggleBreaker(breaker.id)} />
            ))}
          </div>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
        <h2 className="text-lg font-bold text-orange-400 mb-4">🚨 Event Log</h2>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {data.alarms.slice(0, 10).map(alarm => (
            <div key={alarm.id} className={`flex items-center justify-between p-2 rounded text-sm ${
              alarm.severity === 'critical' ? 'bg-red-500/20 text-red-300' :
              alarm.severity === 'warning' ? 'bg-yellow-500/20 text-yellow-300' : 'bg-blue-500/20 text-blue-300'
            }`}>
              <span>{alarm.message}</span>
              <span className="font-mono text-slate-500">{alarm.time}</span>
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

'use client';

import React, { useState, useEffect } from 'react';

interface ProcessData {
  intake: { level: number; flowRate: number; pumpStatus: boolean; valvePosition: number };
  treatment: { chlorineLevel: number; phLevel: number; turbidity: number; dosingRate: number };
  distribution: { pressure: number; flowRate: number; pumpStatus: boolean; tankLevel: number };
  alarms: Array<{ id: number; severity: string; message: string; timestamp: string; acknowledged: boolean }>;
}

const initialData: ProcessData = {
  intake: { level: 72.5, flowRate: 2500, pumpStatus: true, valvePosition: 85 },
  treatment: { chlorineLevel: 2.1, phLevel: 7.2, turbidity: 0.3, dosingRate: 45 },
  distribution: { pressure: 45, flowRate: 2350, pumpStatus: true, tankLevel: 68 },
  alarms: [
    { id: 1, severity: 'warning', message: 'Intake tank level approaching high limit', timestamp: '14:32:15', acknowledged: false },
    { id: 2, severity: 'info', message: 'Chlorine dosing pump maintenance due', timestamp: '13:45:22', acknowledged: true },
    { id: 3, severity: 'critical', message: 'UNAUTHORIZED MODBUS WRITE DETECTED', timestamp: '14:28:47', acknowledged: false }
  ]
};

const Tank = ({ level, label, color }: { level: number; label: string; color: string }) => (
  <div className="flex flex-col items-center">
    <div className="text-sm text-slate-400 mb-2">{label}</div>
    <div className="w-20 h-32 bg-slate-800 rounded-lg border-2 border-slate-600 relative overflow-hidden">
      <div className={`absolute bottom-0 left-0 right-0 ${color} transition-all duration-1000`}
        style={{ height: `${level}%` }}>
        <div className="absolute top-0 left-0 right-0 h-2 bg-white/20 animate-pulse"></div>
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-white font-bold text-lg drop-shadow-lg">{level.toFixed(1)}%</span>
      </div>
    </div>
  </div>
);

const Pump = ({ status, label }: { status: boolean; label: string }) => (
  <div className="flex flex-col items-center">
    <div className={`w-16 h-16 rounded-full border-4 flex items-center justify-center ${
      status ? 'border-green-500 bg-green-500/20' : 'border-red-500 bg-red-500/20'
    }`}>
      <div className={`text-2xl ${status ? 'animate-spin' : ''}`} style={{ animationDuration: '2s' }}>⚙️</div>
    </div>
    <div className="text-sm text-slate-400 mt-2">{label}</div>
    <div className={`text-xs font-bold ${status ? 'text-green-400' : 'text-red-400'}`}>
      {status ? 'RUNNING' : 'STOPPED'}
    </div>
  </div>
);

const Gauge = ({ value, min, max, label, unit, color }: { value: number; min: number; max: number; label: string; unit: string; color: string }) => {
  const percentage = ((value - min) / (max - min)) * 100;
  const rotation = (percentage / 100) * 180 - 90;
  return (
    <div className="flex flex-col items-center">
      <div className="text-sm text-slate-400 mb-2">{label}</div>
      <div className="relative w-24 h-12 overflow-hidden">
        <div className="absolute w-24 h-24 rounded-full border-8 border-slate-700 border-t-transparent" 
          style={{ transform: 'rotate(180deg)' }}></div>
        <div className={`absolute w-24 h-24 rounded-full border-8 border-transparent ${color}`}
          style={{ transform: `rotate(${rotation}deg)`, borderTopColor: 'currentColor', borderRightColor: 'currentColor' }}></div>
        <div className="absolute bottom-0 left-1/2 w-1 h-10 bg-white origin-bottom rounded"
          style={{ transform: `translateX(-50%) rotate(${rotation}deg)` }}></div>
      </div>
      <div className="text-xl font-bold text-white mt-1">{value.toFixed(1)}</div>
      <div className="text-xs text-slate-500">{unit}</div>
    </div>
  );
};

export default function WaterTreatmentPage() {
  const [data, setData] = useState<ProcessData>(initialData);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [attackMode, setAttackMode] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
      setData(prev => ({
        ...prev,
        intake: {
          ...prev.intake,
          level: Math.max(0, Math.min(100, prev.intake.level + (Math.random() - 0.5) * 2)),
          flowRate: Math.max(0, prev.intake.flowRate + (Math.random() - 0.5) * 50)
        },
        treatment: {
          ...prev.treatment,
          chlorineLevel: Math.max(0, Math.min(5, prev.treatment.chlorineLevel + (Math.random() - 0.5) * 0.1)),
          phLevel: Math.max(6, Math.min(8, prev.treatment.phLevel + (Math.random() - 0.5) * 0.05))
        },
        distribution: {
          ...prev.distribution,
          pressure: Math.max(20, Math.min(80, prev.distribution.pressure + (Math.random() - 0.5) * 2)),
          tankLevel: Math.max(0, Math.min(100, prev.distribution.tankLevel + (Math.random() - 0.5) * 1))
        }
      }));
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  const simulateAttack = () => {
    setAttackMode(true);
    setData(prev => ({
      ...prev,
      treatment: { ...prev.treatment, chlorineLevel: 4.8, dosingRate: 100 },
      alarms: [
        { id: Date.now(), severity: 'critical', message: 'CHLORINE LEVEL CRITICAL - POSSIBLE ATTACK', timestamp: currentTime.toLocaleTimeString(), acknowledged: false },
        ...prev.alarms
      ]
    }));
    setTimeout(() => setAttackMode(false), 5000);
  };

  return (
    <div className={`min-h-screen bg-slate-950 text-white p-6 ${attackMode ? 'animate-pulse bg-red-950' : ''}`}>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400">💧 Water Treatment Plant - HMI</h1>
          <p className="text-slate-400">Mjolnir Training • Scenario 1 • Modbus TCP :502</p>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={simulateAttack} className="bg-red-600 hover:bg-red-500 px-4 py-2 rounded text-sm font-medium">
            🎯 Simulate Attack
          </button>
          <div className="text-right">
            <div className="text-xl font-mono text-cyan-300">{currentTime.toLocaleTimeString()}</div>
            <div className="text-slate-500 text-sm">Network: 10.0.1.0/24</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'System Status', value: attackMode ? 'UNDER ATTACK' : 'OPERATIONAL', color: attackMode ? 'text-red-400' : 'text-green-400' },
          { label: 'Total Flow', value: `${data.intake.flowRate.toFixed(0)} GPM`, color: 'text-cyan-400' },
          { label: 'Water Quality', value: data.treatment.turbidity < 0.5 ? 'EXCELLENT' : 'GOOD', color: 'text-green-400' },
          { label: 'Active Alarms', value: data.alarms.filter(a => !a.acknowledged).length.toString(), color: 'text-orange-400' }
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm">{s.label}</div>
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6 mb-6">
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
          <h2 className="text-lg font-bold text-blue-400 mb-4">🚰 Intake Zone</h2>
          <div className="flex justify-around items-end">
            <Tank level={data.intake.level} label="Reservoir" color="bg-blue-500" />
            <Pump status={data.intake.pumpStatus} label="Intake Pump" />
            <Gauge value={data.intake.flowRate} min={0} max={5000} label="Flow Rate" unit="GPM" color="text-blue-400" />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2">
            <div className="bg-slate-800 rounded p-2">
              <div className="text-xs text-slate-500">Valve Position</div>
              <div className="text-cyan-300 font-mono">{data.intake.valvePosition}%</div>
            </div>
            <div className="bg-slate-800 rounded p-2">
              <div className="text-xs text-slate-500">PLC Address</div>
              <div className="text-cyan-300 font-mono">10.0.1.10</div>
            </div>
          </div>
        </div>

        <div className={`bg-slate-900 border rounded-lg p-6 ${attackMode ? 'border-red-500 animate-pulse' : 'border-slate-700'}`}>
          <h2 className="text-lg font-bold text-green-400 mb-4">🧪 Treatment Zone</h2>
          <div className="grid grid-cols-2 gap-4">
            <Gauge value={data.treatment.chlorineLevel} min={0} max={5} label="Chlorine" unit="mg/L" 
              color={data.treatment.chlorineLevel > 4 ? 'text-red-400' : 'text-green-400'} />
            <Gauge value={data.treatment.phLevel} min={6} max={8} label="pH Level" unit="pH" color="text-purple-400" />
            <Gauge value={data.treatment.turbidity} min={0} max={2} label="Turbidity" unit="NTU" color="text-yellow-400" />
            <Gauge value={data.treatment.dosingRate} min={0} max={100} label="Dosing Rate" unit="%" 
              color={data.treatment.dosingRate > 80 ? 'text-red-400' : 'text-cyan-400'} />
          </div>
          <div className="mt-4 bg-slate-800 rounded p-2">
            <div className="text-xs text-slate-500">PLC Address</div>
            <div className="text-cyan-300 font-mono">10.0.1.11</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6">
          <h2 className="text-lg font-bold text-purple-400 mb-4">🏠 Distribution Zone</h2>
          <div className="flex justify-around items-end">
            <Tank level={data.distribution.tankLevel} label="Storage Tank" color="bg-purple-500" />
            <Pump status={data.distribution.pumpStatus} label="Dist. Pump" />
            <Gauge value={data.distribution.pressure} min={0} max={100} label="Pressure" unit="PSI" color="text-purple-400" />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2">
            <div className="bg-slate-800 rounded p-2">
              <div className="text-xs text-slate-500">Flow Rate</div>
              <div className="text-cyan-300 font-mono">{data.distribution.flowRate.toFixed(0)} GPM</div>
            </div>
            <div className="bg-slate-800 rounded p-2">
              <div className="text-xs text-slate-500">PLC Address</div>
              <div className="text-cyan-300 font-mono">10.0.1.12</div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
        <h2 className="text-lg font-bold text-orange-400 mb-4">🚨 Alarm Console</h2>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {data.alarms.map(alarm => (
            <div key={alarm.id} className={`flex items-center justify-between p-3 rounded ${
              alarm.severity === 'critical' ? 'bg-red-500/20 border border-red-500/50' :
              alarm.severity === 'warning' ? 'bg-yellow-500/20 border border-yellow-500/50' :
              'bg-blue-500/20 border border-blue-500/50'
            }`}>
              <div className="flex items-center gap-3">
                <span className={`w-3 h-3 rounded-full ${
                  alarm.severity === 'critical' ? 'bg-red-500 animate-pulse' :
                  alarm.severity === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                }`}></span>
                <span className="text-slate-300">{alarm.message}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-slate-500 text-sm font-mono">{alarm.timestamp}</span>
                {!alarm.acknowledged && (
                  <button className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded">ACK</button>
                )}
              </div>
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

'use client';

import { useEffect } from 'react';
import { useProcessStore } from '@/stores/processStore';
import { Tank } from '@/components/process/Tank';
import { Pump } from '@/components/process/Pump';
import { Valve } from '@/components/process/Valve';
import { SensorDisplay } from '@/components/process/SensorDisplay';
import { AlarmPanel } from '@/components/process/AlarmPanel';
import { TrendChart } from '@/components/charts/TrendChart';
import { ConnectionStatus } from '@/components/ui/ConnectionStatus';
import { Droplets, Activity, Thermometer, Gauge } from 'lucide-react';

export default function Dashboard() {
  const { tanks, pumps, valves, quality, process, addTrendPoint } = useProcessStore();

  // Simulate data updates for demo mode
  useEffect(() => {
    const interval = setInterval(() => {
      const variation = () => (Math.random() - 0.5) * 0.1;
      addTrendPoint('ph', quality.ph + variation());
      addTrendPoint('chlorine', quality.chlorine + variation() * 0.2);
      addTrendPoint('turbidity', Math.max(0, quality.turbidity + variation() * 0.05));
      addTrendPoint('flow_rate', process.flow_rate + variation() * 10);
      addTrendPoint('pressure', process.pressure + variation() * 2);
    }, 1000);
    return () => clearInterval(interval);
  }, [quality, process, addTrendPoint]);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Droplets className="w-8 h-8 text-blue-500" />
            <div>
              <h1 className="text-xl font-bold">VULNOT Water Treatment Facility</h1>
              <p className="text-sm text-gray-400">Real-time Process Control Dashboard</p>
            </div>
          </div>
          <ConnectionStatus />
        </div>
      </header>

      <main className="p-6">
        {/* Alarm Banner */}
        <div className="mb-6">
          <AlarmPanel />
        </div>

        {/* Process Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
          {/* Water Quality Sensors */}
          <div className="lg:col-span-1 space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              Water Quality
            </h2>
            <SensorDisplay label="pH Level" value={quality.ph} unit="pH" min={6.5} max={8.5} decimals={2} />
            <SensorDisplay label="Chlorine" value={quality.chlorine} unit="mg/L" min={0.2} max={4.0} decimals={2} />
            <SensorDisplay label="Turbidity" value={quality.turbidity} unit="NTU" max={4.0} decimals={2} />
            <SensorDisplay label="Temperature" value={quality.temperature} unit="°C" max={35} />
          </div>

          {/* Tanks */}
          <div className="lg:col-span-2">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Droplets className="w-5 h-5 text-blue-400" />
              Tank Levels
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(tanks).map(([name, tank]) => (
                <Tank
                  key={name}
                  name={name}
                  level={tank.level}
                  inflow={tank.inflow}
                  outflow={tank.outflow}
                />
              ))}
            </div>
          </div>

          {/* Process Variables */}
          <div className="lg:col-span-1 space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Gauge className="w-5 h-5 text-blue-400" />
              Process
            </h2>
            <SensorDisplay label="Flow Rate" value={process.flow_rate} unit="GPM" size="lg" />
            <SensorDisplay label="Pressure" value={process.pressure} unit="PSI" size="lg" />
          </div>
        </div>

        {/* Pumps and Valves */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Pumps */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Pumps</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
              {Object.entries(pumps).map(([name, pump]) => (
                <Pump
                  key={name}
                  name={name}
                  running={pump.running}
                  speed={pump.speed}
                  flow={pump.flow}
                />
              ))}
            </div>
          </div>

          {/* Valves */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Valves</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(valves).map(([name, valve]) => (
                <Valve key={name} name={name} position={valve.position} />
              ))}
            </div>
          </div>
        </div>

        {/* Trend Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <TrendChart tag="ph" label="pH Level" color="#3B82F6" min={6.5} max={8.5} unit="pH" />
          <TrendChart tag="chlorine" label="Chlorine Residual" color="#10B981" min={0.2} max={4.0} unit="mg/L" />
          <TrendChart tag="turbidity" label="Turbidity" color="#F59E0B" max={4.0} unit="NTU" />
          <TrendChart tag="flow_rate" label="Flow Rate" color="#8B5CF6" unit="GPM" />
          <TrendChart tag="pressure" label="System Pressure" color="#EC4899" unit="PSI" />
        </div>

        {/* Footer */}
        <footer className="mt-8 pt-6 border-t border-gray-700 text-center text-sm text-gray-500">
          <p>VULNOT v0.1.0 | Water Treatment Facility Scenario</p>
          <p className="text-yellow-500 mt-1">⚠️ This is an intentionally vulnerable training environment</p>
        </footer>
      </main>
    </div>
  );
}

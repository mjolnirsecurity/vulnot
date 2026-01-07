'use client';

import { useState, useEffect } from 'react';
import {
  Thermometer,
  Wind,
  Fan,
  Droplets,
  Sun,
  Lock,
  Unlock,
  AlertTriangle,
  TrendingUp,
  Building,
  Gauge,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface AHU {
  id: number;
  name: string;
  running: boolean;
  mode: string;
  supply_temp: number;
  supply_temp_setpoint: number;
  return_temp: number;
  supply_flow: number;
  supply_fan_speed: number;
  cooling_valve: number;
  heating_valve: number;
  outside_air_damper: number;
  filter_status: string;
}

interface Chiller {
  running: boolean;
  chilled_water_supply_temp: number;
  chilled_water_setpoint: number;
  power_consumption: number;
  tons: number;
}

interface BuildingState {
  timestamp: number;
  outside_temp: number;
  outside_humidity: number;
  ahus: AHU[];
  chiller: Chiller;
  lighting_zones: Record<string, number>;
  access_points: Record<string, boolean>;
  total_power: number;
  alarms: { level: string; message: string; tag: string }[];
}

// AHU Card Component
function AHUCard({ ahu }: { ahu: AHU }) {
  return (
    <div className={cn(
      'bg-gray-800 rounded-lg border p-4',
      ahu.running ? 'border-green-500/50' : 'border-red-500/50'
    )}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Fan className={cn(
            'w-5 h-5',
            ahu.running ? 'text-green-400 animate-spin' : 'text-gray-500'
          )} style={{ animationDuration: '3s' }} />
          <span className="font-bold text-gray-200">{ahu.name}</span>
        </div>
        <span className={cn(
          'px-2 py-0.5 rounded text-xs',
          ahu.mode === 'COOLING' && 'bg-blue-500/20 text-blue-400',
          ahu.mode === 'HEATING' && 'bg-orange-500/20 text-orange-400',
          ahu.mode === 'ECONOMIZER' && 'bg-green-500/20 text-green-400',
          ahu.mode === 'OFF' && 'bg-gray-500/20 text-gray-400',
        )}>
          {ahu.mode}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="flex items-center justify-between p-2 bg-gray-900 rounded">
          <span className="text-gray-400">Supply</span>
          <span className="text-cyan-400 font-mono">{ahu.supply_temp.toFixed(1)}°F</span>
        </div>
        <div className="flex items-center justify-between p-2 bg-gray-900 rounded">
          <span className="text-gray-400">Return</span>
          <span className="text-yellow-400 font-mono">{ahu.return_temp.toFixed(1)}°F</span>
        </div>
        <div className="flex items-center justify-between p-2 bg-gray-900 rounded">
          <span className="text-gray-400">Fan</span>
          <span className="text-green-400 font-mono">{ahu.supply_fan_speed.toFixed(0)}%</span>
        </div>
        <div className="flex items-center justify-between p-2 bg-gray-900 rounded">
          <span className="text-gray-400">Flow</span>
          <span className="text-blue-400 font-mono">{(ahu.supply_flow / 1000).toFixed(1)}k</span>
        </div>
      </div>

      {/* Valve Bars */}
      <div className="mt-3 space-y-2">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Cooling</span>
            <span className="text-blue-400">{ahu.cooling_valve.toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-gray-900 rounded overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all"
              style={{ width: `${ahu.cooling_valve}%` }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Heating</span>
            <span className="text-orange-400">{ahu.heating_valve.toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-gray-900 rounded overflow-hidden">
            <div
              className="h-full bg-orange-500 transition-all"
              style={{ width: `${ahu.heating_valve}%` }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-400">Outside Air</span>
            <span className="text-green-400">{ahu.outside_air_damper.toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-gray-900 rounded overflow-hidden">
            <div
              className="h-full bg-green-500 transition-all"
              style={{ width: `${ahu.outside_air_damper}%` }}
            />
          </div>
        </div>
      </div>

      {/* Filter Status */}
      <div className={cn(
        'mt-3 text-xs text-center py-1 rounded',
        ahu.filter_status === 'OK' && 'bg-green-500/10 text-green-400',
        ahu.filter_status === 'DIRTY' && 'bg-yellow-500/10 text-yellow-400',
        ahu.filter_status === 'REPLACE' && 'bg-red-500/10 text-red-400',
      )}>
        Filter: {ahu.filter_status}
      </div>
    </div>
  );
}

// Chiller Card Component
function ChillerCard({ chiller }: { chiller: Chiller }) {
  return (
    <div className={cn(
      'bg-gray-800 rounded-lg border p-4',
      chiller.running ? 'border-blue-500/50' : 'border-gray-600'
    )}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Droplets className={cn(
            'w-6 h-6',
            chiller.running ? 'text-blue-400' : 'text-gray-500'
          )} />
          <span className="font-bold text-gray-200">Chiller Plant</span>
        </div>
        <span className={cn(
          'px-2 py-1 rounded text-sm',
          chiller.running ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
        )}>
          {chiller.running ? 'RUNNING' : 'OFF'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-3 bg-gray-900 rounded">
          <div className="text-2xl font-bold text-blue-400">
            {chiller.chilled_water_supply_temp.toFixed(1)}°F
          </div>
          <div className="text-xs text-gray-400">CHW Supply</div>
          <div className="text-xs text-gray-500">SP: {chiller.chilled_water_setpoint}°F</div>
        </div>
        <div className="text-center p-3 bg-gray-900 rounded">
          <div className="text-2xl font-bold text-cyan-400">
            {chiller.tons.toFixed(0)}
          </div>
          <div className="text-xs text-gray-400">Tons</div>
        </div>
        <div className="text-center p-3 bg-gray-900 rounded col-span-2">
          <div className="text-xl font-bold text-yellow-400">
            {chiller.power_consumption.toFixed(0)} kW
          </div>
          <div className="text-xs text-gray-400">Power Consumption</div>
        </div>
      </div>
    </div>
  );
}

// Lighting Zone Component
function LightingZone({ name, level }: { name: string; level: number }) {
  return (
    <div className="flex items-center justify-between p-2 bg-gray-800 rounded">
      <div className="flex items-center gap-2">
        <Sun className={cn(
          'w-4 h-4',
          level > 50 ? 'text-yellow-400' : 'text-gray-500'
        )} />
        <span className="text-sm text-gray-300">{name}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-20 h-2 bg-gray-700 rounded overflow-hidden">
          <div
            className="h-full bg-yellow-500 transition-all"
            style={{ width: `${level}%` }}
          />
        </div>
        <span className="text-xs text-gray-400 w-8">{level.toFixed(0)}%</span>
      </div>
    </div>
  );
}

// Access Point Component
function AccessPoint({ name, locked }: { name: string; locked: boolean }) {
  return (
    <div className={cn(
      'flex items-center justify-between p-2 rounded',
      locked ? 'bg-green-500/10' : 'bg-red-500/10'
    )}>
      <span className="text-sm text-gray-300">{name}</span>
      {locked ? (
        <Lock className="w-4 h-4 text-green-400" />
      ) : (
        <Unlock className="w-4 h-4 text-red-400" />
      )}
    </div>
  );
}

export default function BuildingPage() {
  const [state, setState] = useState<BuildingState | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/building`);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setState(data);
      } catch (e) {
        console.error('Parse error:', e);
      }
    };

    return () => ws.close();
  }, []);

  // Mock data for development
  const mockState: BuildingState = {
    timestamp: Date.now(),
    outside_temp: 85,
    outside_humidity: 60,
    ahus: [
      { id: 1, name: 'AHU-1', running: true, mode: 'COOLING', supply_temp: 55, supply_temp_setpoint: 55, return_temp: 72, supply_flow: 15000, supply_fan_speed: 75, cooling_valve: 45, heating_valve: 0, outside_air_damper: 25, filter_status: 'OK' },
      { id: 2, name: 'AHU-2', running: true, mode: 'ECONOMIZER', supply_temp: 58, supply_temp_setpoint: 55, return_temp: 71, supply_flow: 14500, supply_fan_speed: 70, cooling_valve: 20, heating_valve: 0, outside_air_damper: 60, filter_status: 'DIRTY' },
      { id: 3, name: 'AHU-3', running: true, mode: 'COOLING', supply_temp: 54, supply_temp_setpoint: 55, return_temp: 73, supply_flow: 16000, supply_fan_speed: 80, cooling_valve: 55, heating_valve: 0, outside_air_damper: 20, filter_status: 'OK' },
      { id: 4, name: 'AHU-4', running: false, mode: 'OFF', supply_temp: 68, supply_temp_setpoint: 55, return_temp: 68, supply_flow: 0, supply_fan_speed: 0, cooling_valve: 0, heating_valve: 0, outside_air_damper: 0, filter_status: 'REPLACE' },
    ],
    chiller: { running: true, chilled_water_supply_temp: 44, chilled_water_setpoint: 44, power_consumption: 180, tons: 450 },
    lighting_zones: { 'Lobby': 100, 'Floor-1': 85, 'Floor-2': 85, 'Floor-3': 75, 'Parking': 50, 'Exterior': 100 },
    access_points: { 'Main-Entrance': true, 'Loading-Dock': false, 'Stairwell-A': true, 'Stairwell-B': true, 'Server-Room': true },
    total_power: 450,
    alarms: [{ level: 'MEDIUM', message: 'AHU-2 Filter Dirty', tag: 'AHU-2' }],
  };

  const data = state || mockState;

  return (
    <div className="min-h-screen bg-hmi-bg">
      {/* Header */}
      <header className="bg-hmi-panel border-b border-hmi-border px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Building className="w-8 h-8 text-cyan-400" />
            <div>
              <h1 className="text-xl font-bold text-white">
                Building Automation System
              </h1>
              <p className="text-xs text-gray-400">
                10-Story Office Building - BACnet/IP
              </p>
            </div>
          </div>

          {/* Weather */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Thermometer className="w-5 h-5 text-orange-400" />
              <span className="text-lg text-gray-200">{data.outside_temp.toFixed(0)}°F</span>
            </div>
            <div className="flex items-center gap-2">
              <Droplets className="w-5 h-5 text-blue-400" />
              <span className="text-lg text-gray-200">{data.outside_humidity.toFixed(0)}%</span>
            </div>
            <div className="flex items-center gap-2">
              <Gauge className="w-5 h-5 text-yellow-400" />
              <span className="text-lg text-gray-200">{data.total_power.toFixed(0)} kW</span>
            </div>
            <div className={cn(
              'w-3 h-3 rounded-full',
              connected ? 'bg-green-500' : 'bg-red-500'
            )} />
          </div>
        </div>
      </header>

      <div className="p-6">
        <div className="grid grid-cols-12 gap-6">
          {/* AHUs */}
          <div className="col-span-8">
            <h2 className="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2">
              <Wind className="w-5 h-5 text-cyan-400" />
              Air Handling Units
            </h2>
            <div className="grid grid-cols-2 gap-4">
              {data.ahus.map((ahu) => (
                <AHUCard key={ahu.id} ahu={ahu} />
              ))}
            </div>

            {/* Chiller */}
            <div className="mt-6">
              <ChillerCard chiller={data.chiller} />
            </div>
          </div>

          {/* Right Panel */}
          <div className="col-span-4 space-y-6">
            {/* Alarms */}
            <div className="bg-hmi-panel rounded-lg border border-hmi-border p-4">
              <h3 className="text-sm font-bold text-gray-200 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-400" />
                Active Alarms
              </h3>
              {data.alarms.length === 0 ? (
                <p className="text-sm text-gray-500">No active alarms</p>
              ) : (
                <div className="space-y-2">
                  {data.alarms.map((alarm, i) => (
                    <div
                      key={i}
                      className={cn(
                        'p-2 rounded text-sm',
                        alarm.level === 'HIGH' && 'bg-red-500/10 text-red-400',
                        alarm.level === 'MEDIUM' && 'bg-yellow-500/10 text-yellow-400',
                        alarm.level === 'LOW' && 'bg-blue-500/10 text-blue-400',
                      )}
                    >
                      [{alarm.tag}] {alarm.message}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Lighting */}
            <div className="bg-hmi-panel rounded-lg border border-hmi-border p-4">
              <h3 className="text-sm font-bold text-gray-200 mb-3 flex items-center gap-2">
                <Sun className="w-4 h-4 text-yellow-400" />
                Lighting Zones
              </h3>
              <div className="space-y-2">
                {Object.entries(data.lighting_zones).map(([name, level]) => (
                  <LightingZone key={name} name={name} level={level} />
                ))}
              </div>
            </div>

            {/* Access Control */}
            <div className="bg-hmi-panel rounded-lg border border-hmi-border p-4">
              <h3 className="text-sm font-bold text-gray-200 mb-3 flex items-center gap-2">
                <Lock className="w-4 h-4 text-green-400" />
                Access Points
              </h3>
              <div className="space-y-2">
                {Object.entries(data.access_points).map(([name, locked]) => (
                  <AccessPoint key={name} name={name} locked={locked} />
                ))}
              </div>
            </div>

            {/* Training Info */}
            <div className="bg-purple-500/10 rounded-lg border border-purple-500/30 p-4">
              <h3 className="text-sm font-bold text-purple-400 mb-2">Training Info</h3>
              <div className="text-xs text-gray-400 space-y-1">
                <p><span className="text-gray-500">Protocol:</span> BACnet/IP</p>
                <p><span className="text-gray-500">Port:</span> 47808 (UDP)</p>
                <p><span className="text-gray-500">Device ID:</span> 1</p>
                <p><span className="text-gray-500">Network:</span> 10.0.5.0/24</p>
                <p><span className="text-gray-500">Attacker:</span> 10.0.5.100</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-hmi-panel border-t border-hmi-border px-6 py-2 mt-6">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>VULNOT v0.3.0 - Building Automation</span>
          <span>Mjolnir Security - ⚠️ INTENTIONALLY VULNERABLE</span>
        </div>
      </footer>
    </div>
  );
}

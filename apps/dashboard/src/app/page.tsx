'use client';

import { useEffect } from 'react';
import { 
  Droplets, 
  Activity, 
  Gauge, 
  AlertTriangle,
  Wifi,
  WifiOff,
  RefreshCw,
  Settings
} from 'lucide-react';
import { useProcessStore } from '@/lib/store';
import { useWebSocket } from '@/hooks/useWebSocket';
import { cn } from '@/lib/utils';

// HMI Components
import { Tank } from '@/components/hmi/Tank';
import { Pump } from '@/components/hmi/Pump';
import { Valve } from '@/components/hmi/Valve';
import { Gauge as GaugeDisplay, DigitalDisplay } from '@/components/hmi/Gauge';
import { AlarmPanel, AlarmBanner } from '@/components/hmi/AlarmPanel';
import { TrendChart, MultiTrendChart } from '@/components/charts/TrendChart';

export default function WaterTreatmentHMI() {
  const { state, isConnected, history } = useProcessStore();
  const { sendCommand } = useWebSocket();

  // Format timestamp for display
  const formatTime = (ts: number) => new Date(ts * 1000).toLocaleTimeString();

  if (!state) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 mx-auto mb-4 animate-spin text-blue-500" />
          <h2 className="text-xl font-bold text-gray-300">Connecting to Process...</h2>
          <p className="text-gray-500 mt-2">Establishing connection to SCADA system</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-hmi-bg">
      {/* Alarm Banner */}
      <AlarmBanner />
      
      {/* Header */}
      <header className="bg-hmi-panel border-b border-hmi-border px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Droplets className="w-8 h-8 text-blue-400" />
            <div>
              <h1 className="text-xl font-bold text-white">
                VULNOT Water Treatment Plant
              </h1>
              <p className="text-xs text-gray-400">
                Municipal Water Treatment Facility - SCADA HMI
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            {/* Connection Status */}
            <div className={cn(
              'flex items-center gap-2 px-3 py-1 rounded-full text-sm',
              isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
            )}>
              {isConnected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              {isConnected ? 'ONLINE' : 'OFFLINE'}
            </div>
            
            {/* Timestamp */}
            <div className="text-sm text-gray-400 font-mono">
              {formatTime(state.timestamp)}
            </div>
            
            {/* Settings */}
            <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
              <Settings className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>
      </header>

      <div className="p-6">
        <div className="grid grid-cols-12 gap-6">
          
          {/* ============================================================ */}
          {/* LEFT COLUMN - Process Overview */}
          {/* ============================================================ */}
          <div className="col-span-8 space-y-6">
            
            {/* Process Flow Diagram */}
            <div className="bg-hmi-panel rounded-lg border border-hmi-border p-6">
              <h2 className="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-400" />
                Process Overview - Water Treatment Flow
              </h2>
              
              {/* Main Process Display */}
              <div className="flex items-end justify-between gap-4 overflow-x-auto pb-4">
                {/* Intake Section */}
                <div className="flex flex-col items-center gap-4 min-w-fit">
                  <div className="text-xs text-gray-400 font-mono">RAW WATER INTAKE</div>
                  <div className="flex items-end gap-4">
                    <Tank 
                      name="Intake Basin"
                      tag="LIT-101"
                      level={state.intake_level}
                      lowAlarm={25}
                      highAlarm={90}
                    />
                    <div className="flex flex-col gap-2">
                      <Pump 
                        name="P-101"
                        tag="HS-101"
                        running={state.pump_p101_running}
                        speed={state.pump_p101_speed}
                        onClick={() => sendCommand(1, 'pump_p101', state.pump_p101_running ? '0' : '1')}
                      />
                      <Pump 
                        name="P-102"
                        tag="HS-102"
                        running={state.pump_p102_running}
                        speed={state.pump_p102_speed}
                        onClick={() => sendCommand(1, 'pump_p102', state.pump_p102_running ? '0' : '1')}
                      />
                    </div>
                  </div>
                </div>

                {/* Arrow */}
                <div className="text-blue-400 text-2xl pb-16">→</div>

                {/* Treatment Section */}
                <div className="flex flex-col items-center gap-4 min-w-fit">
                  <div className="text-xs text-gray-400 font-mono">TREATMENT</div>
                  <div className="flex items-end gap-3">
                    <Tank 
                      name="Flash Mix"
                      tag="LIT-102"
                      level={state.flash_mix_level}
                    />
                    <Tank 
                      name="Floc Basin"
                      tag="LIT-103"
                      level={state.floc_level}
                    />
                    <Tank 
                      name="Sed Basin"
                      tag="LIT-104"
                      level={state.sed_level}
                    />
                  </div>
                </div>

                {/* Arrow */}
                <div className="text-blue-400 text-2xl pb-16">→</div>

                {/* Disinfection & Storage */}
                <div className="flex flex-col items-center gap-4 min-w-fit">
                  <div className="text-xs text-gray-400 font-mono">DISINFECTION</div>
                  <div className="flex items-end gap-4">
                    <Tank 
                      name="Cl2 Contact"
                      tag="LIT-105"
                      level={state.chlorine_contact_level}
                    />
                    <Valve 
                      name="Chem Inj"
                      tag="FCV-105"
                      position={state.valve_v105}
                    />
                  </div>
                </div>

                {/* Arrow */}
                <div className="text-blue-400 text-2xl pb-16">→</div>

                {/* Distribution */}
                <div className="flex flex-col items-center gap-4 min-w-fit">
                  <div className="text-xs text-gray-400 font-mono">DISTRIBUTION</div>
                  <div className="flex items-end gap-4">
                    <Tank 
                      name="Clearwell"
                      tag="LIT-106"
                      level={state.clearwell_level}
                      lowAlarm={20}
                      highAlarm={95}
                    />
                    <div className="flex flex-col gap-2">
                      <Pump 
                        name="P-301"
                        tag="HS-301"
                        running={state.pump_p301_running}
                        speed={state.pump_p301_speed}
                        onClick={() => sendCommand(3, 'pump_p301', state.pump_p301_running ? '0' : '1')}
                      />
                      <Pump 
                        name="P-302"
                        tag="HS-302"
                        running={state.pump_p302_running}
                        speed={state.pump_p302_speed}
                        onClick={() => sendCommand(3, 'pump_p302', state.pump_p302_running ? '0' : '1')}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Key Metrics Row */}
            <div className="grid grid-cols-4 gap-4">
              <GaugeDisplay 
                name="Distribution Pressure"
                tag="PIT-301"
                value={state.distribution_pressure}
                unit="PSI"
                min={0}
                max={100}
                lowAlarm={40}
                highAlarm={85}
              />
              <GaugeDisplay 
                name="Raw Water Flow"
                tag="FIT-101"
                value={state.raw_water_flow}
                unit="GPM"
                min={0}
                max={3000}
              />
              <GaugeDisplay 
                name="Chlorine Residual"
                tag="AIT-106"
                value={state.chlorine_residual}
                unit="mg/L"
                min={0}
                max={5}
                lowAlarm={0.5}
                highAlarm={3.5}
              />
              <GaugeDisplay 
                name="Treated pH"
                tag="AIT-105"
                value={state.ph_treated}
                unit="pH"
                min={6}
                max={9}
                lowAlarm={6.5}
                highAlarm={8.5}
                decimals={2}
              />
            </div>

            {/* Trend Charts */}
            <div className="grid grid-cols-2 gap-4">
              <TrendChart 
                title="Clearwell Level"
                data={history.timestamps.map((ts, i) => ({
                  timestamp: ts,
                  value: history.clearwell_level[i]
                }))}
                unit="%"
                color="#3b82f6"
                min={0}
                max={100}
                lowAlarm={20}
                highAlarm={95}
              />
              <TrendChart 
                title="Distribution Pressure"
                data={history.timestamps.map((ts, i) => ({
                  timestamp: ts,
                  value: history.distribution_pressure[i]
                }))}
                unit="PSI"
                color="#22c55e"
                min={0}
                max={100}
                lowAlarm={40}
                highAlarm={85}
              />
            </div>

            <MultiTrendChart 
              title="Flow Rates"
              series={[
                { name: 'Raw Water', data: history.raw_water_flow, color: '#3b82f6', unit: 'GPM' },
                { name: 'Distribution', data: history.distribution_flow, color: '#22c55e', unit: 'GPM' },
              ]}
              timestamps={history.timestamps}
            />
          </div>

          {/* ============================================================ */}
          {/* RIGHT COLUMN - Status & Alarms */}
          {/* ============================================================ */}
          <div className="col-span-4 space-y-6">
            
            {/* Water Quality Panel */}
            <div className="bg-hmi-panel rounded-lg border border-hmi-border p-4">
              <h3 className="text-sm font-bold text-gray-200 mb-4 flex items-center gap-2">
                <Droplets className="w-4 h-4 text-blue-400" />
                Water Quality
              </h3>
              
              <div className="grid grid-cols-2 gap-4">
                <DigitalDisplay 
                  name="Raw Turbidity"
                  tag="AIT-101"
                  value={state.raw_turbidity}
                  unit="NTU"
                  highAlarm={25}
                />
                <DigitalDisplay 
                  name="Filtered Turb"
                  tag="AIT-104"
                  value={state.filtered_turbidity}
                  unit="NTU"
                  decimals={2}
                  highAlarm={0.5}
                />
                <DigitalDisplay 
                  name="Raw pH"
                  tag="AIT-102"
                  value={state.ph_raw}
                  unit="pH"
                  decimals={2}
                />
                <DigitalDisplay 
                  name="Temperature"
                  tag="TIT-101"
                  value={state.temperature}
                  unit="°C"
                />
              </div>
            </div>

            {/* Chemical Dosing Panel */}
            <div className="bg-hmi-panel rounded-lg border border-hmi-border p-4">
              <h3 className="text-sm font-bold text-gray-200 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-purple-400" />
                Chemical Dosing
              </h3>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Chlorine</span>
                  <div className="text-right">
                    <div className="text-sm font-mono text-green-400">
                      {state.chlorine_flow.toFixed(1)} GPH
                    </div>
                    <div className="text-xs text-gray-500">
                      SP: {state.chlorine_dose.toFixed(1)} mg/L
                    </div>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Alum</span>
                  <div className="text-right">
                    <div className="text-sm font-mono text-green-400">
                      {state.alum_flow.toFixed(1)} GPH
                    </div>
                    <div className="text-xs text-gray-500">
                      SP: {state.alum_dose.toFixed(1)} mg/L
                    </div>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Fluoride</span>
                  <div className="text-right">
                    <div className="text-sm font-mono text-green-400">
                      {state.fluoride_flow.toFixed(1)} GPH
                    </div>
                    <div className="text-xs text-gray-500">
                      SP: {state.fluoride_dose.toFixed(1)} mg/L
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Filter Status */}
            <div className="bg-hmi-panel rounded-lg border border-hmi-border p-4">
              <h3 className="text-sm font-bold text-gray-200 mb-4">Filter Status</h3>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Filter 1</span>
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      'px-2 py-0.5 rounded text-xs font-mono',
                      state.filter_1_status === 'ONLINE' 
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    )}>
                      {state.filter_1_status}
                    </span>
                    <span className="text-xs text-gray-500">
                      {state.filter_1_runtime.toFixed(1)}h
                    </span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Filter 2</span>
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      'px-2 py-0.5 rounded text-xs font-mono',
                      state.filter_2_status === 'ONLINE' 
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    )}>
                      {state.filter_2_status}
                    </span>
                    <span className="text-xs text-gray-500">
                      {state.filter_2_runtime.toFixed(1)}h
                    </span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-400">Filter ΔP</span>
                  <span className={cn(
                    'text-sm font-mono',
                    state.filter_dp > 8 ? 'text-yellow-400' : 'text-green-400'
                  )}>
                    {state.filter_dp.toFixed(1)} PSI
                  </span>
                </div>
              </div>
            </div>

            {/* Alarm Panel */}
            <AlarmPanel />

            {/* Network Info (for training) */}
            <div className="bg-hmi-panel rounded-lg border border-hmi-border p-4">
              <h3 className="text-sm font-bold text-gray-200 mb-3">
                🎯 Training Info
              </h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">PLC-INTAKE</span>
                  <span className="font-mono text-blue-400">10.0.1.10:502</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">PLC-TREATMENT</span>
                  <span className="font-mono text-blue-400">10.0.1.11:502</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">PLC-DISTRIBUTION</span>
                  <span className="font-mono text-blue-400">10.0.1.12:502</span>
                </div>
                <div className="mt-3 pt-3 border-t border-gray-700 text-gray-500">
                  Protocol: Modbus TCP (No Auth)
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-hmi-panel border-t border-hmi-border px-6 py-2 mt-6">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>VULNOT v0.1.0 - OT Security Training Platform</span>
          <span>Mjolnir Security - ⚠️ INTENTIONALLY VULNERABLE</span>
        </div>
      </footer>
    </div>
  );
}

'use client';

import { useState } from 'react';
import { 
  Server, 
  Monitor, 
  Cpu, 
  Network, 
  Shield,
  Wifi,
  Database,
  AlertTriangle,
  Eye
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NetworkDevice {
  id: string;
  name: string;
  type: 'plc' | 'hmi' | 'switch' | 'router' | 'server' | 'workstation' | 'historian';
  ip: string;
  port?: number;
  protocol?: string;
  level: number; // Purdue level
  status: 'online' | 'offline' | 'warning';
  x: number;
  y: number;
}

interface NetworkConnection {
  from: string;
  to: string;
  type: 'ethernet' | 'serial' | 'wireless';
  protocol?: string;
}

interface NetworkTopologyProps {
  scenario: 'water' | 'power' | 'factory';
  onDeviceClick?: (device: NetworkDevice) => void;
}

// Device configurations for each scenario
const SCENARIOS: Record<string, { devices: NetworkDevice[]; connections: NetworkConnection[] }> = {
  water: {
    devices: [
      // Level 4/5 - Enterprise
      { id: 'corp-net', name: 'Corporate Network', type: 'router', ip: '192.168.1.1', level: 5, status: 'online', x: 400, y: 30 },
      
      // Level 3.5 - DMZ
      { id: 'fw-dmz', name: 'DMZ Firewall', type: 'router', ip: '10.0.0.1', level: 3.5, status: 'online', x: 400, y: 100 },
      { id: 'historian', name: 'Historian Server', type: 'historian', ip: '10.0.0.10', level: 3.5, status: 'online', x: 550, y: 100 },
      
      // Level 3 - Site Operations
      { id: 'scada-srv', name: 'SCADA Server', type: 'server', ip: '10.0.1.5', level: 3, status: 'online', x: 250, y: 180 },
      { id: 'eng-ws', name: 'Engineering WS', type: 'workstation', ip: '10.0.1.6', level: 3, status: 'online', x: 550, y: 180 },
      
      // Level 2 - HMI
      { id: 'hmi-main', name: 'Main HMI', type: 'hmi', ip: '10.0.1.20', level: 2, status: 'online', x: 400, y: 260 },
      
      // Level 1 - Controllers
      { id: 'sw-ot', name: 'OT Switch', type: 'switch', ip: '10.0.1.2', level: 1, status: 'online', x: 400, y: 340 },
      { id: 'plc-intake', name: 'PLC-INTAKE', type: 'plc', ip: '10.0.1.10', port: 502, protocol: 'Modbus', level: 1, status: 'online', x: 200, y: 420 },
      { id: 'plc-treatment', name: 'PLC-TREATMENT', type: 'plc', ip: '10.0.1.11', port: 502, protocol: 'Modbus', level: 1, status: 'online', x: 400, y: 420 },
      { id: 'plc-dist', name: 'PLC-DISTRIBUTION', type: 'plc', ip: '10.0.1.12', port: 502, protocol: 'Modbus', level: 1, status: 'online', x: 600, y: 420 },
      
      // Attacker
      { id: 'attacker', name: 'Attacker WS', type: 'workstation', ip: '10.0.1.100', level: 1, status: 'warning', x: 700, y: 340 },
    ],
    connections: [
      { from: 'corp-net', to: 'fw-dmz', type: 'ethernet' },
      { from: 'fw-dmz', to: 'historian', type: 'ethernet' },
      { from: 'fw-dmz', to: 'scada-srv', type: 'ethernet' },
      { from: 'fw-dmz', to: 'eng-ws', type: 'ethernet' },
      { from: 'scada-srv', to: 'hmi-main', type: 'ethernet' },
      { from: 'eng-ws', to: 'hmi-main', type: 'ethernet' },
      { from: 'hmi-main', to: 'sw-ot', type: 'ethernet' },
      { from: 'sw-ot', to: 'plc-intake', type: 'ethernet', protocol: 'Modbus TCP' },
      { from: 'sw-ot', to: 'plc-treatment', type: 'ethernet', protocol: 'Modbus TCP' },
      { from: 'sw-ot', to: 'plc-dist', type: 'ethernet', protocol: 'Modbus TCP' },
      { from: 'sw-ot', to: 'attacker', type: 'ethernet' },
    ],
  },
  power: {
    devices: [
      { id: 'control-center', name: 'Control Center', type: 'server', ip: '10.0.2.5', level: 3, status: 'online', x: 400, y: 80 },
      { id: 'scada-master', name: 'DNP3 Master', type: 'server', ip: '10.0.2.6', level: 2, status: 'online', x: 400, y: 160 },
      { id: 'comm-router', name: 'Comm Router', type: 'router', ip: '10.0.2.2', level: 2, status: 'online', x: 400, y: 240 },
      { id: 'sub1-rtu', name: 'Substation 1 RTU', type: 'plc', ip: '10.0.2.10', port: 20000, protocol: 'DNP3', level: 1, status: 'online', x: 250, y: 340 },
      { id: 'sub2-rtu', name: 'Substation 2 RTU', type: 'plc', ip: '10.0.2.11', port: 20001, protocol: 'DNP3', level: 1, status: 'online', x: 550, y: 340 },
      { id: 'attacker', name: 'Attacker WS', type: 'workstation', ip: '10.0.2.100', level: 1, status: 'warning', x: 650, y: 240 },
    ],
    connections: [
      { from: 'control-center', to: 'scada-master', type: 'ethernet' },
      { from: 'scada-master', to: 'comm-router', type: 'ethernet' },
      { from: 'comm-router', to: 'sub1-rtu', type: 'ethernet', protocol: 'DNP3' },
      { from: 'comm-router', to: 'sub2-rtu', type: 'ethernet', protocol: 'DNP3' },
      { from: 'comm-router', to: 'attacker', type: 'ethernet' },
    ],
  },
  factory: {
    devices: [
      { id: 'mes-server', name: 'MES Server', type: 'server', ip: '10.0.3.5', level: 3, status: 'online', x: 400, y: 80 },
      { id: 'scada-srv', name: 'SCADA Server', type: 'server', ip: '10.0.3.6', level: 2, status: 'online', x: 250, y: 160 },
      { id: 'eng-ws', name: 'TIA Portal WS', type: 'workstation', ip: '10.0.3.7', level: 2, status: 'online', x: 550, y: 160 },
      { id: 'hmi-panel', name: 'HMI Panel', type: 'hmi', ip: '10.0.3.20', level: 2, status: 'online', x: 400, y: 240 },
      { id: 'profinet-sw', name: 'Profinet Switch', type: 'switch', ip: '10.0.3.2', level: 1, status: 'online', x: 400, y: 320 },
      { id: 'plc-line1', name: 'S7-1500 Line 1', type: 'plc', ip: '10.0.3.10', port: 102, protocol: 'S7comm', level: 1, status: 'online', x: 250, y: 400 },
      { id: 'plc-line2', name: 'S7-1500 Line 2', type: 'plc', ip: '10.0.3.11', port: 102, protocol: 'S7comm', level: 1, status: 'online', x: 550, y: 400 },
      { id: 'attacker', name: 'Attacker WS', type: 'workstation', ip: '10.0.3.100', level: 1, status: 'warning', x: 650, y: 320 },
    ],
    connections: [
      { from: 'mes-server', to: 'scada-srv', type: 'ethernet' },
      { from: 'mes-server', to: 'eng-ws', type: 'ethernet' },
      { from: 'scada-srv', to: 'hmi-panel', type: 'ethernet' },
      { from: 'eng-ws', to: 'hmi-panel', type: 'ethernet' },
      { from: 'hmi-panel', to: 'profinet-sw', type: 'ethernet' },
      { from: 'profinet-sw', to: 'plc-line1', type: 'ethernet', protocol: 'S7comm' },
      { from: 'profinet-sw', to: 'plc-line2', type: 'ethernet', protocol: 'S7comm' },
      { from: 'profinet-sw', to: 'attacker', type: 'ethernet' },
    ],
  },
};

// Device Icon Component
function DeviceIcon({ type }: { type: NetworkDevice['type'] }) {
  const iconClass = 'w-6 h-6';
  
  switch (type) {
    case 'plc':
      return <Cpu className={iconClass} />;
    case 'hmi':
      return <Monitor className={iconClass} />;
    case 'switch':
      return <Network className={iconClass} />;
    case 'router':
      return <Shield className={iconClass} />;
    case 'server':
      return <Server className={iconClass} />;
    case 'workstation':
      return <Monitor className={iconClass} />;
    case 'historian':
      return <Database className={iconClass} />;
    default:
      return <Cpu className={iconClass} />;
  }
}

// Network Device Node
function DeviceNode({ 
  device, 
  onClick,
  selected 
}: { 
  device: NetworkDevice; 
  onClick?: () => void;
  selected?: boolean;
}) {
  const isAttacker = device.id === 'attacker';
  
  return (
    <div
      className={cn(
        'absolute flex flex-col items-center cursor-pointer transition-all',
        'transform -translate-x-1/2 -translate-y-1/2',
        selected && 'scale-110'
      )}
      style={{ left: device.x, top: device.y }}
      onClick={onClick}
    >
      <div className={cn(
        'w-14 h-14 rounded-lg border-2 flex items-center justify-center',
        'transition-colors',
        device.status === 'online' && 'bg-green-500/20 border-green-500 text-green-400',
        device.status === 'offline' && 'bg-gray-500/20 border-gray-500 text-gray-400',
        device.status === 'warning' && 'bg-red-500/20 border-red-500 text-red-400',
        isAttacker && 'animate-pulse',
        selected && 'ring-2 ring-blue-400'
      )}>
        <DeviceIcon type={device.type} />
      </div>
      
      <div className="mt-1 text-xs text-center">
        <div className="font-medium text-gray-200">{device.name}</div>
        <div className="text-gray-400 font-mono">{device.ip}</div>
        {device.protocol && (
          <div className="text-blue-400 text-xs">{device.protocol}</div>
        )}
      </div>
      
      {isAttacker && (
        <AlertTriangle className="absolute -top-2 -right-2 w-4 h-4 text-red-500" />
      )}
    </div>
  );
}

export function NetworkTopology({ scenario, onDeviceClick }: NetworkTopologyProps) {
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const config = SCENARIOS[scenario];
  
  if (!config) return null;
  
  const handleDeviceClick = (device: NetworkDevice) => {
    setSelectedDevice(device.id);
    onDeviceClick?.(device);
  };
  
  // Calculate connection paths
  const getDevicePosition = (id: string) => {
    const device = config.devices.find(d => d.id === id);
    return device ? { x: device.x, y: device.y } : { x: 0, y: 0 };
  };

  return (
    <div className="bg-hmi-panel rounded-lg border border-hmi-border p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-gray-200 flex items-center gap-2">
          <Network className="w-4 h-4 text-blue-400" />
          Network Topology - {scenario.charAt(0).toUpperCase() + scenario.slice(1)} Scenario
        </h3>
        
        {/* Legend */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-green-500" />
            <span className="text-gray-400">Online</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded bg-red-500" />
            <span className="text-gray-400">Attacker</span>
          </div>
        </div>
      </div>
      
      {/* Purdue Level Labels */}
      <div className="relative h-[480px] overflow-hidden">
        {/* Level backgrounds */}
        <div className="absolute inset-0 flex flex-col">
          {[
            { level: '4-5', name: 'Enterprise', color: 'bg-purple-500/5' },
            { level: '3.5', name: 'DMZ', color: 'bg-orange-500/5' },
            { level: '3', name: 'Operations', color: 'bg-blue-500/5' },
            { level: '2', name: 'HMI/SCADA', color: 'bg-green-500/5' },
            { level: '1', name: 'Control', color: 'bg-yellow-500/5' },
            { level: '0', name: 'Process', color: 'bg-red-500/5' },
          ].map((l, i) => (
            <div key={l.level} className={cn('flex-1', l.color, 'border-b border-gray-700/30')}>
              <div className="text-xs text-gray-500 p-1">
                L{l.level} - {l.name}
              </div>
            </div>
          ))}
        </div>
        
        {/* Connections */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          {config.connections.map((conn, i) => {
            const from = getDevicePosition(conn.from);
            const to = getDevicePosition(conn.to);
            
            return (
              <g key={i}>
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke="#4B5563"
                  strokeWidth="2"
                  strokeDasharray={conn.type === 'wireless' ? '5,5' : undefined}
                />
                {conn.protocol && (
                  <text
                    x={(from.x + to.x) / 2}
                    y={(from.y + to.y) / 2 - 5}
                    fill="#9CA3AF"
                    fontSize="10"
                    textAnchor="middle"
                  >
                    {conn.protocol}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
        
        {/* Devices */}
        {config.devices.map((device) => (
          <DeviceNode
            key={device.id}
            device={device}
            onClick={() => handleDeviceClick(device)}
            selected={selectedDevice === device.id}
          />
        ))}
      </div>
      
      {/* Selected Device Info */}
      {selectedDevice && (
        <div className="mt-4 p-3 bg-gray-800 rounded border border-gray-700">
          {(() => {
            const device = config.devices.find(d => d.id === selectedDevice);
            if (!device) return null;
            
            return (
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-400">Name:</span>
                  <span className="ml-2 font-mono">{device.name}</span>
                </div>
                <div>
                  <span className="text-gray-400">IP:</span>
                  <span className="ml-2 font-mono text-blue-400">{device.ip}</span>
                </div>
                {device.port && (
                  <div>
                    <span className="text-gray-400">Port:</span>
                    <span className="ml-2 font-mono text-green-400">{device.port}</span>
                  </div>
                )}
                {device.protocol && (
                  <div>
                    <span className="text-gray-400">Protocol:</span>
                    <span className="ml-2 font-mono text-yellow-400">{device.protocol}</span>
                  </div>
                )}
                <div>
                  <span className="text-gray-400">Level:</span>
                  <span className="ml-2 font-mono">L{device.level}</span>
                </div>
                <div>
                  <span className="text-gray-400">Type:</span>
                  <span className="ml-2 font-mono">{device.type.toUpperCase()}</span>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}

export default NetworkTopology;

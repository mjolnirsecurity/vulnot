'use client';

import { useState } from 'react';
import Link from 'next/link';
import { 
  Droplets,
  Zap,
  Factory,
  Network,
  GraduationCap,
  Shield,
  AlertTriangle,
  ChevronRight,
  Play,
  BookOpen
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Scenario {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  protocol: string;
  network: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  href: string;
  color: string;
  targets: { name: string; ip: string; port: number }[];
}

const SCENARIOS: Scenario[] = [
  {
    id: 'water',
    name: 'Water Treatment Plant',
    icon: <Droplets className="w-8 h-8" />,
    description: 'Municipal water treatment facility with intake, treatment, and distribution systems controlled by Modbus TCP PLCs.',
    protocol: 'Modbus TCP',
    network: '10.0.1.0/24',
    difficulty: 'beginner',
    href: '/',
    color: 'from-blue-500/20 to-cyan-500/20 border-blue-500/50',
    targets: [
      { name: 'PLC-INTAKE', ip: '10.0.1.10', port: 502 },
      { name: 'PLC-TREATMENT', ip: '10.0.1.11', port: 502 },
      { name: 'PLC-DISTRIBUTION', ip: '10.0.1.12', port: 502 },
    ],
  },
  {
    id: 'power',
    name: 'Power Grid Substations',
    icon: <Zap className="w-8 h-8" />,
    description: 'Distribution substations with circuit breakers, transformers, and protective relays controlled by DNP3 RTUs.',
    protocol: 'DNP3',
    network: '10.0.2.0/24',
    difficulty: 'intermediate',
    href: '/power-grid',
    color: 'from-yellow-500/20 to-orange-500/20 border-yellow-500/50',
    targets: [
      { name: 'Substation 1', ip: '10.0.2.10', port: 20000 },
      { name: 'Substation 2', ip: '10.0.2.11', port: 20001 },
    ],
  },
  {
    id: 'factory',
    name: 'Manufacturing Line',
    icon: <Factory className="w-8 h-8" />,
    description: 'Automated assembly line with conveyors, pick & place robots, QC inspection, and packaging controlled by S7-1500 PLCs.',
    protocol: 'S7comm',
    network: '10.0.3.0/24',
    difficulty: 'advanced',
    href: '/factory',
    color: 'from-purple-500/20 to-pink-500/20 border-purple-500/50',
    targets: [
      { name: 'Line 1 PLC', ip: '10.0.3.10', port: 102 },
      { name: 'Line 2 PLC', ip: '10.0.3.11', port: 102 },
    ],
  },
];

function DifficultyBadge({ level }: { level: Scenario['difficulty'] }) {
  const config = {
    beginner: { text: 'Beginner', color: 'bg-green-500/20 text-green-400 border-green-500/50' },
    intermediate: { text: 'Intermediate', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50' },
    advanced: { text: 'Advanced', color: 'bg-red-500/20 text-red-400 border-red-500/50' },
  };
  
  return (
    <span className={cn('px-2 py-0.5 rounded border text-xs', config[level].color)}>
      {config[level].text}
    </span>
  );
}

function ScenarioCard({ scenario }: { scenario: Scenario }) {
  return (
    <div className={cn(
      'bg-gradient-to-br rounded-xl border p-6 transition-all hover:scale-[1.02] hover:shadow-xl',
      scenario.color
    )}>
      <div className="flex items-start justify-between mb-4">
        <div className={cn(
          'p-3 rounded-lg',
          scenario.id === 'water' && 'bg-blue-500/20 text-blue-400',
          scenario.id === 'power' && 'bg-yellow-500/20 text-yellow-400',
          scenario.id === 'factory' && 'bg-purple-500/20 text-purple-400',
        )}>
          {scenario.icon}
        </div>
        <DifficultyBadge level={scenario.difficulty} />
      </div>
      
      <h3 className="text-xl font-bold text-white mb-2">{scenario.name}</h3>
      <p className="text-sm text-gray-400 mb-4">{scenario.description}</p>
      
      <div className="space-y-2 text-sm mb-4">
        <div className="flex justify-between">
          <span className="text-gray-500">Protocol:</span>
          <span className="font-mono text-gray-300">{scenario.protocol}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Network:</span>
          <span className="font-mono text-gray-300">{scenario.network}</span>
        </div>
      </div>
      
      <div className="border-t border-gray-700 pt-4 mb-4">
        <div className="text-xs text-gray-500 mb-2">Targets:</div>
        <div className="space-y-1">
          {scenario.targets.map((target, i) => (
            <div key={i} className="flex justify-between text-xs">
              <span className="text-gray-400">{target.name}</span>
              <span className="font-mono text-green-400">{target.ip}:{target.port}</span>
            </div>
          ))}
        </div>
      </div>
      
      <Link 
        href={scenario.href}
        className="flex items-center justify-center gap-2 w-full py-2.5 bg-white/10 hover:bg-white/20 rounded-lg text-white font-medium transition-colors"
      >
        <Play className="w-4 h-4" />
        Launch HMI Dashboard
      </Link>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-hmi-bg">
      {/* Hero Header */}
      <header className="bg-gradient-to-b from-gray-900 to-hmi-bg border-b border-hmi-border">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex items-center gap-4 mb-4">
            <Shield className="w-12 h-12 text-red-500" />
            <div>
              <h1 className="text-4xl font-bold text-white">VULNOT</h1>
              <p className="text-gray-400">Vulnerable Operational Technology</p>
            </div>
          </div>
          
          <p className="text-xl text-gray-300 max-w-3xl mb-6">
            A comprehensive OT/ICS security training platform. Learn to attack and defend 
            industrial control systems in realistic simulated environments.
          </p>
          
          <div className="flex items-center gap-4">
            <Link 
              href="/training"
              className="flex items-center gap-2 px-6 py-3 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors"
            >
              <GraduationCap className="w-5 h-5" />
              Start Training
            </Link>
            <Link 
              href="/network"
              className="flex items-center gap-2 px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
            >
              <Network className="w-5 h-5" />
              Network View
            </Link>
            <a 
              href="https://github.com/mjolnir-security/vulnot"
              target="_blank"
              className="flex items-center gap-2 px-6 py-3 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg font-medium transition-colors"
            >
              <BookOpen className="w-5 h-5" />
              Documentation
            </a>
          </div>
        </div>
      </header>

      {/* Warning Banner */}
      <div className="bg-red-500/10 border-y border-red-500/30">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <span className="text-red-400 text-sm">
            <strong>WARNING:</strong> This platform is intentionally vulnerable. 
            Do NOT use these techniques against real industrial systems without authorization.
          </span>
        </div>
      </div>

      {/* Scenarios */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-2">Training Scenarios</h2>
          <p className="text-gray-400">
            Choose a scenario to launch the HMI dashboard and begin attacking
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {SCENARIOS.map((scenario) => (
            <ScenarioCard key={scenario.id} scenario={scenario} />
          ))}
        </div>

        {/* Quick Start */}
        <div className="bg-hmi-panel rounded-xl border border-hmi-border p-8">
          <h2 className="text-xl font-bold text-white mb-4">Quick Start</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="text-3xl font-bold text-blue-400 mb-2">1</div>
              <h3 className="font-medium text-white mb-1">Launch Platform</h3>
              <p className="text-sm text-gray-400">
                Start the Docker Compose stack to spin up all services
              </p>
              <code className="block mt-2 text-xs bg-gray-800 p-2 rounded text-green-400 font-mono">
                ./vulnot.sh start
              </code>
            </div>
            
            <div>
              <div className="text-3xl font-bold text-yellow-400 mb-2">2</div>
              <h3 className="font-medium text-white mb-1">Connect Attacker</h3>
              <p className="text-sm text-gray-400">
                Access the attacker workstation to start hacking
              </p>
              <code className="block mt-2 text-xs bg-gray-800 p-2 rounded text-green-400 font-mono">
                docker exec -it vulnot-attacker-water bash
              </code>
            </div>
            
            <div>
              <div className="text-3xl font-bold text-green-400 mb-2">3</div>
              <h3 className="font-medium text-white mb-1">Attack!</h3>
              <p className="text-sm text-gray-400">
                Use the tools to scan, read, and manipulate PLCs
              </p>
              <code className="block mt-2 text-xs bg-gray-800 p-2 rounded text-green-400 font-mono">
                vulnot-scan && vulnot-read -t 10.0.1.10
              </code>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
          {[
            { label: 'Scenarios', value: '3', color: 'text-blue-400' },
            { label: 'Protocols', value: '3', color: 'text-yellow-400' },
            { label: 'Training Labs', value: '10', color: 'text-green-400' },
            { label: 'Attack Tools', value: '12+', color: 'text-red-400' },
          ].map((stat, i) => (
            <div key={i} className="bg-hmi-panel rounded-lg border border-hmi-border p-4 text-center">
              <div className={cn('text-3xl font-bold', stat.color)}>{stat.value}</div>
              <div className="text-sm text-gray-400">{stat.label}</div>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-hmi-panel border-t border-hmi-border mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              VULNOT v0.2.0 - Phase 2 (Modbus, DNP3, S7comm)
            </div>
            <div className="text-sm text-gray-500">
              Built with ⚡ by Mjolnir Security
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

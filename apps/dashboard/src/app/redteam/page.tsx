'use client';

import { useState, useEffect } from 'react';
import {
  Swords,
  Shield,
  Target,
  Clock,
  Flag,
  Trophy,
  Users,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Play,
  Pause,
  RotateCcw,
  Eye,
  EyeOff,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Team {
  name: string;
  type: 'red' | 'blue';
  score: number;
  members: string[];
  objectives: Objective[];
}

interface Objective {
  id: string;
  description: string;
  points: number;
  completed: boolean;
  timestamp?: number;
}

interface Event {
  timestamp: number;
  team: 'red' | 'blue' | 'system';
  event: string;
  points?: number;
}

const RED_OBJECTIVES: Objective[] = [
  { id: 'R1', description: 'Gain initial access to OT network', points: 10, completed: false },
  { id: 'R2', description: 'Enumerate all PLCs on network', points: 15, completed: false },
  { id: 'R3', description: 'Read process values from historian', points: 20, completed: false },
  { id: 'R4', description: 'Modify a process setpoint', points: 30, completed: false },
  { id: 'R5', description: 'Stop a PLC without detection', points: 40, completed: false },
  { id: 'R6', description: 'Exfiltrate historian database', points: 35, completed: false },
  { id: 'R7', description: 'Establish persistence', points: 25, completed: false },
  { id: 'R8', description: 'Delete attack evidence from historian', points: 30, completed: false },
  { id: 'R9', description: 'Cause coordinated multi-protocol attack', points: 50, completed: false },
];

const BLUE_OBJECTIVES: Objective[] = [
  { id: 'B1', description: 'Detect network reconnaissance', points: 15, completed: false },
  { id: 'B2', description: 'Identify attack source IP', points: 20, completed: false },
  { id: 'B3', description: 'Alert on unauthorized OT access', points: 25, completed: false },
  { id: 'B4', description: 'Block attacker without process disruption', points: 30, completed: false },
  { id: 'B5', description: 'Collect forensic evidence', points: 20, completed: false },
  { id: 'B6', description: 'Restore modified setpoint', points: 25, completed: false },
  { id: 'B7', description: 'Identify all IOCs', points: 30, completed: false },
  { id: 'B8', description: 'Map attack to MITRE ATT&CK', points: 20, completed: false },
  { id: 'B9', description: 'Generate incident report', points: 15, completed: false },
];

const SCENARIOS = [
  {
    id: 'scenario-1',
    name: 'Water Treatment Compromise',
    description: 'Red team attempts to manipulate water treatment process. Blue team must detect and respond.',
    duration: 60,
    protocols: ['Modbus', 'Historian'],
    difficulty: 'Intermediate',
  },
  {
    id: 'scenario-2',
    name: 'Power Grid Attack',
    description: 'Simulate Ukraine-style attack on substation. Red team targets breakers.',
    duration: 90,
    protocols: ['DNP3', 'Historian'],
    difficulty: 'Advanced',
  },
  {
    id: 'scenario-3',
    name: 'Manufacturing Sabotage',
    description: 'Red team attempts to halt production. Blue team protects factory line.',
    duration: 75,
    protocols: ['S7comm', 'OPC UA', 'Historian'],
    difficulty: 'Advanced',
  },
  {
    id: 'scenario-4',
    name: 'IIoT Supply Chain',
    description: 'Compromise via vulnerable IIoT devices and pivot to OT.',
    duration: 90,
    protocols: ['MQTT', 'Modbus', 'Historian'],
    difficulty: 'Expert',
  },
];

function TeamCard({ team, onObjectiveComplete }: { team: Team; onObjectiveComplete: (id: string) => void }) {
  const isRed = team.type === 'red';
  const completedObjectives = team.objectives.filter(o => o.completed).length;
  
  return (
    <div className={cn(
      'bg-gray-800 rounded-lg border-2 p-4',
      isRed ? 'border-red-500/50' : 'border-blue-500/50'
    )}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {isRed ? (
            <Swords className="w-6 h-6 text-red-500" />
          ) : (
            <Shield className="w-6 h-6 text-blue-500" />
          )}
          <h2 className={cn('text-lg font-bold', isRed ? 'text-red-400' : 'text-blue-400')}>
            {team.name}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <Trophy className={cn('w-5 h-5', isRed ? 'text-red-400' : 'text-blue-400')} />
          <span className="text-2xl font-bold text-white">{team.score}</span>
        </div>
      </div>
      
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-gray-400">Progress</span>
          <span className="text-gray-400">{completedObjectives}/{team.objectives.length}</span>
        </div>
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className={cn('h-full transition-all', isRed ? 'bg-red-500' : 'bg-blue-500')}
            style={{ width: `${(completedObjectives / team.objectives.length) * 100}%` }}
          />
        </div>
      </div>
      
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {team.objectives.map((obj) => (
          <div 
            key={obj.id}
            onClick={() => !obj.completed && onObjectiveComplete(obj.id)}
            className={cn(
              'flex items-center gap-2 p-2 rounded cursor-pointer transition-colors',
              obj.completed 
                ? 'bg-green-500/10 border border-green-500/30' 
                : 'bg-gray-700 hover:bg-gray-600'
            )}
          >
            {obj.completed ? (
              <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
            ) : (
              <div className="w-4 h-4 rounded-full border-2 border-gray-500 flex-shrink-0" />
            )}
            <span className={cn('text-sm flex-1', obj.completed ? 'text-green-400 line-through' : 'text-gray-300')}>
              {obj.description}
            </span>
            <span className={cn('text-xs font-bold', isRed ? 'text-red-400' : 'text-blue-400')}>
              +{obj.points}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function RedTeamPage() {
  const [exerciseRunning, setExerciseRunning] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(60 * 60); // 60 minutes
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0]);
  const [events, setEvents] = useState<Event[]>([]);
  
  const [redTeam, setRedTeam] = useState<Team>({
    name: 'Red Team',
    type: 'red',
    score: 0,
    members: ['Attacker 1', 'Attacker 2'],
    objectives: RED_OBJECTIVES.map(o => ({...o})),
  });
  
  const [blueTeam, setBlueTeam] = useState<Team>({
    name: 'Blue Team',
    type: 'blue',
    score: 0,
    members: ['Defender 1', 'Defender 2'],
    objectives: BLUE_OBJECTIVES.map(o => ({...o})),
  });

  useEffect(() => {
    if (exerciseRunning && timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining(t => t - 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [exerciseRunning, timeRemaining]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleObjectiveComplete = (team: 'red' | 'blue', objectiveId: string) => {
    const setTeam = team === 'red' ? setRedTeam : setBlueTeam;
    const currentTeam = team === 'red' ? redTeam : blueTeam;
    
    const objective = currentTeam.objectives.find(o => o.id === objectiveId);
    if (!objective || objective.completed) return;
    
    setTeam(prev => ({
      ...prev,
      score: prev.score + objective.points,
      objectives: prev.objectives.map(o => 
        o.id === objectiveId ? { ...o, completed: true, timestamp: Date.now() } : o
      ),
    }));
    
    setEvents(prev => [...prev, {
      timestamp: Date.now(),
      team,
      event: `${team === 'red' ? '🔴' : '🔵'} ${objective.description}`,
      points: objective.points,
    }]);
  };

  const resetExercise = () => {
    setExerciseRunning(false);
    setTimeRemaining(selectedScenario.duration * 60);
    setRedTeam(prev => ({
      ...prev,
      score: 0,
      objectives: RED_OBJECTIVES.map(o => ({...o, completed: false})),
    }));
    setBlueTeam(prev => ({
      ...prev,
      score: 0,
      objectives: BLUE_OBJECTIVES.map(o => ({...o, completed: false})),
    }));
    setEvents([]);
  };

  return (
    <div className="min-h-screen bg-hmi-bg">
      {/* Header */}
      <header className="bg-hmi-panel border-b border-hmi-border px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex">
              <Swords className="w-6 h-6 text-red-500" />
              <Shield className="w-6 h-6 text-blue-500 -ml-2" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Red vs Blue Exercise</h1>
              <p className="text-xs text-gray-400">{selectedScenario.name}</p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            {/* Timer */}
            <div className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg',
              timeRemaining < 300 ? 'bg-red-500/20' : 'bg-gray-800'
            )}>
              <Clock className={cn('w-5 h-5', timeRemaining < 300 ? 'text-red-400' : 'text-gray-400')} />
              <span className={cn('text-2xl font-mono font-bold', timeRemaining < 300 ? 'text-red-400' : 'text-white')}>
                {formatTime(timeRemaining)}
              </span>
            </div>
            
            {/* Controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setExerciseRunning(!exerciseRunning)}
                className={cn(
                  'p-2 rounded',
                  exerciseRunning 
                    ? 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30'
                    : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                )}
              >
                {exerciseRunning ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              </button>
              <button
                onClick={resetExercise}
                className="p-2 bg-gray-800 rounded text-gray-400 hover:bg-gray-700"
              >
                <RotateCcw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="p-6">
        {/* Score Display */}
        <div className="flex items-center justify-center gap-8 mb-6">
          <div className="text-center">
            <div className="text-5xl font-bold text-red-500">{redTeam.score}</div>
            <div className="text-sm text-gray-400">Red Team</div>
          </div>
          <div className="text-4xl font-bold text-gray-600">vs</div>
          <div className="text-center">
            <div className="text-5xl font-bold text-blue-500">{blueTeam.score}</div>
            <div className="text-sm text-gray-400">Blue Team</div>
          </div>
        </div>

        {/* Teams */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <TeamCard 
            team={redTeam} 
            onObjectiveComplete={(id) => handleObjectiveComplete('red', id)} 
          />
          <TeamCard 
            team={blueTeam} 
            onObjectiveComplete={(id) => handleObjectiveComplete('blue', id)} 
          />
        </div>

        {/* Activity Feed */}
        <div className="grid grid-cols-3 gap-6">
          {/* Event Log */}
          <div className="col-span-2 bg-gray-800 rounded-lg border border-gray-700 p-4">
            <h3 className="font-bold text-gray-200 mb-3 flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" />
              Activity Feed
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {events.length === 0 ? (
                <div className="text-sm text-gray-500 text-center py-4">
                  No activity yet. Start the exercise!
                </div>
              ) : (
                events.slice().reverse().map((event, i) => (
                  <div key={i} className="flex items-center justify-between text-sm bg-gray-900 rounded p-2">
                    <span className="text-gray-300">{event.event}</span>
                    <div className="flex items-center gap-2">
                      {event.points && (
                        <span className={cn(
                          'font-bold',
                          event.team === 'red' ? 'text-red-400' : 'text-blue-400'
                        )}>
                          +{event.points}
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Scenario Info */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <h3 className="font-bold text-gray-200 mb-3">Scenario Details</h3>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-gray-400">Duration:</span>
                <span className="ml-2 text-white">{selectedScenario.duration} min</span>
              </div>
              <div>
                <span className="text-gray-400">Difficulty:</span>
                <span className="ml-2 text-yellow-400">{selectedScenario.difficulty}</span>
              </div>
              <div>
                <span className="text-gray-400">Protocols:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedScenario.protocols.map(p => (
                    <span key={p} className="px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
              <p className="text-gray-400 pt-2 border-t border-gray-700">
                {selectedScenario.description}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-hmi-panel border-t border-hmi-border px-6 py-2 mt-6">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>VULNOT v0.5.0 - Red Team Exercise</span>
          <span>⚠️ Training Environment Only</span>
        </div>
      </footer>
    </div>
  );
}

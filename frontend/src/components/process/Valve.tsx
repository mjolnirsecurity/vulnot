'use client';

interface ValveProps {
  name: string;
  position: number;
  onPositionChange?: (position: number) => void;
}

export function Valve({ name, position, onPositionChange }: ValveProps) {
  const status = position === 0 ? 'Closed' : position === 100 ? 'Open' : 'Throttled';
  const color = position === 0 ? 'bg-red-500' : position === 100 ? 'bg-green-500' : 'bg-yellow-500';
  
  return (
    <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-300 capitalize">
          {name.replace(/_/g, ' ')}
        </h4>
        <span className={`px-2 py-0.5 rounded text-xs text-white ${color}`}>
          {status}
        </span>
      </div>
      
      <div className="relative h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className="absolute h-full bg-blue-500 transition-all duration-300"
          style={{ width: `${position}%` }}
        />
      </div>
      
      <div className="text-center mt-1 text-sm text-white font-medium">
        {position.toFixed(0)}%
      </div>
    </div>
  );
}

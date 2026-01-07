import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatValue(value: number, decimals: number = 1): string {
  return value.toFixed(decimals);
}

export function getAlarmColor(priority: string): string {
  const colors: Record<string, string> = {
    critical: 'bg-red-600 animate-pulse',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500',
  };
  return colors[priority] || 'bg-gray-500';
}

export function getLevelColor(level: number): string {
  if (level < 20) return '#EF4444';
  if (level < 40) return '#F59E0B';
  if (level > 90) return '#F59E0B';
  return '#3B82F6';
}

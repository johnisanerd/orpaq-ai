import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatScore(score: number): string {
  if (score >= 80) return 'HOT';
  if (score >= 50) return 'MEDIUM';
  return 'LOW';
}

export function formatScoreColor(priority: string): string {
  switch (priority) {
    case 'hot':
      return 'text-red-400 bg-red-400/10 border-red-400/20';
    case 'medium':
      return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
    default:
      return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
  }
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'hot':
      return 'from-red-500 to-orange-500';
    case 'medium':
      return 'from-yellow-500 to-amber-500';
    default:
      return 'from-gray-500 to-slate-500';
  }
}
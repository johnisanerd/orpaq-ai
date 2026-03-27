'use client';

import { TrendingUp, Users, Zap, Target } from 'lucide-react';

interface StatsProps {
  stats: {
    total: number;
    hot: number;
    medium: number;
    low: number;
    total_businesses?: number;
    total_analyses?: number;
  };
}

export function Stats({ stats }: StatsProps) {
  const cards = [
    {
      label: 'Total Leads',
      value: stats.total,
      icon: Target,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      label: 'Hot Leads',
      value: stats.hot,
      icon: Zap,
      color: 'from-red-500 to-orange-500',
    },
    {
      label: 'Medium Leads',
      value: stats.medium,
      icon: TrendingUp,
      color: 'from-yellow-500 to-amber-500',
    },
    {
      label: 'Low Priority',
      value: stats.low,
      icon: Users,
      color: 'from-gray-500 to-slate-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <div
          key={card.label}
          className="glass-card p-5 animate-fade-in"
          style={{ animationDelay: `${index * 50}ms` }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-1">{card.label}</p>
              <p className="text-3xl font-bold text-white">{card.value}</p>
            </div>
            <div className={`p-3 rounded-xl bg-gradient-to-br ${card.color}`}>
              <card.icon className="w-6 h-6 text-white" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
'use client';

import { useState } from 'react';
import { Play, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';

interface PipelineRunProps {
  onRun: (location: string, category: string, limit: number) => Promise<void>;
  isRunning: boolean;
}

const categories = [
  { value: 'restaurants', label: 'Restaurants' },
  { value: 'clinics', label: 'Clinics' },
  { value: 'agencies', label: 'Agencies' },
  { value: 'salons', label: 'Salons' },
  { value: 'gyms', label: 'Gyms' },
];

export function PipelineRun({ onRun, isRunning }: PipelineRunProps) {
  const [location, setLocation] = useState('');
  const [category, setCategory] = useState('restaurants');
  const [limit, setLimit] = useState('50');
  const [result, setResult] = useState<any>(null);

  const handleRun = async () => {
    if (!location) return;
    
    setResult(null);
    await onRun(location, category, parseInt(limit));
  };

  return (
    <div className="glass-card p-6 mb-6">
      <h2 className="text-lg font-semibold text-white mb-4">Run Discovery Pipeline</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Input
          placeholder="Location (e.g., New York, London)"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        
        <Select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          options={categories}
        />
        
        <Input
          placeholder="Limit (max 200)"
          type="number"
          value={limit}
          onChange={(e) => setLimit(e.target.value)}
        />
        
        <Button onClick={handleRun} disabled={isRunning || !location} className="w-full">
          {isRunning ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 mr-2" />
              Start Pipeline
            </>
          )}
        </Button>
      </div>

      {result && (
        <div className={`mt-4 p-4 rounded-lg border ${
          result.status === 'completed' 
            ? 'bg-green-500/10 border-green-500/20' 
            : result.status === 'failed'
            ? 'bg-red-500/10 border-red-500/20'
            : 'bg-blue-500/10 border-blue-500/20'
        }`}>
          <div className="flex items-center gap-2">
            {result.status === 'completed' ? (
              <CheckCircle className="w-5 h-5 text-green-400" />
            ) : result.status === 'failed' ? (
              <AlertCircle className="w-5 h-5 text-red-400" />
            ) : (
              <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
            )}
            <span className="text-white font-medium">Pipeline {result.status}</span>
          </div>
          <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Businesses Found:</span>
              <span className="ml-2 text-white">{result.businesses_found}</span>
            </div>
            <div>
              <span className="text-gray-400">Analyzed:</span>
              <span className="ml-2 text-white">{result.websites_analyzed}</span>
            </div>
            <div>
              <span className="text-gray-400">Leads Generated:</span>
              <span className="ml-2 text-white">{result.leads_generated}</span>
            </div>
            <div>
              <span className="text-gray-400">Errors:</span>
              <span className="ml-2 text-white">{result.errors?.length || 0}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
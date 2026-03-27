'use client';

import { useState } from 'react';
import { Filter, Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { LeadFilters } from '@/lib/api';

interface FiltersProps {
  onFilter: (filters: LeadFilters) => void;
}

const categories = [
  { value: '', label: 'All Categories' },
  { value: 'restaurant', label: 'Restaurants' },
  { value: 'clinic', label: 'Clinics' },
  { value: 'agency', label: 'Agencies' },
  { value: 'salon', label: 'Salons' },
  { value: 'gym', label: 'Gyms' },
];

const priorities = [
  { value: '', label: 'All Priorities' },
  { value: 'hot', label: 'Hot' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

export function Filters({ onFilter }: FiltersProps) {
  const [search, setSearch] = useState('');
  const [priority, setPriority] = useState('');
  const [category, setCategory] = useState('');
  const [location, setLocation] = useState('');
  const [minScore, setMinScore] = useState('');
  const [maxScore, setMaxScore] = useState('');
  const [showWebsite, setShowWebsite] = useState('');

  const handleApply = () => {
    onFilter({
      search: search || undefined,
      priority: priority || undefined,
      category: category || undefined,
      location: location || undefined,
      min_score: minScore ? parseInt(minScore) : undefined,
      max_score: maxScore ? parseInt(maxScore) : undefined,
      has_website: showWebsite ? showWebsite === 'yes' : undefined,
    });
  };

  const handleClear = () => {
    setSearch('');
    setPriority('');
    setCategory('');
    setLocation('');
    setMinScore('');
    setMaxScore('');
    setShowWebsite('');
    onFilter({});
  };

  const hasFilters = search || priority || category || location || minScore || maxScore || showWebsite;

  return (
    <div className="glass-card p-4 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-4 h-4 text-gray-400" />
        <span className="text-sm font-medium text-gray-300">Filters</span>
        {hasFilters && (
          <button onClick={handleClear} className="ml-auto text-xs text-gray-400 hover:text-white flex items-center gap-1">
            <X className="w-3 h-3" /> Clear
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search businesses..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          />
        </div>

        <Select
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          options={priorities}
        />

        <Select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          options={categories}
        />

        <Input
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
        <Input
          placeholder="Min Score"
          type="number"
          value={minScore}
          onChange={(e) => setMinScore(e.target.value)}
        />
        <Input
          placeholder="Max Score"
          type="number"
          value={maxScore}
          onChange={(e) => setMaxScore(e.target.value)}
        />
        <Select
          value={showWebsite}
          onChange={(e) => setShowWebsite(e.target.value)}
          options={[
            { value: '', label: 'Website Status' },
            { value: 'yes', label: 'Has Website' },
            { value: 'no', label: 'No Website' },
          ]}
        />
        <Button onClick={handleApply} className="w-full">
          Apply Filters
        </Button>
      </div>
    </div>
  );
}
'use client';

import { useState } from 'react';
import { ExternalLink, Trash2, ChevronDown, ChevronUp, Mail } from 'lucide-react';
import { Lead } from '@/lib/api';
import { formatScoreColor, cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface LeadsTableProps {
  leads: Lead[];
  onDelete?: (id: string) => void;
  onSelect?: (lead: Lead) => void;
}

export function LeadsTable({ leads, onDelete, onSelect }: LeadsTableProps) {
  const [sortField, setSortField] = useState<string>('lead_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const sortedLeads = [...leads].sort((a, b) => {
    let aVal: any = a[sortField as keyof Lead];
    let bVal: any = b[sortField as keyof Lead];
    
    if (sortField === 'business') {
      aVal = a.business?.name || '';
      bVal = b.business?.name || '';
    }
    
    if (typeof aVal === 'string') {
      return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  const SortIcon = ({ field }: { field: string }) => {
    if (sortField !== field) return null;
    return sortDir === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />;
  };

  if (leads.length === 0) {
    return (
      <Card className="p-12 text-center">
        <p className="text-gray-400 text-lg">No leads found</p>
        <p className="text-gray-500 text-sm mt-2">Run a pipeline to discover businesses</p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800">
              <th 
                className="text-left p-4 text-sm font-medium text-gray-400 cursor-pointer hover:text-white"
                onClick={() => handleSort('business')}
              >
                <div className="flex items-center gap-1">
                  Business <SortIcon field="business" />
                </div>
              </th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">Category</th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">Location</th>
              <th 
                className="text-left p-4 text-sm font-medium text-gray-400 cursor-pointer hover:text-white"
                onClick={() => handleSort('lead_score')}
              >
                <div className="flex items-center gap-1">
                  Score <SortIcon field="lead_score" />
                </div>
              </th>
              <th className="text-left p-4 text-sm font-medium text-gray-400">Priority</th>
              <th className="text-right p-4 text-sm font-medium text-gray-400">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedLeads.map((lead, index) => (
              <tr
                key={lead.id}
                className={cn(
                  'border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors',
                  'animate-fade-in'
                )}
                style={{ animationDelay: `${index * 30}ms` }}
              >
                <td className="p-4">
                  <div>
                    <p className="font-medium text-white">{lead.business?.name}</p>
                    {lead.business?.website && (
                      <a
                        href={lead.business.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1 mt-1"
                      >
                        <ExternalLink className="w-3 h-3" />
                        {lead.business.website.replace(/^https?:\/\//, '').slice(0, 30)}
                      </a>
                    )}
                    {!lead.business?.website && (
                      <span className="text-sm text-red-400">No website</span>
                    )}
                  </div>
                </td>
                <td className="p-4 text-gray-300">{lead.business?.category}</td>
                <td className="p-4 text-gray-300">{lead.business?.location}</td>
                <td className="p-4">
                  <span className="text-xl font-bold text-white">{lead.lead_score}</span>
                </td>
                <td className="p-4">
                  <span className={cn(
                    'px-3 py-1 rounded-full text-xs font-medium border',
                    formatScoreColor(lead.priority)
                  )}>
                    {lead.priority.toUpperCase()}
                  </span>
                </td>
                <td className="p-4">
                  <div className="flex items-center justify-end gap-2">
                    {lead.business?.email && (
                      <a href={`mailto:${lead.business.email}`}>
                        <Button variant="ghost" size="sm">
                          <Mail className="w-4 h-4" />
                        </Button>
                      </a>
                    )}
                    {onSelect && (
                      <Button variant="ghost" size="sm" onClick={() => onSelect(lead)}>
                        View
                      </Button>
                    )}
                    {onDelete && (
                      <Button variant="ghost" size="sm" onClick={() => onDelete(lead.id)}>
                        <Trash2 className="w-4 h-4 text-red-400" />
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
'use client';

import { useState, useEffect, useCallback } from 'react';
import { 
  Download, RefreshCw, Play, Loader2, Search, Filter, 
  ChevronDown, ChevronUp, Trash2, Mail, ExternalLink,
  Target, Zap, TrendingUp, Users, Sparkles, ArrowRight,
  LayoutGrid, List, MapPin, Building2, Phone, Globe
} from 'lucide-react';
import { leadsApi, Lead, LeadFilters } from '@/lib/api';
import { ThemeToggle } from '@/components/ui/theme-toggle';

export default function Dashboard() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState({ total: 0, hot: 0, medium: 0, low: 0 });
  const [loading, setLoading] = useState(true);
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [filters, setFilters] = useState<LeadFilters>({});
  const [mounted, setMounted] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  
  // Filter states
  const [search, setSearch] = useState('');
  const [priority, setPriority] = useState('');
  const [category, setCategory] = useState('');
  const [location, setLocation] = useState('');
  const [minScore, setMinScore] = useState('');
  const [maxScore, setMaxScore] = useState('');
  const [showWebsite, setShowWebsite] = useState('');

  // Pipeline states
  const [pipelineLocation, setPipelineLocation] = useState('');
  const [pipelineCategory, setPipelineCategory] = useState('restaurants');
  const [pipelineLimit, setPipelineLimit] = useState('10');
  const [pipelineResult, setPipelineResult] = useState<any>(null);

  // Sort
  const [sortField, setSortField] = useState<string>('lead_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    setMounted(true);
  }, []);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const data = await leadsApi.getLeads(filters);
      setLeads(data.leads);
    } catch (error) {
      console.error('Failed to fetch leads:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const fetchStats = async () => {
    try {
      const data = await leadsApi.getStats();
      setStats(data.leads);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const loadData = useCallback(async () => {
    await Promise.all([fetchLeads(), fetchStats()]);
  }, [fetchLeads]);

  useEffect(() => {
    if (mounted) {
      loadData();
    }
  }, [loadData, mounted]);

  const handleApplyFilters = () => {
    setFilters({
      search: search || undefined,
      priority: priority || undefined,
      category: category || undefined,
      location: location || undefined,
      min_score: minScore ? parseInt(minScore) : undefined,
      max_score: maxScore ? parseInt(maxScore) : undefined,
      has_website: showWebsite ? showWebsite === 'yes' : undefined,
    });
  };

  const handleClearFilters = () => {
    setSearch('');
    setPriority('');
    setCategory('');
    setLocation('');
    setMinScore('');
    setMaxScore('');
    setShowWebsite('');
    setFilters({});
  };

  const handleRunPipeline = async () => {
    if (!pipelineLocation) return;
    setRunningPipeline(true);
    setPipelineResult(null);
    try {
      await leadsApi.runPipeline(pipelineLocation, pipelineCategory, parseInt(pipelineLimit));
      await loadData();
    } catch (error) {
      console.error('Pipeline failed:', error);
    } finally {
      setRunningPipeline(false);
    }
  };

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      const data = await leadsApi.exportLeads(format, filters);
      if (format === 'json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'orpaq-leads.json';
        a.click();
      } else {
        const blob = new Blob([data.data], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'orpaq-leads.csv';
        a.click();
      }
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this lead?')) return;
    try {
      await leadsApi.deleteLead(id);
      await loadData();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

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

  if (!mounted) return null;

  const statCards = [
    { label: 'Total Leads', value: stats.total, icon: Target, color: 'from-teal-500 to-cyan-500', bg: 'rgba(20, 184, 166, 0.1)' },
    { label: 'Hot Leads', value: stats.hot, icon: Zap, color: 'from-orange-500 to-red-500', bg: 'rgba(249, 115, 22, 0.1)' },
    { label: 'Medium Leads', value: stats.medium, icon: TrendingUp, color: 'from-yellow-500 to-amber-500', bg: 'rgba(234, 179, 8, 0.1)' },
    { label: 'Low Priority', value: stats.low, icon: Users, color: 'from-slate-500 to-gray-500', bg: 'rgba(100, 116, 139, 0.1)' },
  ];

  return (
    <div className="min-h-screen bg-mesh">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-[var(--border-color)]">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center glow-teal">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-transparent">
                  Orpaq AI
                </h1>
                <p className="text-xs text-[var(--text-muted)]">Lead Generation Platform</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <ThemeToggle />
              <button
                onClick={() => loadData()}
                disabled={loading}
                className="p-2.5 rounded-xl glass hover:border-[var(--accent-primary)] transition-all"
              >
                <RefreshCw className={`w-4 h-4 text-[var(--text-secondary)] ${loading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => handleExport('csv')}
                className="px-4 py-2 rounded-xl glass text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent-primary)] hover:border-[var(--accent-primary)] transition-all flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {statCards.map((card, index) => (
            <div
              key={card.label}
              className="glass-card p-5 animate-slide-up"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-[var(--text-muted)] mb-1">{card.label}</p>
                  <p className="text-3xl font-bold">{card.value}</p>
                </div>
                <div 
                  className="w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{ background: card.bg }}
                >
                  <card.icon className={`w-6 h-6 bg-gradient-to-br ${card.color} bg-clip-text text-transparent`} />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Pipeline Runner */}
        <div className="glass-card p-6 mb-8 animate-slide-up" style={{ animationDelay: '200ms' }}>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center">
              <Play className="w-4 h-4 text-white" />
            </div>
            <h2 className="text-lg font-semibold">Discovery Pipeline</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
              <input
                type="text"
                placeholder="Location (e.g., New York)"
                value={pipelineLocation}
                onChange={(e) => setPipelineLocation(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:border-[var(--accent-primary)] transition-all"
              />
            </div>
            <select
              value={pipelineCategory}
              onChange={(e) => setPipelineCategory(e.target.value)}
              className="px-4 py-3 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:border-[var(--accent-primary)] transition-all"
            >
              <option value="restaurants">Restaurants</option>
              <option value="clinics">Clinics</option>
              <option value="agencies">Agencies</option>
              <option value="salons">Salons</option>
              <option value="gyms">Gyms</option>
            </select>
            <input
              type="number"
              placeholder="Limit"
              value={pipelineLimit}
              onChange={(e) => setPipelineLimit(e.target.value)}
              className="px-4 py-3 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:border-[var(--accent-primary)] transition-all"
            />
            <button
              onClick={handleRunPipeline}
              disabled={runningPipeline || !pipelineLocation}
              className="btn-primary px-6 py-3 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {runningPipeline ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Start Pipeline
                </>
              )}
            </button>
          </div>

          {pipelineResult && (
            <div className="mt-4 p-4 rounded-xl bg-[var(--accent-subtle)] border border-[var(--accent-primary)]/20">
              <div className="flex items-center gap-2 text-[var(--accent-primary)]">
                <Sparkles className="w-4 h-4" />
                <span className="font-medium">Pipeline completed!</span>
              </div>
              <div className="grid grid-cols-4 gap-4 mt-3 text-sm">
                <div><span className="text-[var(--text-muted)]">Found:</span> <span className="font-semibold">{pipelineResult.businesses_found}</span></div>
                <div><span className="text-[var(--text-muted)]">Analyzed:</span> <span className="font-semibold">{pipelineResult.websites_analyzed}</span></div>
                <div><span className="text-[var(--text-muted)]">Leads:</span> <span className="font-semibold">{pipelineResult.leads_generated}</span></div>
                <div><span className="text-[var(--text-muted)]">Errors:</span> <span className="font-semibold">{pipelineResult.errors?.length || 0}</span></div>
              </div>
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="glass-card p-4 mb-8 animate-slide-up" style={{ animationDelay: '250ms' }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-[var(--text-muted)]" />
              <span className="font-medium">Filters</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex rounded-lg overflow-hidden border border-[var(--border-color)]">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 ${viewMode === 'grid' ? 'bg-[var(--accent-primary)] text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-muted)]'}`}
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 ${viewMode === 'list' ? 'bg-[var(--accent-primary)] text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-muted)]'}`}
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
              {(search || priority || category || location) && (
                <button
                  onClick={handleClearFilters}
                  className="text-xs text-[var(--text-muted)] hover:text-[var(--accent-primary)] transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)]" />
              <input
                type="text"
                placeholder="Search businesses..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] text-sm"
              />
            </div>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="px-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] text-sm"
            >
              <option value="">Priority</option>
              <option value="hot">Hot</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="px-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] text-sm"
            >
              <option value="">Category</option>
              <option value="restaurant">Restaurants</option>
              <option value="clinic">Clinics</option>
              <option value="agency">Agencies</option>
              <option value="salon">Salons</option>
              <option value="gym">Gyms</option>
            </select>
            <input
              type="text"
              placeholder="Location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="px-4 py-2.5 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] text-sm"
            />
          </div>

          <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--border-color)]">
            <div className="flex items-center gap-4">
              <input
                type="number"
                placeholder="Min score"
                value={minScore}
                onChange={(e) => setMinScore(e.target.value)}
                className="w-28 px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] text-sm"
              />
              <span className="text-[var(--text-muted)]">-</span>
              <input
                type="number"
                placeholder="Max score"
                value={maxScore}
                onChange={(e) => setMaxScore(e.target.value)}
                className="w-28 px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] text-sm"
              />
            </div>
            <button
              onClick={handleApplyFilters}
              className="px-6 py-2.5 btn-primary rounded-xl text-sm font-medium flex items-center gap-2"
            >
              Apply Filters
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Leads */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-10 h-10 spinner" />
          </div>
        ) : leads.length === 0 ? (
          <div className="glass-card p-12 text-center animate-fade-in">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[var(--accent-subtle)] flex items-center justify-center">
              <Target className="w-8 h-8 text-[var(--accent-primary)]" />
            </div>
            <h3 className="text-xl font-semibold mb-2">No leads yet</h3>
            <p className="text-[var(--text-muted)] mb-6">Run a pipeline to discover businesses</p>
            <button
              onClick={() => handleRunPipeline()}
              disabled={runningPipeline || !pipelineLocation}
              className="btn-primary px-6 py-3 rounded-xl inline-flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Start Discovery
            </button>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedLeads.map((lead, index) => (
              <div
                key={lead.id}
                className="glass-card p-5 card-shine animate-slide-up hover:scale-[1.02] transition-all cursor-pointer"
                style={{ animationDelay: `${index * 30}ms` }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg mb-1">{lead.business?.name}</h3>
                    <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
                      <Building2 className="w-3.5 h-3.5" />
                      <span>{lead.business?.category}</span>
                    </div>
                  </div>
                  <span className={`badge badge-${lead.priority}`}>{lead.priority}</span>
                </div>

                <div className="space-y-2 text-sm mb-4">
                  <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>{lead.business?.location}</span>
                  </div>
                  {lead.business?.phone && (
                    <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                      <Phone className="w-3.5 h-3.5" />
                      <span>{lead.business.phone}</span>
                    </div>
                  )}
                  {lead.business?.website ? (
                    <div className="flex items-center gap-2 text-[var(--accent-primary)]">
                      <Globe className="w-3.5 h-3.5" />
                      <a href={lead.business.website} target="_blank" rel="noopener noreferrer" className="hover:underline truncate">
                        {lead.business.website.replace(/^https?:\/\//, '')}
                      </a>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-red-400">
                      <Globe className="w-3.5 h-3.5" />
                      <span>No website</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-[var(--border-color)]">
                  <div className="flex items-center gap-2">
                    <div className={`priority-dot ${lead.priority === 'hot' ? 'priority-dot-hot' : lead.priority === 'medium' ? 'priority-dot-medium' : 'priority-dot-low'}`} />
                    <span className="text-2xl font-bold">{lead.lead_score}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {lead.business?.email && (
                      <a href={`mailto:${lead.business.email}`} className="p-2 rounded-lg hover:bg-[var(--accent-subtle)] transition-colors">
                        <Mail className="w-4 h-4 text-[var(--text-muted)]" />
                      </a>
                    )}
                    {lead.business?.website && (
                      <a href={lead.business.website} target="_blank" rel="noopener noreferrer" className="p-2 rounded-lg hover:bg-[var(--accent-subtle)] transition-colors">
                        <ExternalLink className="w-4 h-4 text-[var(--text-muted)]" />
                      </a>
                    )}
                    <button onClick={() => handleDelete(lead.id)} className="p-2 rounded-lg hover:bg-red-500/10 transition-colors">
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="glass-card overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--border-color)]">
                  <th className="text-left p-4 text-sm font-medium text-[var(--text-muted)]">Business</th>
                  <th className="text-left p-4 text-sm font-medium text-[var(--text-muted)]">Category</th>
                  <th className="text-left p-4 text-sm font-medium text-[var(--text-muted)]">Location</th>
                  <th 
                    className="text-left p-4 text-sm font-medium text-[var(--text-muted)] cursor-pointer hover:text-[var(--accent-primary)]"
                    onClick={() => handleSort('lead_score')}
                  >
                    <div className="flex items-center gap-1">
                      Score {sortField === 'lead_score' && (sortDir === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
                    </div>
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-[var(--text-muted)]">Priority</th>
                  <th className="text-right p-4 text-sm font-medium text-[var(--text-muted)]">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedLeads.map((lead) => (
                  <tr key={lead.id} className="table-row border-b border-[var(--border-color)]">
                    <td className="p-4">
                      <div>
                        <p className="font-medium">{lead.business?.name}</p>
                        {lead.business?.website ? (
                          <a href={lead.business.website} target="_blank" rel="noopener noreferrer" className="text-xs text-[var(--accent-primary)] hover:underline">
                            {lead.business.website.replace(/^https?:\/\//, '').slice(0, 30)}
                          </a>
                        ) : (
                          <span className="text-xs text-red-400">No website</span>
                        )}
                      </div>
                    </td>
                    <td className="p-4 text-[var(--text-secondary)]">{lead.business?.category}</td>
                    <td className="p-4 text-[var(--text-secondary)]">{lead.business?.location}</td>
                    <td className="p-4"><span className="text-xl font-bold">{lead.lead_score}</span></td>
                    <td className="p-4"><span className={`badge badge-${lead.priority}`}>{lead.priority}</span></td>
                    <td className="p-4">
                      <div className="flex items-center justify-end gap-1">
                        {lead.business?.email && (
                          <a href={`mailto:${lead.business.email}`} className="p-2 rounded-lg hover:bg-[var(--accent-subtle)]">
                            <Mail className="w-4 h-4 text-[var(--text-muted)]" />
                          </a>
                        )}
                        <button onClick={() => handleDelete(lead.id)} className="p-2 rounded-lg hover:bg-red-500/10">
                          <Trash2 className="w-4 h-4 text-red-400" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
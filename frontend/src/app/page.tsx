'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Download, RefreshCw, Play, Loader2, Search, Filter, 
  ChevronDown, ChevronUp, Trash2, Mail, ExternalLink,
  Target, Zap, TrendingUp, Users, Sparkles, ArrowRight,
  LayoutGrid, List, MapPin, Building2, Phone, Globe, LogOut, SearchIcon,
  ChevronRight, Copy, Check
} from 'lucide-react';
import { leadsApi, Lead, LeadFilters } from '@/lib/api';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { useAuth } from '@/lib/auth';

export default function Dashboard() {
  const { user, signOut } = useAuth();
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState({ total: 0, hot: 0, medium: 0, low: 0 });
  const [loading, setLoading] = useState(true);
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [enriching, setEnriching] = useState<string | null>(null);
  const [sendingWa, setSendingWa] = useState<string | null>(null);
  const [filters, setFilters] = useState<LeadFilters>({});
  const [mounted, setMounted] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    if (user === null) {
      router.push('/login');
    }
  }, [user, router]);
  
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
  
  // Lead suggestions from API
  const [pipelineSuggestions, setPipelineSuggestions] = useState<any[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);

  // Fetch suggestions from API
  const fetchSuggestions = useCallback(async (loc?: string) => {
    setSuggestionsLoading(true);
    try {
      const params = loc ? `?location=${encodeURIComponent(loc)}&limit=12` : '?limit=12';
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/suggestions${params}`);
      if (res.ok) {
        const data = await res.json();
        setPipelineSuggestions(data);
      }
    } catch {
      // API offline — will stay empty
    } finally {
      setSuggestionsLoading(false);
    }
  }, []);

  // Load suggestions on mount
  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  // Filter suggestions as user types location
  const handleLocationChange = (val: string) => {
    setPipelineLocation(val);
    fetchSuggestions(val || undefined);
  };

  // Sort
  const [sortField, setSortField] = useState<string>('lead_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  
  // Expanded cards
  const [expandedCard, setExpandedCard] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

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

  const [pipelineStatus, setPipelineStatus] = useState('');
  const [pipelineElapsed, setPipelineElapsed] = useState(0);

  const handleRunPipeline = async () => {
    if (!pipelineLocation) return;
    setRunningPipeline(true);
    setPipelineResult(null);
    setPipelineStatus('Starting research...');
    setPipelineElapsed(0);
    const startTime = Date.now();
    const elapsedInt = setInterval(() => {
      setPipelineElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    try {
      const result = await leadsApi.runPipeline(pipelineLocation, pipelineCategory, parseInt(pipelineLimit));
      const runId = result.run_id;
      if (!runId) {
        setPipelineStatus('Pipeline started, waiting for results...');
        // No run_id returned, just wait then refresh
        await new Promise(resolve => setTimeout(resolve, 5000));
      } else {
        // Poll for completion
        setPipelineStatus('Researching...');
        for (let i = 0; i < 60; i++) {
          await new Promise(resolve => setTimeout(resolve, 3000));
          try {
            const runsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/pipeline-runs?limit=5`);
            const runs = await runsRes.json();
            const thisRun = runs.find((r: any) => r.id === runId);
            if (thisRun && (thisRun.status === 'completed' || thisRun.status === 'failed')) {
              setPipelineStatus(thisRun.status === 'completed' ? 'Research complete!' : `Failed: ${thisRun.errors || 'unknown error'}`);
              setPipelineResult(thisRun);
              break;
            }
          } catch {}
        }
      }
      await loadData();
    } catch (error) {
      console.error('Pipeline failed:', error);
      setPipelineStatus('Research failed');
    } finally {
      clearInterval(elapsedInt);
      setTimeout(() => setRunningPipeline(false), 2000);
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

  const handleCopyOutreach = async (message: string, leadId: string) => {
    try {
      await navigator.clipboard.writeText(message);
      setCopiedId(leadId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (error) {
      console.error('Copy failed:', error);
    }
  };

  const handleEnrich = async (id: string) => {
    setEnriching(id);
    try {
      await leadsApi.enrichLead(id);
      await loadData();
    } catch (error) {
      console.error('Enrich failed:', error);
      alert('Failed to enrich lead');
    } finally {
      setEnriching(null);
    }
  };

  const handleWhatsapp = async (id: string) => {
    setSendingWa(id);
    try {
      await leadsApi.sendWhatsapp(id);
      alert('Message sent to WhatsApp bridge!');
    } catch (error) {
      console.error('WhatsApp failed:', error);
      alert('Failed to send via WhatsApp');
    } finally {
      setSendingWa(null);
    }
  };

  const sortedLeads = [...leads].sort((a, b) => {
    let aVal: any = a[sortField as keyof Lead];
    let bVal: any = b[sortField as keyof Lead];
    if (sortField === 'business') {
      aVal = a.businesses?.name || a.business?.name || '';
      bVal = b.businesses?.name || b.business?.name || '';
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

  const googleMapsUrl = (name: string, location: string) => {
    return `https://www.google.com/maps/search/${encodeURIComponent(`${name} ${location}`)}`;
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[var(--bg-primary)] border-b border-[var(--border-color)]">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-9 h-9 rounded-lg bg-[var(--accent-primary)] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-[var(--text-primary)]">
                  Orpaq AI
                </h1>
                <p className="text-xs text-[var(--text-muted)]">Lead Generation Platform</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <span className="text-sm text-[var(--text-muted)]">{user?.email}</span>
              <button
                onClick={() => signOut()}
                className="p-2 rounded-lg hover:bg-[var(--bg-secondary)] border border-transparent hover:border-[var(--border-color)] transition-all"
              >
                <LogOut className="w-4 h-4 text-[var(--text-secondary)]" />
              </button>
              <ThemeToggle />
              <button
                onClick={() => loadData()}
                disabled={loading}
                className="p-2 rounded-lg hover:bg-[var(--bg-secondary)] border border-transparent hover:border-[var(--border-color)] transition-all"
              >
                <RefreshCw className={`w-4 h-4 text-[var(--text-secondary)] ${loading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => handleExport('csv')}
                className="px-4 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] text-sm font-medium hover:border-[var(--accent-primary)] transition-all flex items-center gap-2"
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
              className="surface-card p-5"
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
        <section className="surface-card p-6 md:p-8 mb-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-[var(--accent-primary)] flex items-center justify-center">
                <Target className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold tracking-tight">Discovery Pipeline</h2>
                <p className="text-sm text-[var(--text-muted)] mt-1">Deploy autonomous agent to scan and score leads</p>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-[1fr_200px_120px_180px] gap-4 mb-6">
            <div className="relative">
              <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)] pointer-events-none" />
              <input
                type="text"
                placeholder="Location (e.g., Kochi)"
                value={pipelineLocation}
                onChange={(e) => handleLocationChange(e.target.value)}
                className="w-full pl-12 pr-4 py-3.5 premium-input text-sm font-medium"
              />
            </div>
            <div className="relative">
              <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)] pointer-events-none" />
              <select
                value={pipelineCategory}
                onChange={(e) => setPipelineCategory(e.target.value)}
                className="w-full pl-12 pr-4 py-3.5 premium-input text-sm font-medium appearance-none cursor-pointer"
              >
                <option value="restaurants">Restaurants</option>
                <option value="clinics">Clinics</option>
                <option value="agencies">Agencies</option>
                <option value="salons">Salons</option>
                <option value="gyms">Gyms</option>
                <option value="dentists">Dentists</option>
                <option value="real-estate">Real Estate</option>
                <option value="interior-designers">Interior Designers</option>
                <option value="architects">Architects</option>
                <option value="wedding-planners">Wedding Planners</option>
                <option value="furniture">Furniture</option>
              </select>
              <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)] pointer-events-none" />
            </div>
            <div className="relative">
              <Users className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)] pointer-events-none" />
              <input
                type="number"
                placeholder="Max"
                value={pipelineLimit}
                onChange={(e) => setPipelineLimit(e.target.value)}
                className="w-full pl-12 pr-4 py-3.5 premium-input text-sm font-medium"
              />
            </div>
            <button
              onClick={handleRunPipeline}
              disabled={runningPipeline || !pipelineLocation}
              className="btn-primary w-full py-3.5 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm shadow-lg border border-white/10"
            >
              {runningPipeline ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>
                    {pipelineStatus || 'Running...'}
                    {pipelineElapsed > 0 && ` (${pipelineElapsed}s)`}
                  </span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  Deploy Agent
                </>
              )}
            </button>
          </div>

          {/* Suggestion chips */}
          <div className="mt-6 pt-6 border-t border-[var(--border-color)]">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-[var(--accent-primary)] fill-[var(--accent-primary)]/20" />
              <span className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider">Quick Suggestions</span>
            </div>
            <div className="flex flex-wrap gap-2.5">
              {pipelineSuggestions.map((s, i) => (
                <button
                  key={`${s.location}-${s.category}-${i}`}
                  onClick={() => {
                    setPipelineLocation(s.location);
                    setPipelineCategory(s.category);
                    fetchSuggestions(s.location);
                  }}
                  className={`group px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border flex items-center gap-1.5 ${
                    s.priority === 'high'
                      ? 'border-red-500/20 bg-red-500/5 text-red-500 hover:bg-red-500/10'
                      : s.priority === 'medium'
                      ? 'border-amber-500/20 bg-amber-500/5 text-amber-500 hover:bg-amber-500/10'
                      : 'border-[var(--border-color)] bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-primary)]'
                  }`}
                  title={s.desc}
                >
                  <span className="tracking-wide">{s.label}</span>
                  <span className="w-1 h-1 rounded-full bg-current opacity-40"></span>
                  <span className="opacity-80">{s.location}</span>
                </button>
              ))}
            </div>
          </div>

          {pipelineResult && (
            <div className="mt-6 p-5 rounded-xl bg-[var(--accent-subtle)] border border-[var(--accent-primary)]/30 shadow-inner flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-3 text-[var(--accent-primary)]">
                <div className="w-10 h-10 rounded-full bg-[var(--accent-primary)]/20 flex items-center justify-center">
                  <Check className="w-5 h-5" />
                </div>
                <div>
                  <span className="block font-bold text-sm">Mission Accomplished</span>
                  <span className="text-xs opacity-80 font-medium">Agent research sequence complete</span>
                </div>
              </div>
              <div className="flex gap-6 text-sm">
                <div className="flex flex-col"><span className="text-[var(--text-muted)] text-xs uppercase tracking-wider font-semibold">Discovered</span> <span className="font-bold text-lg text-[var(--text-primary)]">{pipelineResult.businesses_found}</span></div>
                <div className="flex flex-col"><span className="text-[var(--text-muted)] text-xs uppercase tracking-wider font-semibold">Analyzed</span> <span className="font-bold text-lg text-[var(--text-primary)]">{pipelineResult.websites_analyzed}</span></div>
                <div className="flex flex-col"><span className="text-[var(--text-muted)] text-xs uppercase tracking-wider font-semibold">Leads</span> <span className="font-bold text-lg text-[var(--accent-primary)]">{pipelineResult.leads_generated}</span></div>
              </div>
            </div>
          )}
        </section>

        {/* Filters */}
        <div className="surface-card p-5 mb-6">
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
              <option value="dentists">Dentists</option>
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
          <div className="surface-card p-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--bg-secondary)] border border-[var(--border-color)] flex items-center justify-center">
              <Target className="w-8 h-8 text-[var(--text-muted)]" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No leads yet</h3>
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
                className="surface-card p-5 cursor-pointer hover:border-[var(--accent-primary)] transition-colors"
                onClick={() => setExpandedCard(expandedCard === lead.id ? null : lead.id)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg mb-1">{lead.businesses?.name || lead.business?.name}</h3>
                    <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
                      <Building2 className="w-3.5 h-3.5" />
                      <span>{lead.businesses?.category || lead.business?.category}</span>
                    </div>
                  </div>
                  <span className={`badge badge-${lead.priority}`}>{lead.priority}</span>
                </div>

                <div className="space-y-2 text-sm mb-4">
                  <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>{lead.businesses?.location || lead.business?.location}</span>
                  </div>
                  {(lead.businesses?.phone || lead.business?.phone) && (
                    <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                      <Phone className="w-3.5 h-3.5" />
                      <span>{lead.businesses?.phone || lead.business?.phone}</span>
                    </div>
                  )}
                  {(lead.businesses?.website || lead.business?.website) ? (
                    <div className="flex items-center gap-2 text-[var(--accent-primary)]">
                      <Globe className="w-3.5 h-3.5" />
                      <a href={lead.businesses?.website || lead.business?.website} target="_blank" rel="noopener noreferrer" className="hover:underline truncate" onClick={(e) => e.stopPropagation()}>
                        {(lead.businesses?.website || lead.business?.website)?.replace(/^https?:\/\//, '')}
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
                    <a
                      href={googleMapsUrl(lead.businesses?.name || lead.business?.name || '', lead.businesses?.location || lead.business?.location || '')}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-lg hover:bg-[var(--accent-subtle)] transition-colors"
                      title="Open in Google Maps"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <MapPin className="w-4 h-4 text-[var(--text-muted)]" />
                    </a>
                    <a
                      href={`https://www.google.com/search?q=${encodeURIComponent(`${lead.businesses?.name || lead.business?.name} ${lead.businesses?.category || lead.business?.category} ${lead.businesses?.location || lead.business?.location}`)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-lg hover:bg-[var(--accent-subtle)] transition-colors"
                      title="Search on Google"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <SearchIcon className="w-4 h-4 text-[var(--text-muted)]" />
                    </a>
                    {(lead.businesses?.email || lead.business?.email) && (
                      <a href={`mailto:${lead.businesses?.email || lead.business?.email}`} className="p-2 rounded-lg hover:bg-[var(--accent-subtle)] transition-colors" onClick={(e) => e.stopPropagation()}>
                        <Mail className="w-4 h-4 text-[var(--text-muted)]" />
                      </a>
                    )}
                    {(lead.businesses?.website || lead.business?.website) && (
                      <a href={lead.businesses?.website || lead.business?.website} target="_blank" rel="noopener noreferrer" className="p-2 rounded-lg hover:bg-[var(--accent-subtle)] transition-colors" onClick={(e) => e.stopPropagation()}>
                        <ExternalLink className="w-4 h-4 text-[var(--text-muted)]" />
                      </a>
                    )}
                    <button onClick={(e) => { e.stopPropagation(); handleDelete(lead.id); }} className="p-2 rounded-lg hover:bg-red-500/10 transition-colors">
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                </div>

                {/* Expanded content */}
                {expandedCard === lead.id && (
                  <div className="mt-4 pt-4 border-t border-[var(--border-color)]">
                    <div className="flex justify-end gap-2 mb-4">
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleEnrich(lead.id); }}
                        disabled={enriching === lead.id}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] hover:border-[var(--accent-primary)] transition-all flex items-center gap-1.5"
                      >
                        {enriching === lead.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                        Enrich Lead
                      </button>
                      <button 
                        onClick={(e) => { e.stopPropagation(); handleWhatsapp(lead.id); }}
                        disabled={sendingWa === lead.id || !lead.outreach_message || !(lead.businesses?.phone || lead.business?.phone)}
                        className="px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20 hover:scale-[1.02] transition-all flex items-center gap-1.5 disabled:opacity-50 disabled:hover:scale-100"
                      >
                        {sendingWa === lead.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Phone className="w-3.5 h-3.5" />}
                        Send WhatsApp
                      </button>
                    </div>
                    {lead.outreach_message && (
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">Outreach Message</span>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleCopyOutreach(lead.outreach_message!, lead.id); }}
                            className="flex items-center gap-1 text-xs text-[var(--accent-primary)] hover:text-[var(--accent-primary)]/80"
                          >
                            {copiedId === lead.id ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                            {copiedId === lead.id ? 'Copied!' : 'Copy'}
                          </button>
                        </div>
                        <div className="p-3 rounded-lg bg-[var(--bg-secondary)] text-sm text-[var(--text-secondary)] whitespace-pre-wrap">
                          {lead.outreach_message}
                        </div>
                      </div>
                    )}
                    {lead.redesign_suggestions && (
                      <div>
                        <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">Suggestions</span>
                        <p className="mt-1 text-sm text-[var(--text-secondary)]">{lead.redesign_suggestions}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="surface-card overflow-hidden">
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
                        <p className="font-medium">{lead.businesses?.name || lead.business?.name}</p>
                        {(lead.businesses?.website || lead.business?.website) ? (
                          <a href={lead.businesses?.website || lead.business?.website} target="_blank" rel="noopener noreferrer" className="text-xs text-[var(--accent-primary)] hover:underline">
                            {(lead.businesses?.website || lead.business?.website)?.replace(/^https?:\/\//, '').slice(0, 30)}
                          </a>
                        ) : (
                          <span className="text-xs text-red-400">No website</span>
                        )}
                      </div>
                    </td>
                    <td className="p-4 text-[var(--text-secondary)]">{lead.businesses?.category || lead.business?.category}</td>
                    <td className="p-4 text-[var(--text-secondary)]">{lead.businesses?.location || lead.business?.location}</td>
                    <td className="p-4"><span className="text-xl font-bold">{lead.lead_score}</span></td>
                    <td className="p-4"><span className={`badge badge-${lead.priority}`}>{lead.priority}</span></td>
                    <td className="p-4">
                      <div className="flex items-center justify-end gap-1">
                        <a
                          href={googleMapsUrl(lead.businesses?.name || lead.business?.name || '', lead.businesses?.location || lead.business?.location || '')}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 rounded-lg hover:bg-[var(--accent-subtle)]"
                          title="Open in Google Maps"
                        >
                          <MapPin className="w-4 h-4 text-[var(--text-muted)]" />
                        </a>
                        <a
                          href={`https://www.google.com/search?q=${encodeURIComponent(`${lead.businesses?.name || lead.business?.name} ${lead.businesses?.category || lead.business?.category} ${lead.businesses?.location || lead.business?.location}`)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 rounded-lg hover:bg-[var(--accent-subtle)]"
                          title="Search on Google"
                        >
                          <SearchIcon className="w-4 h-4 text-[var(--text-muted)]" />
                        </a>
                        {(lead.businesses?.email || lead.business?.email) && (
                          <a href={`mailto:${lead.businesses?.email || lead.business?.email}`} className="p-2 rounded-lg hover:bg-[var(--accent-subtle)]">
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
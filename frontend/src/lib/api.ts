import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Business {
  id: string;
  name: string;
  website?: string;
  phone?: string;
  email?: string;
  category: string;
  location: string;
  address?: string;
  rating?: number;
  reviews_count?: number;
}

export interface Analysis {
  id: string;
  business_id: string;
  screenshot_url?: string;
  pagespeed_score?: number;
  pagespeed_issues?: string[];
  mobile_friendly?: boolean;
  ai_ui_score?: number;
  ai_outdated?: boolean;
  ai_issues?: string[];
  analysis_status: string;
}

export interface Lead {
  id: string;
  business_id: string;
  lead_score: number;
  priority: 'hot' | 'medium' | 'low';
  outreach_message?: string;
  redesign_suggestions?: string;
  business?: Business;
  analysis?: Analysis;
}

export interface LeadFilters {
  priority?: string;
  min_score?: number;
  max_score?: number;
  has_website?: boolean;
  location?: string;
  category?: string;
  search?: string;
}

export const leadsApi = {
  getLeads: async (filters?: LeadFilters) => {
    const params = new URLSearchParams();
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.min_score) params.append('min_score', filters.min_score.toString());
    if (filters?.max_score) params.append('max_score', filters.max_score.toString());
    if (filters?.location) params.append('location', filters.location);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.search) params.append('search', filters.search);
    
    const response = await api.get(`/leads?${params.toString()}`);
    return response.data;
  },

  getLead: async (id: string) => {
    const response = await api.get(`/leads/${id}`);
    return response.data;
  },

  deleteLead: async (id: string) => {
    const response = await api.delete(`/leads/${id}`);
    return response.data;
  },

  runPipeline: async (location: string, category: string, limit?: number) => {
    const response = await api.post('/run-pipeline', { location, category, limit });
    return response.data;
  },

  fetchBusinesses: async (location: string, category: string, limit?: number) => {
    const response = await api.post('/fetch-businesses', { location, category, limit });
    return response.data;
  },

  analyzeWebsite: async (businessId: string) => {
    const response = await api.post('/analyze-website', { business_id: businessId });
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/stats');
    return response.data;
  },

  exportLeads: async (format: 'csv' | 'json', filters?: LeadFilters) => {
    const response = await api.post('/export', { format, filters });
    return response.data;
  },
};
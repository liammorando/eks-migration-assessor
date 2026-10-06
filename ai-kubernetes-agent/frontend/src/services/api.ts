import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Use the rewrite path for browser compatibility
export const api = axios.create({
  baseURL: '/api/backend',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Cluster {
  name: string;
  current: boolean;
}

export interface ClustersResponse {
  status: string;
  clusters: Cluster[];
  current_context: string | null;
}

export async function healthCheck() {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
}

export async function listClusters(): Promise<ClustersResponse> {
  const response = await api.get('/clusters');
  return response.data;
}

export async function useCluster(contextName: string): Promise<{ status: string; current_context: string }> {
  const response = await api.post(`/clusters/${contextName}/use`);
  return response.data;
}

export interface InvestigationRequest {
  namespace?: string;
  context?: string;
}

export async function investigateCluster(request: InvestigationRequest = {}) {
  const response = await api.post('/investigate', request);
  return response.data;
}

export interface InvestigationRecord {
  id: string;
  timestamp: string;
  namespace: string;
  root_cause: string;
  confidence: number;
  status: 'completed' | 'failed' | 'no_issues';
}

export interface HistoryResponse {
  status: string;
  history: InvestigationRecord[];
}

export async function getInvestigationHistory(limit: number = 50): Promise<InvestigationRecord[]> {
  const response = await api.get<HistoryResponse>('/investigations/history', { params: { limit } });
  return response.data.history || [];
}

export async function saveInvestigation(investigation: any): Promise<InvestigationRecord> {
  const response = await api.post('/investigations', investigation);
  return response.data;
}
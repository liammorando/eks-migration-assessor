export interface HealthResponse {
  status: string;
  service: string;
}

export interface PodInfo {
  name: string;
  namespace: string;
  status: string;
  ready: string;
  restarts: number;
  age: string;
}

export interface NodeInfo {
  name: string;
  status: string;
  roles: string;
  age: string;
  version: string;
}

export interface EventInfo {
  name: string;
  namespace: string;
  type: string;
  reason: string;
  message: string;
  age: string;
}

export interface InvestigationRequest {
  namespace?: string;
  include_logs?: boolean;
}

export interface Issue {
  severity: string;
  component: string;
  description: string;
  suggestion: string;
}

export interface DiagnosisResponse {
  issues: Issue[];
  root_cause: string;
  suggested_fixes: string[];
  timestamp: string;
}
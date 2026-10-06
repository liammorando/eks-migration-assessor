'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { InvestigateButton } from '@/components/InvestigateButton';
import { SystemStatus } from '@/components/SystemStatus';
import { InvestigationProgress } from '@/components/InvestigationProgress';
import { DiagnosisResult } from '@/components/DiagnosisResult';
import { InvestigationHistory } from '@/components/InvestigationHistory';
import { 
  investigateCluster, 
  getInvestigationHistory, 
  InvestigationRecord, 
  listClusters, 
  useCluster,
  Cluster 
} from '@/services/api';

export default function DashboardPage() {
  const { isLoading: authLoading } = useAuth();
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [diagnosis, setDiagnosis] = useState<DiagnosisResultProps['diagnosis']>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<InvestigationRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [namespace, setNamespace] = useState('default');
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [currentContext, setCurrentContext] = useState<string | null>(null);
  const [clustersLoading, setClustersLoading] = useState(true);
  const [switchingCluster, setSwitchingCluster] = useState(false);

  const loadClusters = async () => {
    try {
      const data = await listClusters();
      setClusters(data.clusters || []);
      setCurrentContext(data.current_context);
    } catch (err) {
      console.error('Failed to load clusters:', err);
    } finally {
      setClustersLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await getInvestigationHistory();
      setHistory(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleClusterChange = async (contextName: string) => {
    if (contextName === currentContext) return;
    setSwitchingCluster(true);
    try {
      await useCluster(contextName);
      setCurrentContext(contextName);
      setClusters(prev => prev.map(c => ({ ...c, current: c.name === contextName })));
      // Reload history after switching cluster
      await loadHistory();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to switch cluster');
    } finally {
      setSwitchingCluster(false);
    }
  };

  const handleInvestigate = async () => {
    setIsInvestigating(true);
    setError(null);
    setDiagnosis(null);

    try {
      const response = await investigateCluster({ namespace, context: currentContext || undefined });
      if (response.status === 'success' && response.investigation?.diagnosis) {
        setDiagnosis(response.investigation.diagnosis);
        await loadHistory();
      } else if (response.status === 'success') {
        // No diagnosis in response (shouldn't happen, but handle gracefully)
        setDiagnosis({
          root_cause: "Investigation completed",
          explanation: "No diagnosis returned",
          fix: "Check investigation details",
          kubectl_commands: [],
          prevention: "Continue monitoring",
          confidence: 0,
        });
        await loadHistory();
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Investigation failed';
      setError(formatErrorMessage(errorMessage));
    } finally {
      setIsInvestigating(false);
    }
  };

  useEffect(() => {
    loadClusters();
    loadHistory();
  }, []);

  const formatErrorMessage = (message: string): string => {
    if (message.includes('connection refused') || message.includes('Unable to connect')) {
      return `Unable to connect to Kubernetes cluster.\n\nPlease verify:\n- kubeconfig path is correct\n- cluster is accessible\n- kubectl permissions are configured`;
    }
    if (message.includes('context') || message.includes('context')) {
      return `Cluster context error.\n\nPlease verify:\n- context name exists in kubeconfig\n- cluster is reachable`;
    }
    if (message.includes('timeout') || message.includes('Timeout')) {
      return `Request timed out.\n\nPlease verify:\n- cluster is responsive\n- network connectivity`;
    }
    return message;
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AI Kubernetes Agent</h1>
        <p className="mt-2 text-gray-600">Troubleshoot Kubernetes with AI</p>
      </div>

      {/* Cluster Selector */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Kubernetes Cluster</h2>
          {clustersLoading && (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {clusters.map((cluster) => (
            <button
              key={cluster.name}
              onClick={() => handleClusterChange(cluster.context_name || cluster.name)}
              disabled={switchingCluster || cluster.current}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                cluster.current
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              } ${switchingCluster ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {cluster.name} {cluster.current && <span className="ml-1 text-xs">(current)</span>}
            </button>
          ))}
          {clusters.length === 0 && !clustersLoading && (
            <span className="text-sm text-gray-500">No clusters found in kubeconfig</span>
          )}
        </div>
        {switchingCluster && (
          <p className="mt-2 text-sm text-blue-600">Switching cluster...</p>
        )}
      </div>

      <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
        <div className="md:col-span-2 lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Run Investigation</h2>
              <div className="flex items-center gap-2">
                <label htmlFor="namespace" className="text-sm text-gray-500">Namespace:</label>
                <select
                  id="namespace"
                  value={namespace}
                  onChange={(e) => setNamespace(e.target.value)}
                  className="block w-auto rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-blue-500"
                  disabled={isInvestigating}
                >
                  <option value="default">default</option>
                  <option value="kube-system">kube-system</option>
                  <option value="">All namespaces</option>
                </select>
              </div>
            </div>
            <InvestigateButton
              onClick={handleInvestigate}
              disabled={isInvestigating || clustersLoading}
              isLoading={isInvestigating}
            />
            {error && (
              <div className="mt-4 bg-red-50 text-red-600 p-4 rounded-lg text-sm whitespace-pre-line" role="alert">
                {error}
              </div>
            )}
          </div>

          <InvestigationProgress
            isInvestigating={isInvestigating}
            onComplete={() => {}}
          />

          <DiagnosisResult diagnosis={diagnosis} />
          
          {!isInvestigating && !diagnosis && !error && (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="mt-2 text-lg font-medium text-gray-900">Ready to Investigate</h3>
              <p className="mt-1 text-gray-500">Select a cluster and namespace, then click "Investigate Cluster" to start troubleshooting.</p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <SystemStatus />
          <InvestigationHistory
            investigations={history}
            isLoading={historyLoading}
          />
        </div>
      </div>
    </div>
  );
}

interface DiagnosisResultProps {
  diagnosis: {
    root_cause: string;
    explanation: string;
    fix: string;
    kubectl_commands: string[];
    prevention: string;
    confidence: number;
  } | null;
}
'use client';

interface InvestigationRecord {
  id: string;
  timestamp: string;
  namespace: string;
  root_cause: string;
  confidence: number;
  status: 'completed' | 'failed' | 'no_issues';
}

interface InvestigationHistoryProps {
  investigations: InvestigationRecord[];
  isLoading?: boolean;
}

export function InvestigationHistory({ investigations, isLoading }: InvestigationHistoryProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Investigation History</h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!investigations || investigations.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Investigation History</h2>
        <p className="text-gray-500 text-center py-8">No investigations yet. Click "Investigate Cluster" to start.</p>
      </div>
    );
  }

  const statusStyles: Record<string, string> = {
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    no_issues: 'bg-blue-100 text-blue-800',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Investigations</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Namespace</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Root Cause</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {investigations.map((record) => (
              <tr key={record.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900">
                  {new Date(record.timestamp).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900">{record.namespace || 'all'}</td>
                <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">{record.root_cause}</td>
                <td className="px-4 py-3 text-sm text-gray-900">{record.confidence}%</td>
                <td className="px-4 py-3 text-sm">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusStyles[record.status] || 'bg-gray-100 text-gray-800'}`}>
                    {record.status.replace('_', ' ')}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
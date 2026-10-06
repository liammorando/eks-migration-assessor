'use client';

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

export function DiagnosisResult({ diagnosis }: DiagnosisResultProps) {
  if (!diagnosis) {
    return null;
  }

  const confidenceColor =
    diagnosis.confidence >= 80
      ? 'text-green-600 bg-green-50'
      : diagnosis.confidence >= 50
      ? 'text-yellow-600 bg-yellow-50'
      : 'text-red-600 bg-red-50';

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Diagnosis</h2>
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">Root Cause</h3>
          <p className="text-gray-900">{diagnosis.root_cause}</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">Explanation</h3>
          <p className="text-gray-700 whitespace-pre-wrap">{diagnosis.explanation}</p>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">Suggested Fix</h3>
          <p className="text-gray-900">{diagnosis.fix}</p>
        </div>
        {diagnosis.kubectl_commands && diagnosis.kubectl_commands.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">kubectl Commands</h3>
            <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
              {diagnosis.kubectl_commands.map((cmd, index) => (
                <div key={index} className="text-green-300 font-mono text-sm mb-1">
                  $ {cmd}
                </div>
              ))}
            </div>
          </div>
        )}
        <div>
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-1">Prevention</h3>
          <p className="text-gray-700">{diagnosis.prevention}</p>
        </div>
        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-500">Confidence</span>
            <div className="flex items-center gap-3">
              <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    diagnosis.confidence >= 80 ? 'bg-green-500' : diagnosis.confidence >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${diagnosis.confidence}%` }}
                />
              </div>
              <span className={`text-sm font-semibold ${confidenceColor} px-2 py-1 rounded`}>
                {diagnosis.confidence}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
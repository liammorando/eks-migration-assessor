'use client';

import { useState, useEffect } from 'react';

interface InvestigationProgressProps {
  isInvestigating: boolean;
  onComplete?: () => void;
}

const STEPS = [
  { id: 'pods', label: 'Checking Pods' },
  { id: 'logs', label: 'Reading Logs' },
  { id: 'events', label: 'Analyzing Events' },
  { id: 'deployments', label: 'Inspecting Deployments' },
  { id: 'network', label: 'Checking Networking' },
  { id: 'ai', label: 'AI Reasoning' },
  { id: 'complete', label: 'Root Cause Found' },
];

export function InvestigationProgress({ isInvestigating, onComplete }: InvestigationProgressProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!isInvestigating) {
      setCurrentStep(0);
      setCompletedSteps(new Set());
      return;
    }

    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < STEPS.length - 1) {
          setCompletedSteps((prevSet) => new Set([...prevSet, prev]));
          return prev + 1;
        } else {
          clearInterval(interval);
          onComplete?.();
          return prev;
        }
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isInvestigating, onComplete]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Investigation Progress</h2>
      <div className="space-y-3">
        {STEPS.map((step, index) => {
          const isCompleted = completedSteps.has(index);
          const isCurrent = index === currentStep && isInvestigating;
          const isLast = index === STEPS.length - 1;

          return (
            <div
              key={step.id}
              className={`flex items-center gap-3 transition-colors ${
                isCurrent ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-400'
              }`}
            >
              <div className="flex items-center">
                {isCompleted ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : isCurrent ? (
                  <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  <div className="w-5 h-5 rounded-full border-2 border-gray-300 flex items-center justify-center" />
                )}
              </div>
              <span className={`font-medium ${isCurrent ? 'font-semibold' : ''}`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
'use client';

import { ButtonHTMLAttributes, forwardRef } from 'react';

interface InvestigateButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
}

export const InvestigateButton = forwardRef<HTMLButtonElement, InvestigateButtonProps>(
  ({ isLoading = false, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`
          w-full py-4 px-6 text-lg font-semibold text-white rounded-lg
          transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2
          ${isLoading || disabled
            ? 'bg-blue-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
          }
        `}
        {...props}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Investigating...
          </span>
        ) : (
          children || 'Investigate Cluster'
        )}
      </button>
    );
  }
);

InvestigateButton.displayName = 'InvestigateButton';
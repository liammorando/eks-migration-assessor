'use client';

export function SystemStatus() {
  return (
    <div className="mt-8 p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-center justify-center gap-2 text-gray-600">
        <span className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
        </span>
        <span className="text-sm font-medium">System Status: Ready</span>
      </div>
    </div>
  );
}
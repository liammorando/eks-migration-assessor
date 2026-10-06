'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';

export default function Home() {
  const router = useRouter();
  const { isLoading, isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 bg-gray-50">
      <div className="max-w-md w-full text-center">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-10">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">AI Kubernetes Agent</h1>
          <p className="text-xl text-gray-600 mb-8">Troubleshoot Kubernetes with AI</p>
          <div className="space-y-4">
            <Link
              href="/auth/signin"
              className="block w-full py-4 px-6 text-lg font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Sign In to Dashboard
            </Link>
            <Link
              href="/auth/signup"
              className="block w-full py-4 px-6 text-lg font-semibold text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              Create Account
            </Link>
          </div>
        </div>
        <div className="mt-8 text-sm text-gray-500">
          <p>Powered by InsForge Authentication</p>
        </div>
      </div>
    </main>
  );
}
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Auth check
const getToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  
  // Check URL first
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get('token');
  if (urlToken) {
    localStorage.setItem('seminars_token', urlToken);
    window.history.replaceState({}, '', window.location.pathname);
    return urlToken;
  }
  
  // Then check localStorage
  return localStorage.getItem('seminars_token');
};

// Simple test component
function TestComponent() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Seminars App</h1>
      <p className="text-gray-600">App is working!</p>
      <button 
        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded"
        onClick={() => alert('Button works!')}
      >
        Test Button
      </button>
    </div>
  );
}

function App() {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const t = getToken();
      setToken(t);
    } catch (e) {
      setError('Error checking auth: ' + (e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-red-50 flex items-center justify-center">
        <div className="text-xl text-red-600">{error}</div>
      </div>
    );
  }

  // If no token, redirect to login
  if (!token) {
    const currentUrl = window.location.href;
    const authUrl = `https://inacio-auth.fly.dev/login?returnTo=${encodeURIComponent(currentUrl)}`;
    window.location.href = authUrl;
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Redirecting to login...</div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <TestComponent />
      </div>
    </QueryClientProvider>
  );
}

export default App;

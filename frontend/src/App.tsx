import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect, Component, ReactNode } from 'react';
import { SeminarsModule } from './modules/seminars/SeminarsModule';
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
    // Clean URL
    window.history.replaceState({}, '', window.location.pathname);
    return urlToken;
  }
  
  // Then check localStorage
  return localStorage.getItem('seminars_token');
};

// Error Boundary
interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-red-50 p-8">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Something went wrong</h1>
          <pre className="bg-white p-4 rounded overflow-auto">{this.state.error?.message}</pre>
        </div>
      );
    }

    return this.props.children;
  }
}

function App() {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = getToken();
    setToken(t);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  // If no token, redirect to login
  if (!token) {
    const currentUrl = window.location.href;
    const authUrl = `https://inacio-auth.fly.dev/login?returnTo=${encodeURIComponent(currentUrl)}`;
    window.location.href = authUrl;
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-xl">Redirecting to login...</div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <div className="min-h-screen bg-gray-50">
          <SeminarsModule />
        </div>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}

export default App;

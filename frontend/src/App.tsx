import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SeminarsModule } from './modules/seminars/SeminarsModule';
import { Lock, LogOut } from 'lucide-react';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Get JWT token from URL (from auth service)
const getJWTFromURL = (): string | null => {
  if (typeof window === 'undefined') return null;
  
  const params = new URLSearchParams(window.location.search);
  const urlToken = params.get('token');
  if (urlToken) {
    localStorage.setItem('seminars_token', urlToken);
    window.history.replaceState({}, '', window.location.pathname);
    return urlToken;
  }
  return null;
};

// Check if we have a JWT token stored
const hasStoredJWT = (): boolean => {
  return !!localStorage.getItem('seminars_token');
};

// Password login component
function PasswordLogin({ onLogin }: { onLogin: () => void }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { loginWithPassword } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      await loginWithPassword(password);
      onLogin();
    } catch (err: any) {
      setError(err.message || 'Invalid password');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthServiceLogin = () => {
    const currentUrl = window.location.href;
    const authUrl = `https://inacio-auth.fly.dev/login?returnTo=${encodeURIComponent(currentUrl)}`;
    window.location.href = authUrl;
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
        <div className="flex items-center justify-center mb-6">
          <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
            <Lock className="w-6 h-6 text-primary-600" />
          </div>
        </div>
        
        <h1 className="text-2xl font-bold text-center text-gray-900 mb-2">
          Seminars App
        </h1>
        <p className="text-center text-gray-600 mb-6">
          Sign in to access the seminar management system
        </p>

        {/* Admin Login */}
        <div className="mb-6">
          <button
            onClick={handleAuthServiceLogin}
            className="w-full py-3 px-4 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
          >
            Sign in with Admin Account
          </button>
        </div>

        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">or continue with password</span>
          </div>
        </div>

        {/* Password Login */}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Editor Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              placeholder="Enter password"
              disabled={isLoading}
            />
            <p className="mt-1 text-xs text-gray-500">
              Editor access: view and edit only (no delete, no database)
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !password}
            className="w-full py-2 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing in...' : 'Sign in as Editor'}
          </button>
        </form>
      </div>
    </div>
  );
}

// Main app content
function AppContent() {
  const { token, isLoading, logout, isEditor } = useAuth();
  const [showLogin, setShowLogin] = useState(false);

  useEffect(() => {
    // Check for JWT in URL first (from auth service redirect)
    const jwtFromURL = getJWTFromURL();
    if (jwtFromURL) {
      // JWT was found and stored, auth provider will pick it up
      setShowLogin(false);
      return;
    }
    
    if (!isLoading) {
      // No token at all - show login
      if (!token && !hasStoredJWT()) {
        setShowLogin(true);
      } else {
        setShowLogin(false);
      }
    }
  }, [token, isLoading]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  // Show login if no token
  if (showLogin || (!token && !hasStoredJWT())) {
    return <PasswordLogin onLogin={() => setShowLogin(false)} />;
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        {/* Header with logout */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <h1 className="text-lg font-semibold text-gray-900">Seminars Management</h1>
            <div className="flex items-center gap-4">
              {isEditor && (
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                  Editor Mode
                </span>
              )}
              <button
                onClick={logout}
                className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
        <SeminarsModule />
      </div>
    </QueryClientProvider>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;

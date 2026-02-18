import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthStatus {
  authenticated: boolean;
  role: string | null;
  permissions: string[];
}

interface AuthContextType {
  authStatus: AuthStatus | null;
  isLoading: boolean;
  error: string | null;
  login: (code: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = '';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check auth status on mount (using cookie)
  useEffect(() => {
    const initAuth = async () => {
      // Check if auth is disabled by calling status
      try {
        const response = await fetch(`${API_URL}/api/v1/auth/status`, {
          credentials: 'include',  // Include cookies
        });
        if (response.ok) {
          const data = await response.json();
          if (data.authenticated) {
            setAuthStatus({ 
              authenticated: true, 
              role: data.role || 'admin', 
              permissions: data.permissions || ['admin'] 
            });
          }
        }
      } catch {
        // If status check fails, assume auth might be disabled
        setAuthStatus({ authenticated: true, role: 'admin', permissions: ['admin'] });
      }
      
      setIsLoading(false);
    };
    
    initAuth();
  }, []);

  const login = async (code: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
        credentials: 'include',  // Include cookies - this sets the cookie from the response
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setAuthStatus({
            authenticated: true,
            role: data.role,
            permissions: data.permissions,
          });
          return true;
        } else {
          setError('Invalid access code');
          return false;
        }
      } else {
        setError('Login failed');
        return false;
      }
    } catch {
      setError('Network error');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      // Call backend to clear cookie
      await fetch(`${API_URL}/api/v1/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch {
      // Ignore errors
    }
    
    setAuthStatus(null);
    
    // Remove access_code from URL if present
    const url = new URL(window.location.href);
    if (url.searchParams.has('access_code')) {
      url.searchParams.delete('access_code');
      window.history.replaceState({}, '', url.toString());
    }
  };

  return (
    <AuthContext.Provider value={{ authStatus, isLoading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

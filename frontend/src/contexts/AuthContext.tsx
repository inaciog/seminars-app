import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: string;
  role: 'admin' | 'editor';
  name: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  loginWithPassword: (password: string) => Promise<void>;
  logout: () => void;
  isEditor: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'seminars_auth';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load auth state from storage on mount
  useEffect(() => {
    const loadAuth = async () => {
      // First check new storage format
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        try {
          const auth = JSON.parse(stored);
          if (auth.token && auth.user) {
            setToken(auth.token);
            setUser(auth.user);
            setIsLoading(false);
            return;
          }
        } catch {
          localStorage.removeItem(STORAGE_KEY);
        }
      }

      // Check for JWT from auth service (stored by getJWTFromURL)
      const jwtToken = localStorage.getItem('seminars_token');
      if (jwtToken) {
        // Verify it's valid and get user info
        try {
          const res = await fetch('/api/auth/me', {
            headers: { Authorization: `Bearer ${jwtToken}` }
          });
          if (res.ok) {
            const userData: User = await res.json();
            setToken(jwtToken);
            setUser(userData);
            // Migrate to new storage
            localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: jwtToken, user: userData }));
          } else {
            // Invalid token, clear it
            localStorage.removeItem('seminars_token');
          }
        } catch {
          localStorage.removeItem('seminars_token');
        }
      }

      setIsLoading(false);
    };

    loadAuth();
  }, []);

  // Verify token with backend
  useEffect(() => {
    if (token && !isLoading) {
      fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(res => {
          if (!res.ok) throw new Error('Invalid token');
          return res.json();
        })
        .then((userData: User) => {
          setUser(userData);
          localStorage.setItem(STORAGE_KEY, JSON.stringify({ token, user: userData }));
        })
        .catch(() => {
          // Token invalid, clear it
          logout();
        });
    }
  }, [token]);

  const loginWithPassword = async (password: string) => {
    const res = await fetch('/api/auth/login-editor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password })
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Invalid password');
    }

    const data = await res.json();
    const userData: User = { id: 'editor', role: data.role, name: data.name };
    
    setToken(data.token);
    setUser(userData);
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ token: data.token, user: userData }));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem('seminars_token'); // Also clear old JWT token
  };

  const isEditor = user?.role === 'editor';
  const isAdmin = user?.role === 'admin';

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      isLoading, 
      loginWithPassword, 
      logout,
      isEditor,
      isAdmin
    }}>
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

import { useState, useEffect } from 'react';
import { SeminarsModule } from './seminars/SeminarsModule';
import './index.css';

// Auth context for token
const getToken = () => {
  const params = new URLSearchParams(window.location.search);
  return params.get('token') || localStorage.getItem('token');
};

function App() {
  const [token, setToken] = useState<string | null>(getToken());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Store token from URL
    const urlToken = new URLSearchParams(window.location.search).get('token');
    if (urlToken) {
      localStorage.setItem('token', urlToken);
      setToken(urlToken);
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    }
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  // If no token, show login redirect
  if (!token) {
    const authUrl = `https://inacio-auth.fly.dev/login?returnTo=${encodeURIComponent(window.location.href)}`;
    window.location.href = authUrl;
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-xl">Redirecting to login...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <SeminarsModule />
    </div>
  );
}

export default App;

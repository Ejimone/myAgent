import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import authService from '../services/authService';

function GoogleCallbackPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      const params = new URLSearchParams(location.search);
      const code = params.get('code');

      if (!code) {
        setError('Authorization code not found in callback URL.');
        setLoading(false);
        return;
      }

      try {
        // Use one of the authorized redirect URIs from credentials.json
        const redirectUri = "http://localhost:8000/accounts/google/login/callback/";
        await authService.handleGoogleCallback(code, redirectUri);
        navigate('/dashboard'); // Redirect to dashboard on success
      } catch (err) {
        console.error('Google callback error:', err);
        setError('Failed to process Google login. Please try again.');
        setLoading(false);
        // Optionally redirect back to login after a delay
        // setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [location, navigate]);

  return (
    <div>
      <h2>Processing Google Login...</h2>
      {loading && <p>Please wait...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {!loading && !error && <p>Redirecting...</p>}
    </div>
  );
}

export default GoogleCallbackPage;
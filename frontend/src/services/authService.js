import apiClient from './api';

const authService = {
  // Standard email/password login
  login: async (email, password) => {
    try {
      const response = await apiClient.post('/auth/token', new URLSearchParams({
        username: email,
        password: password,
      }), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      if (response.data.access_token) {
        localStorage.setItem('authToken', response.data.access_token);
      }
      return response.data;
    } catch (error) {
      console.error('Login failed:', error.response?.data || error.message);
      throw error;
    }
  },

  // User registration
  register: async (email, fullName, password) => {
    try {
      const response = await apiClient.post('/auth/register', {
        email,
        full_name: fullName,
        password,
      });
      return response.data;
    } catch (error) {
      console.error('Registration failed:', error.response?.data || error.message);
      throw error;
    }
  },

  // Get Google OAuth login URL
  getGoogleLoginUrl: async () => {
    try {
      const response = await apiClient.get('/auth/google/login');
      return response.data.auth_url;
    } catch (error) {
      console.error('Failed to get Google login URL:', error.response?.data || error.message);
      throw error;
    }
  },

  // Handle Google OAuth callback
  handleGoogleCallback: async (code, redirectUri) => {
    try {
      const response = await apiClient.post('/auth/google/callback', {
        code,
        redirect_uri: redirectUri,
      });
      if (response.data.access_token) {
        localStorage.setItem('authToken', response.data.access_token);
      }
      return response.data;
    } catch (error) {
      console.error('Google callback failed:', error.response?.data || error.message);
      throw error;
    }
  },

  // Get current user info
  getCurrentUser: async () => {
    try {
      const response = await apiClient.get('/auth/me');
      return response.data;
    } catch (error) {
      // Error handled by interceptor, but we might want specific logic here
      console.error('Failed to get current user:', error.response?.data || error.message);
      throw error;
    }
  },

  // Logout
  logout: () => {
    localStorage.removeItem('authToken');
    // Optionally: Call a backend endpoint to invalidate the token
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('authToken');
  },
};

export default authService;
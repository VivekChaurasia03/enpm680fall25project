import api from './api';

/**
 * Register new user
 */
export const register = async (userData) => {
  try {
    const response = await api.post('/api/auth/register', userData);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Registration failed',
    };
  }
};

/**
 * Login user
 */
export const login = async (email, password) => {
  try {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const { access_token, user } = response.data;

    // Store token and user info
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user', JSON.stringify(user));

    return { success: true, data: { token: access_token, user } };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Login failed',
    };
  }
};

/**
 * Logout user
 */
export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = '/login';
};

/**
 * Get current user from localStorage
 */
export const getCurrentUser = () => {
  try {
    const userStr = localStorage.getItem('user');
    if (!userStr || userStr === 'undefined') {
      return null;
    }
    return JSON.parse(userStr);
  } catch (error) {
    console.error('Error parsing user data:', error);
    return null;
  }
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

/**
 * Get user profile from API
 */
export const getProfile = async () => {
  try {
    const response = await api.get('/api/auth/me');
    localStorage.setItem('user', JSON.stringify(response.data));
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch profile',
    };
  }
};
import { createContext, useState, useEffect } from 'react';
import { getCurrentUser, isAuthenticated, logout as logoutService } from '../services/authService';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = () => {
      if (isAuthenticated()) {
        try {
          const currentUser = getCurrentUser();
          if (currentUser) {
            setUser(currentUser);
          }
        } catch (error) {
          console.error('Error loading user:', error);
          localStorage.removeItem('user');
          localStorage.removeItem('access_token');
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = (userData) => {
    setUser(userData);
  };

  const logout = () => {
    setUser(null);
    logoutService();
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  const isFleetManager = () => {
    return user?.role === 'FLEET_MANAGER';
  };

  const isAdmin = () => {
    return user?.role === 'ADMIN';
  };

  const isFleetUser = () => {
    return user?.role === 'FLEET_USER';
  };

  const value = {
    user,
    login,
    logout,
    updateUser,
    isAuthenticated: !!user,
    isFleetManager,
    isAdmin,
    isFleetUser,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
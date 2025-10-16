import api from './api';

/**
 * Get all users (Admin only)
 */
export const getAllUsers = async () => {
  try {
    const response = await api.get('/api/users');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch users',
    };
  }
};

/**
 * Get fleet users only (Fleet Manager only)
 */
export const getFleetUsers = async () => {
  try {
    const response = await api.get('/api/users/fleet-users');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch fleet users',
    };
  }
};

/**
 * Get specific user details (Fleet Manager only)
 */
export const getUser = async (userId) => {
  try {
    const response = await api.get(`/api/users/${userId}`);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch user details',
    };
  }
};

/**
 * Update user information (Fleet Manager only)
 */
export const updateUser = async (userId, userData) => {
  try {
    const response = await api.patch(`/api/users/${userId}`, userData);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to update user',
    };
  }
};

/**
 * Delete user (Admin only)
 */
export const deleteUser = async (userId) => {
  try {
    await api.delete(`/api/users/${userId}`);
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to delete user',
    };
  }
};

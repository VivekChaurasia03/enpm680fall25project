import api from './api';

/**
 * Get all reservations for current user
 */
export const getMyReservations = async () => {
  try {
    const userResponse = await api.get('/api/auth/me');
    const user = userResponse.data;
    
    const response = await api.get(`/api/reservations/user/${user.user_id}`);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch reservations',
    };
  }
};

/**
 * Get all reservations (Fleet Manager only)
 */
export const getAllReservations = async () => {
  try {
    const response = await api.get('/api/reservations');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch all reservations',
    };
  }
};

/**
 * Create new reservation
 * Fleet Users: Can create for themselves (only vehicleId needed)
 * Fleet Managers: Can create for any user (userId and vehicleId needed)
 */
export const createReservation = async (vehicleId, userId = null) => {
  try {
    // If userId not provided, get current user's ID
    let targetUserId = userId;
    
    if (!targetUserId) {
      const userResponse = await api.get('/api/auth/me');
      targetUserId = userResponse.data.user_id;
    }
    
    const response = await api.post('/api/reservations', { 
      user_id: targetUserId, 
      vehicle_id: vehicleId 
    });
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to create reservation',
    };
  }
};

/**
 * Return vehicle (complete reservation)
 */
export const returnVehicle = async (reservationId) => {
  try {
    const response = await api.post('/api/reservations/return', {
      reservation_id: reservationId
    });
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to return vehicle',
    };
  }
};

/**
 * Cancel reservation
 */
export const cancelReservation = async (reservationId) => {
  try {
    // Since backend doesn't have cancel endpoint, we'll use return
    const response = await api.post('/api/reservations/return', {
      reservation_id: reservationId
    });
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to cancel reservation',
    };
  }
};

/**
 * Get pending returns (Fleet Manager only) - Alias for active reservations
 */
export const getPendingReturns = async () => {
  try {
    const response = await api.get('/api/reservations/pending-return');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch pending returns',
    };
  }
};

/**
 * Get active reservations (Fleet Manager only)
 */
export const getActiveReservations = async () => {
  try {
    const response = await api.get('/api/reservations/active');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch active reservations',
    };
  }
};

/**
 * Get specific reservation details
 */
export const getReservation = async (reservationId) => {
  try {
    const response = await api.get(`/api/reservations/${reservationId}`);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch reservation details',
    };
  }
};
import api from './api';

/**
 * Get all vehicles
 */
export const getAllVehicles = async () => {
  try {
    const response = await api.get('/api/vehicles');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch vehicles',
    };
  }
};

/**
 * Get vehicle by ID
 */
export const getVehicleById = async (vehicleId) => {
  try {
    const response = await api.get(`/api/vehicles/${vehicleId}`);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch vehicle',
    };
  }
};

/**
 * Create new vehicle (Fleet Manager only)
 */
export const createVehicle = async (vehicleData) => {
  try {
    const response = await api.post('/api/vehicles', vehicleData);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to create vehicle',
    };
  }
};

/**
 * Update vehicle (Fleet Manager only)
 */
export const updateVehicle = async (vehicleId, vehicleData) => {
  try {
    const response = await api.patch(`/api/vehicles/${vehicleId}`, vehicleData);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to update vehicle',
    };
  }
};

/**
 * Delete vehicle (Fleet Manager only)
 */
export const deleteVehicle = async (vehicleId) => {
  try {
    await api.delete(`/api/vehicles/${vehicleId}`);
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to delete vehicle',
    };
  }
};

/**
 * Get available vehicles only
 */
export const getAvailableVehicles = async () => {
  try {
    const response = await api.get('/api/vehicles');
    const availableVehicles = response.data.filter(
      (vehicle) => vehicle.status === 'AVAILABLE'
    );
    return { success: true, data: availableVehicles };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch available vehicles',
    };
  }
};

/**
 * Chatbot: Get manufacturers
 */
export const getManufacturers = async () => {
  try {
    const response = await api.get('/api/chatbot/manufacturers');
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch manufacturers',
    };
  }
};

/**
 * Chatbot: Get models by manufacturer
 */
export const getModelsByManufacturer = async (manufacturer) => {
  try {
    const response = await api.get(`/api/chatbot/models?manufacturer=${manufacturer}`);
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch models',
    };
  }
};

/**
 * Chatbot: Check vehicle availability
 */
export const checkAvailability = async (manufacturer, model) => {
  try {
    const response = await api.post('/api/chatbot/availability', {
      manufacturer,
      model,
    });
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to check availability',
    };
  }
};
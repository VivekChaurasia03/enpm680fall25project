import api from './api';

/**
 * Get list of available manufacturers
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
 * Get models for a specific manufacturer
 */
export const getModelsByManufacturer = async (manufacturer) => {
  try {
    const response = await api.get('/api/chatbot/models', {
      params: { manufacturer },
    });
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || 'Failed to fetch models',
    };
  }
};

/**
 * Check availability for a specific manufacturer and model
 * NOTE: Backend uses POST method, not GET
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
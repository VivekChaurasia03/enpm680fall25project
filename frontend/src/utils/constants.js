// API Base URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// User Roles - MUST MATCH BACKEND EXACTLY
export const USER_ROLES = {
  FLEET_USER: 'FLEET_USER',
  FLEET_MANAGER: 'FLEET_MANAGER',
  ADMIN: 'ADMIN'
};

// Vehicle Status
export const VEHICLE_STATUS = {
  AVAILABLE: 'AVAILABLE',
  RENTED: 'RENTED',
  MAINTENANCE: 'MAINTENANCE',
  UNAVAILABLE: 'UNAVAILABLE'
};

// Reservation Status
export const RESERVATION_STATUS = {
  ACTIVE: 'ACTIVE',
  COMPLETED: 'COMPLETED',
  CANCELLED: 'CANCELLED'
};

// Status Colors for UI
export const STATUS_COLORS = {
  AVAILABLE: 'bg-green-100 text-green-800 border-green-300',
  RENTED: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  MAINTENANCE: 'bg-red-100 text-red-800 border-red-300',
  UNAVAILABLE: 'bg-gray-100 text-gray-800 border-gray-300'
};

// Reservation limits
export const MAX_RESERVATIONS = 3;

// Vehicle placeholder image
export const VEHICLE_PLACEHOLDER = 'https://via.placeholder.com/400x300/4F46E5/FFFFFF?text=Vehicle';
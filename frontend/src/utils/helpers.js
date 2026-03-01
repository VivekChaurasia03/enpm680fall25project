import { format } from 'date-fns';

/**
 * Format date to readable string
 */
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    return format(new Date(dateString), 'MMM dd, yyyy');
  } catch {
    return 'Invalid Date';
  }
};

/**
 * Format datetime to readable string
 */
export const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
  } catch {
    return 'Invalid Date';
  }
};

/**
 * Get initials from name
 */
export const getInitials = (name) => {
  if (!name) return 'U';
  const names = name.split(' ');
  if (names.length === 1) return names[0].charAt(0).toUpperCase();
  return (names[0].charAt(0) + names[names.length - 1].charAt(0)).toUpperCase();
};

/**
 * Validate email format
 */
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate phone format
 */
export const isValidPhone = (phone) => {
  const phoneRegex = /^\d{10,15}$/;
  return phoneRegex.test(phone.replace(/[\s-]/g, ''));
};

/**
 * Check if user can make more reservations
 */
export const canMakeReservation = (currentCount, maxAllowed = 3) => {
  return currentCount < maxAllowed;
};

/**
 * Get vehicle image or placeholder
 */
export const getVehicleImage = (manufacturer, model) => {
  // Since we don't have real images, return placeholder
  return `https://via.placeholder.com/400x300/4F46E5/FFFFFF?text=${encodeURIComponent(manufacturer + ' ' + model)}`;
};
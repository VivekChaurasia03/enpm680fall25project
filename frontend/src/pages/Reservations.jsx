import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  getMyReservations,
  getAllReservations,
  createReservation,
  returnVehicle,
} from '../services/reservationService';
import { getAllVehicles } from '../services/vehicleService';
import { getAllUsers } from '../services/userService';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { formatDateTime } from '../utils/helpers';
import toast from 'react-hot-toast';

const Reservations = () => {
  const { isFleetManager, user } = useAuth();
  const [reservations, setReservations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  
  // For Fleet Manager reservation creation
  const [users, setUsers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedVehicleId, setSelectedVehicleId] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    loadReservations();
    if (isFleetManager()) {
      loadUsersAndVehicles();
    }
  }, []);

  const loadReservations = async () => {
    setLoading(true);
    const result = isFleetManager() 
      ? await getAllReservations()
      : await getMyReservations();

    if (result.success) {
      setReservations(result.data);
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };

  const loadUsersAndVehicles = async () => {
    const [usersResult, vehiclesResult] = await Promise.all([
      getAllUsers(),
      getAllVehicles()
    ]);

    if (usersResult.success) {
      // Filter only Fleet Users
      const fleetUsers = usersResult.data.filter(u => u.role === 'FLEET_USER');
      setUsers(fleetUsers);
    }

    if (vehiclesResult.success) {
      // Filter only available vehicles
      const availableVehicles = vehiclesResult.data.filter(v => v.status === 'AVAILABLE');
      setVehicles(availableVehicles);
    }
  };

  const handleCreateReservation = async (e) => {
    e.preventDefault();
    
    if (!selectedUserId || !selectedVehicleId) {
      toast.error('Please select both user and vehicle');
      return;
    }

    setFormLoading(true);
    const result = await createReservation(selectedVehicleId, selectedUserId);

    if (result.success) {
      toast.success('Reservation created successfully!');
      setShowCreateForm(false);
      setSelectedUserId('');
      setSelectedVehicleId('');
      loadReservations();
      loadUsersAndVehicles(); // Refresh to update available vehicles
    } else {
      toast.error(result.error);
    }

    setFormLoading(false);
  };

  const handleReturnVehicle = async (reservationId) => {
    if (!window.confirm('Process vehicle return?')) {
      return;
    }

    const result = await returnVehicle(reservationId);
    if (result.success) {
      toast.success('Vehicle returned successfully!');
      loadReservations();
      if (isFleetManager()) {
        loadUsersAndVehicles(); // Refresh available vehicles
      }
    } else {
      toast.error(result.error);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading reservations..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Reservations</h1>
          <p className="text-gray-600 mt-2">
            {isFleetManager()
              ? 'Manage all vehicle reservations'
              : 'View your active and past reservations'}
          </p>
        </div>

        {isFleetManager() && (
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition flex items-center gap-2"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Reservation
          </button>
        )}
      </div>

      {/* Create Reservation Form Modal (Fleet Manager Only) */}
      {showCreateForm && isFleetManager() && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Reservation</h2>
            
            <form onSubmit={handleCreateReservation} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Fleet User
                </label>
                <select
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- Select User --</option>
                  {users.map((u) => (
                    <option key={u.user_id} value={u.user_id}>
                      {u.name} - {u.email} (Reservations: {u.reservation_count}/3)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Available Vehicle
                </label>
                <select
                  value={selectedVehicleId}
                  onChange={(e) => setSelectedVehicleId(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- Select Vehicle --</option>
                  {vehicles.map((v) => (
                    <option key={v.vehicle_id} value={v.vehicle_id}>
                      {v.manufacturer} {v.model} - {v.license_plate}
                    </option>
                  ))}
                </select>
                {vehicles.length === 0 && (
                  <p className="text-sm text-red-600 mt-1">No vehicles available</p>
                )}
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setSelectedUserId('');
                    setSelectedVehicleId('');
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formLoading}
                  className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {formLoading ? 'Creating...' : 'Create Reservation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reservations List */}
      <div className="bg-white rounded-lg shadow">
        {reservations.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No reservations found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Vehicle
                  </th>
                  {isFleetManager() && (
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                  )}
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reserved On
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Returned On
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  {isFleetManager() && (
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {reservations.map((reservation) => (
                  <tr key={reservation.reservation_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {reservation.vehicle.manufacturer} {reservation.vehicle.model}
                      </div>
                      <div className="text-sm text-gray-500">
                        {reservation.vehicle.license_plate}
                      </div>
                    </td>
                    {isFleetManager() && (
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{reservation.user.name}</div>
                        <div className="text-sm text-gray-500">{reservation.user.email}</div>
                      </td>
                    )}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDateTime(reservation.reservation_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {reservation.return_date ? formatDateTime(reservation.return_date) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          reservation.status === 'ACTIVE'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {reservation.status}
                      </span>
                    </td>
                    {isFleetManager() && (
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {reservation.status === 'ACTIVE' && (
                          <button
                            onClick={() => handleReturnVehicle(reservation.reservation_id)}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            Process Return
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Reservations;
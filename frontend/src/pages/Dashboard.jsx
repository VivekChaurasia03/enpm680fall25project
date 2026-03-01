import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { getMyReservations, getAllReservations } from '../services/reservationService';
import { getAllVehicles } from '../services/vehicleService';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { formatDateTime } from '../utils/helpers';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const { user, isFleetManager } = useAuth();
  const [stats, setStats] = useState({
    myReservations: 0,
    activeReservations: 0,
    availableVehicles: 0,
    totalVehicles: 0,
  });
  const [recentReservations, setRecentReservations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);

    try {
      // Get vehicles data
      const vehiclesResult = await getAllVehicles();
      const allVehicles = vehiclesResult.success ? vehiclesResult.data : [];
      const availableVehicles = allVehicles.filter(v => v.status === 'AVAILABLE');

      if (isFleetManager()) {
        // Fleet Manager: Show all system reservations
        const reservationsResult = await getAllReservations();
        if (reservationsResult.success) {
          const allReservations = reservationsResult.data;
          const activeReservations = allReservations.filter(r => r.status === 'ACTIVE');

          setStats({
            myReservations: allReservations.length,
            activeReservations: activeReservations.length,
            availableVehicles: availableVehicles.length,
            totalVehicles: allVehicles.length,
          });

          setRecentReservations(allReservations.slice(0, 5));
        }
      } else {
        // Fleet User: Show only their reservations
        const reservationsResult = await getMyReservations();
        if (reservationsResult.success) {
          const myReservations = reservationsResult.data;
          const activeReservations = myReservations.filter(r => r.status === 'ACTIVE');

          setStats({
            myReservations: myReservations.length,
            activeReservations: activeReservations.length,
            availableVehicles: availableVehicles.length,
            totalVehicles: allVehicles.length,
          });

          setRecentReservations(myReservations.slice(0, 5));
        }
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }

    setLoading(false);
  };

  if (loading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.name}!
        </h1>
        <p className="text-gray-600 mt-2">
          {isFleetManager()
            ? 'Manage your fleet and reservations from this dashboard.'
            : 'View your reservations and browse available vehicles.'}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-indigo-100 text-indigo-600">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">
                {isFleetManager() ? 'Total Reservations' : 'My Reservations'}
              </p>
              <p className="text-2xl font-bold text-gray-900">{stats.myReservations}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Active Reservations</p>
              <p className="text-2xl font-bold text-gray-900">{stats.activeReservations}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12M8 12h12m-7 5h7M3 7h.01M3 12h.01M3 17h.01" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Available Vehicles</p>
              <p className="text-2xl font-bold text-gray-900">{stats.availableVehicles}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Total Vehicles</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalVehicles}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <Link
          to="/vehicles"
          className="bg-indigo-600 text-white rounded-lg shadow p-6 hover:bg-indigo-700 transition"
        >
          <h3 className="text-xl font-bold mb-2">Browse Vehicles</h3>
          <p className="text-indigo-100">
            {isFleetManager() 
              ? 'View and manage all fleet vehicles'
              : 'View available vehicles and make reservations'}
          </p>
        </Link>

        <Link
          to="/reservations"
          className="bg-purple-600 text-white rounded-lg shadow p-6 hover:bg-purple-700 transition"
        >
          <h3 className="text-xl font-bold mb-2">
            {isFleetManager() ? 'Manage Reservations' : 'My Reservations'}
          </h3>
          <p className="text-purple-100">
            {isFleetManager()
              ? 'Process returns and view all reservations'
              : 'View and manage your current and past reservations'}
          </p>
        </Link>
      </div>

      {/* Recent Reservations */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">
            {isFleetManager() ? 'Recent Reservations' : 'My Recent Reservations'}
          </h2>
        </div>
        <div className="p-6">
          {recentReservations.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No reservations yet</p>
          ) : (
            <div className="space-y-4">
              {recentReservations.map((reservation) => (
                <div
                  key={reservation.reservation_id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
                >
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">
                      {reservation.vehicle.manufacturer} {reservation.vehicle.model}
                    </p>
                    <p className="text-sm text-gray-600">
                      License: {reservation.vehicle.license_plate}
                    </p>
                    {isFleetManager() && (
                      <p className="text-sm text-gray-600">
                        User: {reservation.user.name} ({reservation.user.email})
                      </p>
                    )}
                    <p className="text-sm text-gray-500 mt-1">
                      Reserved: {formatDateTime(reservation.reservation_date)}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      reservation.status === 'ACTIVE'
                        ? 'bg-green-100 text-green-800'
                        : reservation.status === 'COMPLETED'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {reservation.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
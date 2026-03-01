import { useState, useEffect } from 'react';
import { getAllUsers, deleteUser } from '../services/userService';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { USER_ROLES } from '../utils/constants';
import { formatDateTime, getInitials } from '../utils/helpers';
import toast from 'react-hot-toast';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    const result = await getAllUsers();
    if (result.success) {
      setUsers(result.data);
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };


  const handleDeleteUser = async (userId, userName) => {
    if (!window.confirm(`Delete user ${userName}? This action cannot be undone.`)) {
      return;
    }

    const result = await deleteUser(userId);
    if (result.success) {
      toast.success('User deleted successfully!');
      loadUsers();
    } else {
      toast.error(result.error);
    }
  };

  const filteredUsers = users.filter(
    (user) =>
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.employee_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <LoadingSpinner message="Loading users..." />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
        <p className="text-gray-600 mt-2">Manage user accounts and roles</p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search by name, email, or employee ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      {/* Users Grid */}
      {filteredUsers.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-500">No users found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredUsers.map((user) => (
            <div key={user.user_id} className="bg-white rounded-lg shadow p-6">
              {/* User Avatar */}
              <div className="flex items-center mb-4">
                <div className="h-12 w-12 rounded-full bg-indigo-600 flex items-center justify-center text-white font-semibold text-lg">
                  {getInitials(user.name)}
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-semibold text-gray-900">{user.name}</h3>
                  <p className="text-sm text-gray-500">{user.employee_id}</p>
                </div>
              </div>

              {/* User Details */}
              <div className="space-y-2 mb-4">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Email:</span> {user.email}
                </p>
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Phone:</span> {user.phone}
                </p>
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Reservations:</span>{' '}
                  {user.reservation_count}
                </p>
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Joined:</span>{' '}
                  {formatDateTime(user.created_at)}
                </p>
              </div>

              {/* Role Display */}
              <div className="mb-4">
                <span
                  className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    user.role === 'FLEET_MANAGER'
                      ? 'bg-purple-100 text-purple-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}
                >
                  {user.role === 'FLEET_MANAGER' ? 'Fleet Manager' : 'Fleet User'}
                </span>
              </div>

              {/* Delete Button */}
              {user.role !== 'FLEET_MANAGER' && user.reservation_count === 0 && (
                <button
                  onClick={() => handleDeleteUser(user.user_id, user.name)}
                  className="w-full bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition"
                >
                  Delete User
                </button>
              )}
              {user.role === 'FLEET_MANAGER' && (
                <div className="text-center text-sm text-gray-500 py-2">
                  Fleet Managers cannot be deleted
                </div>
              )}
              {user.reservation_count > 0 && user.role !== 'FLEET_MANAGER' && (
                <div className="text-center text-sm text-gray-500 py-2">
                  Cannot delete user with active reservations
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Users;
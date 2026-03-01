import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getInitials } from '../../utils/helpers';

const Navbar = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-indigo-600 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <Link to="/dashboard" className="flex items-center">
              <svg
                className="h-8 w-8 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7h12M8 12h12m-7 5h7M3 7h.01M3 12h.01M3 17h.01"
                />
              </svg>
              <span className="ml-2 text-xl font-bold text-white">FleetWise</span>
            </Link>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center space-x-4">
            <Link
              to="/dashboard"
              className="text-white hover:bg-indigo-700 px-3 py-2 rounded-md text-sm font-medium transition"
            >
              Dashboard
            </Link>

            <Link
              to="/vehicles"
              className="text-white hover:bg-indigo-700 px-3 py-2 rounded-md text-sm font-medium transition"
            >
              Vehicles
            </Link>

            <Link
              to="/reservations"
              className="text-white hover:bg-indigo-700 px-3 py-2 rounded-md text-sm font-medium transition"
            >
              Reservations
            </Link>

            {isAdmin() && (
              <Link
                to="/users"
                className="text-white hover:bg-indigo-700 px-3 py-2 rounded-md text-sm font-medium transition"
              >
                Users
              </Link>
            )}

            {/* User Menu */}
            <div className="flex items-center space-x-3 ml-4 border-l border-indigo-500 pl-4">
              <div className="flex items-center">
                <div className="h-8 w-8 rounded-full bg-indigo-800 flex items-center justify-center text-white font-semibold">
                  {getInitials(user?.name)}
                </div>
                <div className="ml-2 text-white">
                  <p className="text-sm font-medium">{user?.name}</p>
                  <p className="text-xs text-indigo-200">
                    {user?.role?.replace('_', ' ')}
                  </p>
                </div>
              </div>

              <button
                onClick={handleLogout}
                className="text-white hover:bg-indigo-700 px-3 py-2 rounded-md text-sm font-medium transition"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
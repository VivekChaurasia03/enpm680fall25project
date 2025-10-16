import { VEHICLE_STATUS, STATUS_COLORS } from '../../utils/constants';
import { useAuth } from '../../hooks/useAuth';

const VehicleCard = ({ vehicle, onEdit, onDelete }) => {
  const { isFleetManager, isFleetUser } = useAuth();

  const getStatusBadge = (status) => {
    const colorClass = STATUS_COLORS[status] || 'bg-gray-100 text-gray-800';
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${colorClass} border`}>
        {status}
      </span>
    );
  };

  const isRented = vehicle.status === VEHICLE_STATUS.RENTED;

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      {/* Vehicle Image Placeholder */}
      <div className="h-48 bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
        <svg
          className="h-24 w-24 text-white opacity-50"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
          />
        </svg>
      </div>

      {/* Vehicle Details */}
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900">
              {vehicle.manufacturer} {vehicle.model}
            </h3>
            <p className="text-sm text-gray-600 mt-1">{vehicle.license_plate}</p>
          </div>
          {getStatusBadge(vehicle.status)}
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex items-center text-sm text-gray-600">
            <svg
              className="h-5 w-5 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Rental Count: {vehicle.rental_count}
          </div>
        </div>

        {/* Fleet Manager Actions */}
        {isFleetManager() && (
          <div className="flex gap-2">
            {onEdit && (
              <button
                onClick={() => onEdit(vehicle)}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
              >
                Edit
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(vehicle)}
                disabled={isRented}
                className={`flex-1 px-4 py-2 rounded-md transition ${
                  isRented
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed opacity-60'
                    : 'bg-red-600 text-white hover:bg-red-700 cursor-pointer'
                }`}
                title={isRented ? 'Cannot delete rented vehicle' : 'Delete vehicle'}
              >
                Delete
              </button>
            )}
          </div>
        )}

        {/* Fleet User Info Message */}
        {isFleetUser() && (
          <div className="bg-indigo-50 border border-indigo-200 rounded-md p-3">
            <p className="text-sm text-indigo-800 text-center">
              {vehicle.status === VEHICLE_STATUS.AVAILABLE ? (
                <>
                  <span className="font-semibold">Available for reservation</span>
                  <br />
                  Contact Fleet Manager to reserve this vehicle
                </>
              ) : (
                <>
                  <span className="font-semibold">Currently unavailable</span>
                  <br />
                  This vehicle is currently rented
                </>
              )}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default VehicleCard;
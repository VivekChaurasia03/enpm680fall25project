import { formatDateTime, getVehicleImage } from '../../utils/helpers';
import { STATUS_COLORS } from '../../utils/constants';

const VehicleDetails = ({ vehicle, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Vehicle Details</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Vehicle Image */}
          <div className="mb-6">
            <img
              src={getVehicleImage(vehicle.manufacturer, vehicle.model)}
              alt={`${vehicle.manufacturer} ${vehicle.model}`}
              className="w-full h-64 object-cover rounded-lg"
            />
          </div>

          {/* Vehicle Information */}
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Manufacturer</p>
                <p className="text-lg font-semibold text-gray-900">
                  {vehicle.manufacturer}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Model</p>
                <p className="text-lg font-semibold text-gray-900">{vehicle.model}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">License Plate</p>
                <p className="text-lg font-semibold text-gray-900">
                  {vehicle.license_plate}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Status</p>
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${
                    STATUS_COLORS[vehicle.status]
                  }`}
                >
                  {vehicle.status}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Total Rentals</p>
                <p className="text-lg font-semibold text-gray-900">
                  {vehicle.rental_count}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Added On</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatDateTime(vehicle.created_at)}
                </p>
              </div>
            </div>
          </div>

          {/* Close Button */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VehicleDetails;
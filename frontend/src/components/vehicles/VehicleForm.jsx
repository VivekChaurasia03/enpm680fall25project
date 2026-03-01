import { useState, useEffect } from 'react';

const VehicleForm = ({ vehicle, onSubmit, onCancel, loading }) => {
  const [formData, setFormData] = useState({
    manufacturer: '',
    model: '',
    license_plate: '',
  });

  useEffect(() => {
    if (vehicle) {
      setFormData({
        manufacturer: vehicle.manufacturer,
        model: vehicle.model,
        license_plate: vehicle.license_plate,
      });
    }
  }, [vehicle]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Manufacturer
        </label>
        <input
          type="text"
          name="manufacturer"
          value={formData.manufacturer}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="e.g., Toyota"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Model
        </label>
        <input
          type="text"
          name="model"
          value={formData.model}
          onChange={handleChange}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="e.g., Camry"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          License Plate
        </label>
        <input
          type="text"
          name="license_plate"
          value={formData.license_plate}
          onChange={handleChange}
          required
          disabled={!!vehicle} // Can't change license plate when editing
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:bg-gray-100"
          placeholder="e.g., ABC-1234"
        />
        {vehicle && (
          <p className="text-xs text-gray-500 mt-1">License plate cannot be changed</p>
        )}
      </div>

      {vehicle && (
        <div className="bg-blue-50 p-3 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Current Status:</strong> {vehicle.status}
          </p>
          <p className="text-xs text-blue-600 mt-1">
            Status changes automatically when vehicles are reserved or returned.
          </p>
        </div>
      )}

      <div className="flex gap-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {loading ? 'Saving...' : vehicle ? 'Update Vehicle' : 'Add Vehicle'}
        </button>
      </div>
    </form>
  );
};

export default VehicleForm;
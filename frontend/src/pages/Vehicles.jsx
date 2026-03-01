import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  getAllVehicles,
  createVehicle,
  updateVehicle,
  deleteVehicle,
} from '../services/vehicleService';
import VehicleList from '../components/vehicles/VehicleList';
import VehicleForm from '../components/vehicles/VehicleForm';
import toast from 'react-hot-toast';

const Vehicles = () => {
  const { isFleetManager } = useAuth();
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState(null);
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    loadVehicles();
  }, []);

  const loadVehicles = async () => {
    setLoading(true);
    const result = await getAllVehicles();
    if (result.success) {
      setVehicles(result.data);
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };

  const handleAddVehicle = () => {
    setEditingVehicle(null);
    setShowForm(true);
  };

  const handleEditVehicle = (vehicle) => {
    setEditingVehicle(vehicle);
    setShowForm(true);
  };

  const handleFormSubmit = async (formData) => {
    setFormLoading(true);

    let result;
    if (editingVehicle) {
      result = await updateVehicle(editingVehicle.vehicle_id, formData);
    } else {
      result = await createVehicle(formData);
    }

    if (result.success) {
      toast.success(
        editingVehicle ? 'Vehicle updated successfully!' : 'Vehicle added successfully!'
      );
      setShowForm(false);
      setEditingVehicle(null);
      loadVehicles();
    } else {
      toast.error(result.error);
    }

    setFormLoading(false);
  };

  const handleDeleteVehicle = async (vehicle) => {
    if (vehicle.status === 'RENTED') {
      toast.error('Cannot delete a rented vehicle');
      return;
    }

    if (
      !window.confirm(
        `Are you sure you want to delete ${vehicle.manufacturer} ${vehicle.model}?`
      )
    ) {
      return;
    }

    const result = await deleteVehicle(vehicle.vehicle_id);
    if (result.success) {
      toast.success('Vehicle deleted successfully!');
      loadVehicles();
    } else {
      toast.error(result.error);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Vehicles</h1>
          <p className="text-gray-600 mt-2">
            {isFleetManager()
              ? 'Manage your fleet vehicles'
              : 'Browse available vehicles - Contact Fleet Manager to reserve'}
          </p>
        </div>

        {isFleetManager() && (
          <button
            onClick={handleAddVehicle}
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition flex items-center gap-2"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Add Vehicle
          </button>
        )}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              {editingVehicle ? 'Edit Vehicle' : 'Add New Vehicle'}
            </h2>
            <VehicleForm
              vehicle={editingVehicle}
              onSubmit={handleFormSubmit}
              onCancel={() => {
                setShowForm(false);
                setEditingVehicle(null);
              }}
              loading={formLoading}
            />
          </div>
        </div>
      )}

      <VehicleList
        vehicles={vehicles}
        loading={loading}
        onEdit={isFleetManager() ? handleEditVehicle : undefined}
        onDelete={isFleetManager() ? handleDeleteVehicle : undefined}
        // NO onReserve prop - neither Fleet User nor Fleet Manager can reserve from here
      />
    </div>
  );
};

export default Vehicles;
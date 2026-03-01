import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import {
  getManufacturers,
  getModelsByManufacturer,
  checkAvailability,
} from '../../services/chatbotService';
import toast from 'react-hot-toast';

const ChatBot = () => {
  const { isFleetUser } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState('welcome'); // welcome, manufacturer, model, result
  const [manufacturers, setManufacturers] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedManufacturer, setSelectedManufacturer] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [availabilityResult, setAvailabilityResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Only show chatbot for Fleet Users
  if (!isFleetUser()) {
    return null;
  }

  const handleOpen = async () => {
    setIsOpen(true);
    if (step === 'welcome') {
      await loadManufacturers();
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    // Reset state when closing
    setTimeout(() => {
      setStep('welcome');
      setSelectedManufacturer('');
      setSelectedModel('');
      setAvailabilityResult(null);
      setModels([]);
    }, 300);
  };

  const loadManufacturers = async () => {
    setLoading(true);
    setStep('manufacturer');
    const result = await getManufacturers();
    if (result.success) {
      setManufacturers(result.data.manufacturers);
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };

  const handleManufacturerSelect = async (manufacturer) => {
    setSelectedManufacturer(manufacturer);
    setLoading(true);
    setStep('model');
    
    const result = await getModelsByManufacturer(manufacturer);
    if (result.success) {
      setModels(result.data.models);
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };

  const handleModelSelect = async (model) => {
    setSelectedModel(model);
    setLoading(true);
    setStep('result');
    
    const result = await checkAvailability(selectedManufacturer, model);
    if (result.success) {
      setAvailabilityResult(result.data);
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };

  const handleStartOver = () => {
    setStep('welcome');
    setSelectedManufacturer('');
    setSelectedModel('');
    setAvailabilityResult(null);
    setModels([]);
    loadManufacturers();
  };

  return (
    <>
      {/* Chatbot Bubble */}
      {!isOpen && (
        <button
          onClick={handleOpen}
          className="fixed bottom-6 right-6 bg-indigo-600 text-white p-4 rounded-full shadow-lg hover:bg-indigo-700 transition-all hover:scale-110 z-50"
          aria-label="Open chatbot"
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
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </button>
      )}

      {/* Chatbot Dialog */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 bg-white rounded-lg shadow-2xl z-50 flex flex-col max-h-[600px]">
          {/* Header */}
          <div className="bg-indigo-600 text-white p-4 rounded-t-lg flex justify-between items-center">
            <div className="flex items-center gap-2">
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
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
              <h3 className="font-semibold">FleetWise Assistant</h3>
            </div>
            <button
              onClick={handleClose}
              className="text-white hover:text-gray-200 transition"
              aria-label="Close chatbot"
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

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Welcome Step */}
            {step === 'welcome' && (
              <div className="space-y-4">
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  <p className="text-gray-800">
                    👋 Hi! I can help you check vehicle availability.
                  </p>
                  <p className="text-gray-600 text-sm mt-2">
                    Click below to get started!
                  </p>
                </div>
                <button
                  onClick={loadManufacturers}
                  className="w-full bg-indigo-600 text-white px-4 py-3 rounded-md hover:bg-indigo-700 transition font-medium"
                >
                  Check Vehicle Availability
                </button>
              </div>
            )}

            {/* Manufacturer Selection */}
            {step === 'manufacturer' && (
              <div className="space-y-4">
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  <p className="text-gray-800 font-medium">
                    Please select a manufacturer:
                  </p>
                </div>
                
                {loading ? (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                    <p className="text-sm text-gray-600 mt-2">Loading manufacturers...</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-2">
                    {manufacturers.map((manufacturer) => (
                      <button
                        key={manufacturer}
                        onClick={() => handleManufacturerSelect(manufacturer)}
                        className="bg-white border-2 border-indigo-200 text-indigo-700 px-4 py-3 rounded-md hover:bg-indigo-50 hover:border-indigo-400 transition font-medium"
                      >
                        {manufacturer}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Model Selection */}
            {step === 'model' && (
              <div className="space-y-4">
                <div className="bg-gray-100 rounded-lg p-3 text-sm">
                  <span className="text-gray-600">Selected:</span>
                  <span className="font-medium text-gray-800 ml-2">{selectedManufacturer}</span>
                </div>

                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  <p className="text-gray-800 font-medium">
                    Select a model:
                  </p>
                </div>

                {loading ? (
                  <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                    <p className="text-sm text-gray-600 mt-2">Loading models...</p>
                  </div>
                ) : models.length > 0 ? (
                  <div className="space-y-2">
                    {models.map((model) => (
                      <button
                        key={model}
                        onClick={() => handleModelSelect(model)}
                        className="w-full bg-white border-2 border-indigo-200 text-indigo-700 px-4 py-3 rounded-md hover:bg-indigo-50 hover:border-indigo-400 transition font-medium text-left"
                      >
                        {model}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-yellow-800">
                      No models available for {selectedManufacturer}.
                    </p>
                  </div>
                )}

                <button
                  onClick={() => {
                    setStep('manufacturer');
                    setSelectedManufacturer('');
                    setModels([]);
                  }}
                  className="w-full bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300 transition text-sm"
                >
                  ← Back to Manufacturers
                </button>
              </div>
            )}

            {/* Result */}
            {step === 'result' && availabilityResult && (
              <div className="space-y-4">
                <div className="bg-gray-100 rounded-lg p-3 text-sm">
                  <div>
                    <span className="text-gray-600">Vehicle:</span>
                    <span className="font-medium text-gray-800 ml-2">
                      {selectedManufacturer} {selectedModel}
                    </span>
                  </div>
                </div>

                <div
                  className={`border-2 rounded-lg p-4 ${
                    availabilityResult.available
                      ? 'bg-green-50 border-green-300'
                      : 'bg-red-50 border-red-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {availabilityResult.available ? (
                      <svg
                        className="h-6 w-6 text-green-600 flex-shrink-0"
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
                    ) : (
                      <svg
                        className="h-6 w-6 text-red-600 flex-shrink-0"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    )}
                    <div>
                      <p
                        className={`font-semibold ${
                          availabilityResult.available
                            ? 'text-green-800'
                            : 'text-red-800'
                        }`}
                      >
                        {availabilityResult.available ? 'Available!' : 'Not Available'}
                      </p>
                      <p
                        className={`text-sm mt-1 ${
                          availabilityResult.available
                            ? 'text-green-700'
                            : 'text-red-700'
                        }`}
                      >
                        {availabilityResult.message}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-300">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Total</p>
                        <p className="font-semibold text-gray-800">
                          {availabilityResult.total_count}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-600">Available</p>
                        <p className="font-semibold text-gray-800">
                          {availabilityResult.available_count}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {availabilityResult.available && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-blue-800 text-sm">
                      💡 <strong>Next step:</strong> Contact a Fleet Manager to reserve this
                      vehicle.
                    </p>
                  </div>
                )}

                <button
                  onClick={handleStartOver}
                  className="w-full bg-indigo-600 text-white px-4 py-3 rounded-md hover:bg-indigo-700 transition font-medium"
                >
                  Check Another Vehicle
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default ChatBot;
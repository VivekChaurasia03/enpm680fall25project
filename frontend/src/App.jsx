import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContextProvider';
import ProtectedRoute from './components/common/ProtectedRoute';
import Layout from './components/common/Layout';
import ChatBot from './components/chatbot/ChatBot'; // ADD THIS LINE

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Vehicles from './pages/Vehicles';
import Reservations from './pages/Reservations';
import Users from './pages/Users';

import { USER_ROLES } from './utils/constants';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Toaster position="top-right" />
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes - All authenticated users */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/vehicles"
            element={
              <ProtectedRoute>
                <Layout>
                  <Vehicles />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/reservations"
            element={
              <ProtectedRoute>
                <Layout>
                  <Reservations />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Fleet Manager Only Route */}
          <Route
            path="/users"
            element={
              <ProtectedRoute allowedRoles={[USER_ROLES.FLEET_MANAGER]}>
                <Layout>
                  <Users />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Catch all - redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        {/* ADD CHATBOT HERE - only shows for Fleet Users */}
        <ChatBot />
      </Router>
    </AuthProvider>
  );
}

export default App;
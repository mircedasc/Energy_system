import { Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// --- IMPORTURILE REALE ---
import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';   // <-- Importăm fișierul real
import ClientDashboard from './pages/ClientDashboard'; // <-- Importăm fișierul real
import PrivateRoute from './components/PrivateRoute';
import DeviceHistory from './pages/DeviceHistory';

function App() {
  return (
    <>
      <ToastContainer position="top-right" autoClose={3000} />

      <Routes>
        <Route path="/login" element={<Login />} />

        {/* RUTA PROTEJATĂ ADMIN */}
        {/* Doar userii cu rol 'Administrator' pot intra aici */}
        <Route
          path="/admin"
          element={
            <PrivateRoute allowedRoles={['Administrator']}>
              <AdminDashboard />
            </PrivateRoute>
          }
        />

        {/* RUTA PROTEJATĂ CLIENT */}
        {/* Clienții intră aici. Adminul poate intra și el de obicei, sau îl poți exclude */}
        <Route
          path="/client"
          element={
            <PrivateRoute allowedRoles={['Client', 'Administrator']}>
              <ClientDashboard />
            </PrivateRoute>
          }
        />

        <Route
          path="/device/:deviceId"
          element={
            <PrivateRoute allowedRoles={['Client', 'Administrator']}>
              <DeviceHistory />
            </PrivateRoute>
          }
        />

        {/* Orice altă rută duce la login */}
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </>
  );
}

export default App;
import { ReactElement } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { getToken } from './api/client';
import Login from './pages/Login';
import Register from './pages/Register';
import HealthAssessment from './pages/HealthAssessment';
import Dashboard from './pages/Dashboard';
import Recommendations from './pages/Recommendations';
import Progress from './pages/Progress';

function RequireAuth({ children }: { children: ReactElement }) {
  const token = getToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/health-assessment"
        element={
          <RequireAuth>
            <HealthAssessment />
          </RequireAuth>
        }
      />
      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/recommendations"
        element={
          <RequireAuth>
            <Recommendations />
          </RequireAuth>
        }
      />
      <Route
        path="/progress"
        element={
          <RequireAuth>
            <Progress />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

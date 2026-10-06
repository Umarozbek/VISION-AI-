import { useSelector } from 'react-redux';
import { Navigate, Route, Routes } from 'react-router-dom';
import MainLayout from './components/Layout/MainLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import TrafficFlowPage from './pages/TrafficFlowPage';
import HeatmapPage from './pages/HeatmapPage';
import StaffPage from './pages/StaffPage';
import CamerasPage from './pages/CamerasPage';
import WebCameraPage from './pages/WebCameraPage';
import StaffCenterPage from './pages/StaffCenterPage';
import InsightsPage from './pages/InsightsPage';
import VideoAnalysisPage from './pages/VideoAnalysisPage';

function PrivateRoute({ children }) {
  const token = useSelector((state) => state.auth.token);
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <PrivateRoute>
            <MainLayout />
          </PrivateRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="traffic" element={<TrafficFlowPage />} />
        <Route path="heatmap" element={<HeatmapPage />} />
        <Route path="staff" element={<StaffPage />} />
        <Route path="staff-center" element={<StaffCenterPage />} />
        <Route path="insights" element={<InsightsPage />} />
        <Route path="cameras" element={<CamerasPage />} />
        <Route path="web-camera" element={<WebCameraPage />} />
        <Route path="video-analysis" element={<VideoAnalysisPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

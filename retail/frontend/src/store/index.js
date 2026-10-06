import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import dashboardReducer from './slices/dashboardSlice';
import camerasReducer from './slices/camerasSlice';
import staffReducer from './slices/staffSlice';
import websocketReducer from './slices/websocketSlice';
import insightsReducer from './slices/insightsSlice';

const store = configureStore({
  reducer: {
    auth: authReducer,
    dashboard: dashboardReducer,
    cameras: camerasReducer,
    staff: staffReducer,
    websocket: websocketReducer,
    insights: insightsReducer,
  },
});

export default store;

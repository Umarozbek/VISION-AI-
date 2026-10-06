import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import client from '../../api/client';

export const fetchOverview = createAsyncThunk('dashboard/overview', async () => {
  const { data } = await client.get('/dashboard/overview');
  return data;
});

export const fetchGender = createAsyncThunk('dashboard/gender', async () => {
  const { data } = await client.get('/dashboard/gender');
  return data;
});

export const fetchAge = createAsyncThunk('dashboard/age', async () => {
  const { data } = await client.get('/dashboard/age');
  return data;
});

export const fetchTrafficFlow = createAsyncThunk('dashboard/traffic', async (hours = 24) => {
  const { data } = await client.get(`/dashboard/traffic-flow?hours=${hours}`);
  return data;
});

export const fetchRealtime = createAsyncThunk('dashboard/realtime', async () => {
  const { data } = await client.get('/dashboard/realtime?limit=30');
  return data;
});

export const fetchHeatmap = createAsyncThunk('dashboard/heatmap', async (cameraId) => {
  const { data } = await client.get(`/dashboard/heatmap/${cameraId}`);
  return data;
});

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState: {
    overview: null,
    gender: null,
    age: null,
    trafficFlow: [],
    realtime: [],
    heatmap: null,
    loading: false,
    error: null,
  },
  reducers: {
    updateOverview(state, action) {
      state.overview = action.payload;
    },
    addRealtimeDetection(state, action) {
      state.realtime = [action.payload, ...state.realtime].slice(0, 50);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchOverview.fulfilled, (state, action) => {
        state.overview = action.payload;
      })
      .addCase(fetchGender.fulfilled, (state, action) => {
        state.gender = action.payload;
      })
      .addCase(fetchAge.fulfilled, (state, action) => {
        state.age = action.payload;
      })
      .addCase(fetchTrafficFlow.fulfilled, (state, action) => {
        state.trafficFlow = action.payload;
      })
      .addCase(fetchRealtime.fulfilled, (state, action) => {
        state.realtime = action.payload;
      })
      .addCase(fetchHeatmap.fulfilled, (state, action) => {
        state.heatmap = action.payload;
      });
  },
});

export const { updateOverview, addRealtimeDetection } = dashboardSlice.actions;
export default dashboardSlice.reducer;

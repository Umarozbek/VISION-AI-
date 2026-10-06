import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import client from '../../api/client';

export const fetchCameras = createAsyncThunk('cameras/fetch', async () => {
  const { data } = await client.get('/cameras/');
  return data;
});

export const createCamera = createAsyncThunk('cameras/create', async (payload) => {
  const { data } = await client.post('/cameras/', payload);
  return data;
});

export const updateCamera = createAsyncThunk('cameras/update', async ({ id, payload }) => {
  const { data } = await client.patch(`/cameras/${id}`, payload);
  return data;
});

export const deleteCamera = createAsyncThunk('cameras/delete', async (id) => {
  await client.delete(`/cameras/${id}`);
  return id;
});

export const testCameraConnection = createAsyncThunk('cameras/test', async (payload) => {
  const { data } = await client.post('/cameras/test-connection', payload);
  return data;
});

const camerasSlice = createSlice({
  name: 'cameras',
  initialState: { items: [], loading: false, testResult: null },
  reducers: {
    clearTestResult(state) {
      state.testResult = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCameras.fulfilled, (state, action) => {
        state.items = action.payload;
      })
      .addCase(createCamera.fulfilled, (state, action) => {
        state.items.push(action.payload);
      })
      .addCase(updateCamera.fulfilled, (state, action) => {
        const idx = state.items.findIndex((c) => c.id === action.payload.id);
        if (idx >= 0) state.items[idx] = action.payload;
      })
      .addCase(deleteCamera.fulfilled, (state, action) => {
        state.items = state.items.filter((c) => c.id !== action.payload);
      })
      .addCase(testCameraConnection.fulfilled, (state, action) => {
        state.testResult = action.payload;
      });
  },
});

export const { clearTestResult } = camerasSlice.actions;
export default camerasSlice.reducer;

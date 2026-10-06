import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import client from '../../api/client';

export const fetchDwellSummary = createAsyncThunk('insights/dwellSummary', async () => {
  const { data } = await client.get('/insights/dwell-summary');
  return data;
});

export const fetchDwellRecords = createAsyncThunk('insights/dwellRecords', async () => {
  const { data } = await client.get('/insights/dwell-time?limit=30');
  return data;
});

export const fetchDirectionFlow = createAsyncThunk('insights/direction', async () => {
  const { data } = await client.get('/insights/direction-flow');
  return data;
});

export const fetchZonePopularity = createAsyncThunk('insights/zones', async () => {
  const { data } = await client.get('/insights/zone-popularity');
  return data;
});

const insightsSlice = createSlice({
  name: 'insights',
  initialState: {
    dwellSummary: [],
    dwellRecords: [],
    directionFlow: [],
    zonePopularity: [],
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDwellSummary.fulfilled, (state, action) => {
        state.dwellSummary = action.payload;
      })
      .addCase(fetchDwellRecords.fulfilled, (state, action) => {
        state.dwellRecords = action.payload;
      })
      .addCase(fetchDirectionFlow.fulfilled, (state, action) => {
        state.directionFlow = action.payload;
      })
      .addCase(fetchZonePopularity.fulfilled, (state, action) => {
        state.zonePopularity = action.payload;
      });
  },
});

export default insightsSlice.reducer;

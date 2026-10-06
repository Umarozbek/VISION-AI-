import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import client from '../../api/client';
import { API_BASE } from '../../config';

export const fetchStaffMonitoring = createAsyncThunk('staff/monitoring', async () => {
  const { data } = await client.get('/staff/monitoring');
  return data;
});

export const fetchStaffActivities = createAsyncThunk('staff/activities', async () => {
  const { data } = await client.get('/staff/activities?limit=30');
  return data;
});

export const toggleStaffDuty = createAsyncThunk('staff/toggle', async (staffId) => {
  const { data } = await client.patch(`/staff/members/${staffId}/duty`);
  return data;
});

// ── Staff Center ─────────────────────────────────────────────────────────────

export const fetchZones = createAsyncThunk('staff/zones', async () => {
  const { data } = await client.get('/staff/zones');
  return data.zones;
});

export const fetchStaffCenter = createAsyncThunk('staff/center/fetch', async () => {
  const { data } = await client.get('/staff/center');
  return data;
});

export const createStaffCenter = createAsyncThunk('staff/center/create', async (payload) => {
  const { data } = await client.post('/staff/center', payload);
  return data;
});

export const updateStaffCenter = createAsyncThunk('staff/center/update', async ({ id, payload }) => {
  const { data } = await client.patch(`/staff/center/${id}`, payload);
  return data;
});

export const deleteStaffCenter = createAsyncThunk('staff/center/delete', async (id) => {
  await client.delete(`/staff/center/${id}`);
  return id;
});

export const uploadStaffPhoto = createAsyncThunk('staff/center/photo', async ({ id, file }, { rejectWithValue }) => {
  const form = new FormData();
  form.append('file', file);
  // axios client'ning default 'Content-Type: application/json' headeri multipart
  // boundary'ni buzib qo'yishi mumkin — shuning uchun bu yerda fetch ishlatamiz,
  // brauzer FormData uchun to'g'ri boundary'ni o'zi qo'shadi.
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}/staff/center/${id}/photos`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    return rejectWithValue(body?.detail || `Rasm yuklashda xato: ${res.status}`);
  }
  return res.json();
});

export const deleteStaffPhoto = createAsyncThunk('staff/center/photo/delete', async ({ id, photoId }) => {
  const { data } = await client.delete(`/staff/center/${id}/photos/${photoId}`);
  return data;
});

const staffSlice = createSlice({
  name: 'staff',
  initialState: {
    monitoring: null,
    activities: [],
    zones: [],
    center: [],
    loading: false,
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStaffMonitoring.fulfilled, (state, action) => {
        state.monitoring = action.payload;
      })
      .addCase(fetchStaffActivities.fulfilled, (state, action) => {
        state.activities = action.payload;
      })
      .addCase(toggleStaffDuty.fulfilled, (state, action) => {
        if (state.monitoring?.members) {
          const member = state.monitoring.members.find((m) => m.id === action.payload.id);
          if (member) member.is_on_duty = action.payload.is_on_duty;
          state.monitoring.on_duty = state.monitoring.members.filter((m) => m.is_on_duty).length;
          state.monitoring.off_duty = state.monitoring.members.filter((m) => !m.is_on_duty).length;
        }
      })
      .addCase(fetchZones.fulfilled, (state, action) => {
        state.zones = action.payload;
      })
      .addCase(fetchStaffCenter.fulfilled, (state, action) => {
        state.center = action.payload;
      })
      .addCase(createStaffCenter.fulfilled, (state, action) => {
        state.center.push(action.payload);
      })
      .addCase(updateStaffCenter.fulfilled, (state, action) => {
        const idx = state.center.findIndex((m) => m.id === action.payload.id);
        if (idx >= 0) state.center[idx] = action.payload;
      })
      .addCase(deleteStaffCenter.fulfilled, (state, action) => {
        state.center = state.center.filter((m) => m.id !== action.payload);
      })
      .addCase(uploadStaffPhoto.fulfilled, (state, action) => {
        const idx = state.center.findIndex((m) => m.id === action.payload.id);
        if (idx >= 0) state.center[idx] = action.payload;
      })
      .addCase(deleteStaffPhoto.fulfilled, (state, action) => {
        const idx = state.center.findIndex((m) => m.id === action.payload.id);
        if (idx >= 0) state.center[idx] = action.payload;
      });
  },
});

export default staffSlice.reducer;

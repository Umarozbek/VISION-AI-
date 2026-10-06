import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import client from '../../api/client';

export const login = createAsyncThunk(
  'auth/login',
  async ({ username, password }, { rejectWithValue }) => {
    try {
      const { data } = await client.post('/auth/login', { username, password });
      localStorage.setItem('token', data.access_token);
      localStorage.setItem(
        'user',
        JSON.stringify({ username: data.username, role: data.role })
      );
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Login failed');
    }
  }
);

export const fetchMe = createAsyncThunk('auth/fetchMe', async (_, { rejectWithValue }) => {
  try {
    const { data } = await client.get('/auth/me');
    return data;
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail);
  }
});

const savedUser = localStorage.getItem('user');

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    token: localStorage.getItem('token'),
    user: savedUser ? JSON.parse(savedUser) : null,
    loading: false,
    error: null,
  },
  reducers: {
    logout(state) {
      state.token = null;
      state.user = null;
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.token = action.payload.access_token;
        state.user = {
          username: action.payload.username,
          role: action.payload.role,
        };
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(fetchMe.fulfilled, (state, action) => {
        state.user = action.payload;
      });
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;

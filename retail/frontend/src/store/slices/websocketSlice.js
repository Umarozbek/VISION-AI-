import { createSlice } from '@reduxjs/toolkit';

const websocketSlice = createSlice({
  name: 'websocket',
  initialState: {
    connected: false,
    lastMessage: null,
  },
  reducers: {
    setConnected(state, action) {
      state.connected = action.payload;
    },
    setLastMessage(state, action) {
      state.lastMessage = action.payload;
    },
  },
});

export const { setConnected, setLastMessage } = websocketSlice.actions;
export default websocketSlice.reducer;

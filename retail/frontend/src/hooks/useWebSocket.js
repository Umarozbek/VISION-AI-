import { useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { WS_BASE } from '../config';
import { addRealtimeDetection, updateOverview } from '../store/slices/dashboardSlice';
import { setConnected, setLastMessage } from '../store/slices/websocketSlice';

export default function useWebSocket(token) {
  const dispatch = useDispatch();
  const wsRef = useRef(null);

  useEffect(() => {
    if (!token) return undefined;

    const ws = new WebSocket(`${WS_BASE}/ws/analytics`);
    wsRef.current = ws;

    ws.onopen = () => dispatch(setConnected(true));
    ws.onclose = () => dispatch(setConnected(false));
    ws.onerror = () => dispatch(setConnected(false));

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        dispatch(setLastMessage(message));

        if (message.type === 'overview') {
          dispatch(updateOverview(message.data));
        }
        if (message.type === 'detection') {
          dispatch(addRealtimeDetection(message.data));
        }
      } catch {
        /* ignore malformed messages */
      }
    };

    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping');
    }, 30000);

    return () => {
      clearInterval(ping);
      ws.close();
    };
  }, [token, dispatch]);
}

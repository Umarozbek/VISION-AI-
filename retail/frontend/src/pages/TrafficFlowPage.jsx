import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { Box, Card, CardContent, Typography } from '@mui/material';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { fetchTrafficFlow } from '../store/slices/dashboardSlice';

export default function TrafficFlowPage() {
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const { trafficFlow } = useSelector((state) => state.dashboard);

  useEffect(() => {
    dispatch(fetchTrafficFlow(24));
    const interval = setInterval(() => dispatch(fetchTrafficFlow(24)), 10000);
    return () => clearInterval(interval);
  }, [dispatch]);

  const peakHour = trafficFlow.reduce(
    (max, item) => (item.entered > (max?.entered || 0) ? item : max),
    null
  );

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 1 }}>
        {t('traffic.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('traffic.subtitle')}
        {peakHour && t('traffic.peakHour', { hour: peakHour.hour, count: peakHour.entered })}
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('traffic.hourlyFlowTitle')}
          </Typography>
          <ResponsiveContainer width="100%" height={360}>
            <AreaChart data={trafficFlow}>
              <defs>
                <linearGradient id="enteredGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="exitedGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="hour" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
              <Legend />
              <Area
                type="monotone"
                dataKey="entered"
                name={t('traffic.series.entered')}
                stroke="#10b981"
                fill="url(#enteredGrad)"
              />
              <Area
                type="monotone"
                dataKey="exited"
                name={t('traffic.series.exited')}
                stroke="#f59e0b"
                fill="url(#exitedGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('traffic.insideCountTitle')}
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trafficFlow}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="hour" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
              <Bar dataKey="inside" name={t('traffic.series.inside')} fill="#6366f1" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </Box>
  );
}

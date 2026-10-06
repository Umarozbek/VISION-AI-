import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardContent,
  Grid2 as Grid,
  Typography,
} from '@mui/material';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import GroupsIcon from '@mui/icons-material/Groups';
import VideocamIcon from '@mui/icons-material/Videocam';
import BadgeIcon from '@mui/icons-material/Badge';
import VisibilityIcon from '@mui/icons-material/Visibility';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import StatCard from '../components/StatCard';
import RealtimeTable from '../components/RealtimeTable';
import {
  fetchAge,
  fetchGender,
  fetchOverview,
  fetchRealtime,
  fetchTrafficFlow,
} from '../store/slices/dashboardSlice';

const PIE_COLORS = ['#6366f1', '#22d3ee', '#10b981', '#f59e0b'];
const GENDER_COLORS = { male: '#6366f1', female: '#ec4899', unknown: '#94a3b8' };

export default function DashboardPage() {
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const { overview, gender, age, trafficFlow, realtime } = useSelector(
    (state) => state.dashboard
  );

  useEffect(() => {
    dispatch(fetchOverview());
    dispatch(fetchGender());
    dispatch(fetchAge());
    dispatch(fetchTrafficFlow(24));
    dispatch(fetchRealtime());

    const interval = setInterval(() => {
      dispatch(fetchOverview());
      dispatch(fetchTrafficFlow(24));
    }, 15000);

    return () => clearInterval(interval);
  }, [dispatch]);

  const genderData = gender
    ? Object.entries(gender).map(([name, value]) => ({ name, value }))
    : [];

  const ageData = age
    ? Object.entries(age).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        {t('dashboard.title')}
      </Typography>

      <Grid container spacing={2.5} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
          <StatCard
            title={t('dashboard.entered')}
            value={overview?.entered?.toLocaleString()}
            subtitle={t('dashboard.today')}
            color="success"
            icon={<LoginIcon />}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
          <StatCard
            title={t('dashboard.exited')}
            value={overview?.exited?.toLocaleString()}
            subtitle={t('dashboard.today')}
            color="warning"
            icon={<LogoutIcon />}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
          <StatCard
            title={t('dashboard.inside')}
            value={overview?.inside}
            subtitle={t('dashboard.now')}
            color="info"
            icon={<GroupsIcon />}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
          <StatCard
            title={t('dashboard.cameras')}
            value={overview?.active_cameras}
            subtitle={t('dashboard.active')}
            color="primary"
            icon={<VideocamIcon />}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
          <StatCard
            title={t('dashboard.detections')}
            value={overview?.total_detections?.toLocaleString()}
            subtitle={t('dashboard.today')}
            color="primary"
            icon={<VisibilityIcon />}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
          <StatCard
            title={t('dashboard.staff')}
            value={overview?.staff_on_duty}
            subtitle={t('dashboard.onDuty')}
            color="success"
            icon={<BadgeIcon />}
          />
        </Grid>
      </Grid>

      <Grid container spacing={2.5} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('dashboard.trafficFlow24h')}
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trafficFlow}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="hour" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="entered"
                    name={t('dashboard.series.entered')}
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="exited"
                    name={t('dashboard.series.exited')}
                    stroke="#f59e0b"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="inside"
                    name={t('dashboard.series.inside')}
                    stroke="#6366f1"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('dashboard.genderDistribution')}
              </Typography>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={genderData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                  >
                    {genderData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={GENDER_COLORS[entry.name] || '#94a3b8'}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(v) => [`${v}%`, '']}
                    contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, md: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('dashboard.ageGroups')}
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={ageData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} unit="%" />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }}
                  />
                  <Bar dataKey="value" name={t('dashboard.series.percent')} radius={[6, 6, 0, 0]}>
                    {ageData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 7 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('dashboard.realtimeTracking')}
              </Typography>
              <RealtimeTable detections={realtime} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

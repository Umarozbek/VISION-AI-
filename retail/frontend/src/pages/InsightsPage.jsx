import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardContent,
  Grid2 as Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  fetchDirectionFlow,
  fetchDwellRecords,
  fetchDwellSummary,
  fetchZonePopularity,
} from '../store/slices/insightsSlice';

const COLORS = ['#6366f1', '#22d3ee', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

export default function InsightsPage() {
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const { dwellSummary, dwellRecords, directionFlow, zonePopularity } = useSelector(
    (state) => state.insights
  );

  useEffect(() => {
    dispatch(fetchDwellSummary());
    dispatch(fetchDwellRecords());
    dispatch(fetchDirectionFlow());
    dispatch(fetchZonePopularity());
    const interval = setInterval(() => {
      dispatch(fetchDwellSummary());
      dispatch(fetchDwellRecords());
      dispatch(fetchDirectionFlow());
      dispatch(fetchZonePopularity());
    }, 15000);
    return () => clearInterval(interval);
  }, [dispatch]);

  // Backend "label" maydoni o'zbekcha keladi — displey uchun o'zimiz tarjima qilamiz
  const translatedDirectionFlow = directionFlow.map((row) => ({
    ...row,
    label: t(`insights.directions.${row.direction}`, row.label),
  }));

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {t('insights.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('insights.subtitle')}
      </Typography>

      <Grid container spacing={2.5} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('insights.avgTimeByZone')}
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={dwellSummary}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="zone" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
                  <Bar dataKey="avg_dwell_minutes" name={t('insights.series.minutes')} radius={[6, 6, 0, 0]}>
                    {dwellSummary.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('insights.movementDirections')}
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={translatedDirectionFlow} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis type="number" stroke="#94a3b8" />
                  <YAxis dataKey="label" type="category" stroke="#94a3b8" width={100} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
                  <Bar dataKey="count" name={t('insights.series.movements')} fill="#6366f1" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('insights.popularZones')}
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('insights.table.zone')}</TableCell>
                      <TableCell>{t('insights.table.visits')}</TableCell>
                      <TableCell>{t('insights.table.totalTime')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {zonePopularity.map((row) => (
                      <TableRow key={row.zone}>
                        <TableCell>{row.zone}</TableCell>
                        <TableCell>{row.visits}</TableCell>
                        <TableCell>{row.total_dwell_minutes}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('insights.recentDwellTimes')}
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('insights.table.zone')}</TableCell>
                      <TableCell>{t('insights.table.time')}</TableCell>
                      <TableCell>{t('insights.table.gender')}</TableCell>
                      <TableCell>{t('insights.table.age')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {dwellRecords.map((row) => (
                      <TableRow key={row.id}>
                        <TableCell>{row.zone_label}</TableCell>
                        <TableCell>{row.dwell_seconds}</TableCell>
                        <TableCell>{row.gender || '—'}</TableCell>
                        <TableCell>{row.age_group || '—'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Grid2 as Grid,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import ToggleOnIcon from '@mui/icons-material/ToggleOn';
import ToggleOffIcon from '@mui/icons-material/ToggleOff';
import { format } from 'date-fns';
import StatCard from '../components/StatCard';
import {
  fetchStaffActivities,
  fetchStaffMonitoring,
  toggleStaffDuty,
} from '../store/slices/staffSlice';

export default function StaffPage() {
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const { monitoring, activities } = useSelector((state) => state.staff);
  const activityLabels = {
    patrol: t('staffMonitoring.activities.patrol'),
    assisting_customer: t('staffMonitoring.activities.assisting_customer'),
    at_counter: t('staffMonitoring.activities.at_counter'),
    break: t('staffMonitoring.activities.break'),
    check_in: t('staffMonitoring.activities.check_in'),
  };

  useEffect(() => {
    dispatch(fetchStaffMonitoring());
    dispatch(fetchStaffActivities());
    const interval = setInterval(() => {
      dispatch(fetchStaffMonitoring());
      dispatch(fetchStaffActivities());
    }, 15000);
    return () => clearInterval(interval);
  }, [dispatch]);

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        {t('staffMonitoring.title')}
      </Typography>

      <Grid container spacing={2.5} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard title={t('staffMonitoring.totalStaff')} value={monitoring?.total} color="primary" />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard title={t('staffMonitoring.onDuty')} value={monitoring?.on_duty} color="success" />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <StatCard title={t('staffMonitoring.offDuty')} value={monitoring?.off_duty} color="warning" />
        </Grid>
      </Grid>

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('staffMonitoring.staffStatusTitle')}
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('staffMonitoring.table.name')}</TableCell>
                      <TableCell>{t('staffMonitoring.table.badge')}</TableCell>
                      <TableCell>{t('staffMonitoring.table.department')}</TableCell>
                      <TableCell>{t('staffMonitoring.table.location')}</TableCell>
                      <TableCell>{t('staffMonitoring.table.status')}</TableCell>
                      <TableCell align="right">{t('staffMonitoring.table.action')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {monitoring?.members?.map((member) => (
                      <TableRow key={member.id} hover>
                        <TableCell>{member.name}</TableCell>
                        <TableCell>{member.badge_id}</TableCell>
                        <TableCell>{member.department}</TableCell>
                        <TableCell>{member.last_location || '—'}</TableCell>
                        <TableCell>
                          <Chip
                            label={member.is_on_duty ? t('staffMonitoring.onDuty') : t('staffMonitoring.offDuty')}
                            size="small"
                            color={member.is_on_duty ? 'success' : 'default'}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            color={member.is_on_duty ? 'success' : 'default'}
                            onClick={() => dispatch(toggleStaffDuty(member.id))}
                          >
                            {member.is_on_duty ? <ToggleOnIcon /> : <ToggleOffIcon />}
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 5 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('staffMonitoring.recentActivityTitle')}
              </Typography>
              <TableContainer component={Paper} sx={{ bgcolor: 'transparent' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('staffMonitoring.table.staff')}</TableCell>
                      <TableCell>{t('staffMonitoring.table.activity')}</TableCell>
                      <TableCell>{t('staffMonitoring.table.duration')}</TableCell>
                      <TableCell>{t('staffMonitoring.table.time')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {activities.map((act) => (
                      <TableRow key={act.id}>
                        <TableCell>{act.staff_name}</TableCell>
                        <TableCell>{activityLabels[act.activity] || act.activity}</TableCell>
                        <TableCell>{Math.round(act.duration_seconds / 60)} min</TableCell>
                        <TableCell>{format(new Date(act.timestamp), 'HH:mm')}</TableCell>
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

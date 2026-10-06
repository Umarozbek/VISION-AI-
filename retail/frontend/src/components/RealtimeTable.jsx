import {
  Box,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { format } from 'date-fns';
import { useTranslation } from 'react-i18next';

const eventColors = {
  enter: 'success',
  exit: 'warning',
  track: 'info',
  detect: 'default',
};

export default function RealtimeTable({ detections }) {
  const { t } = useTranslation();

  if (!detections?.length) {
    return (
      <Typography color="text.secondary" align="center" py={4}>
        {t('realtimeTable.empty')}
      </Typography>
    );
  }

  return (
    <TableContainer component={Paper} sx={{ bgcolor: 'background.paper', maxHeight: 420 }}>
      <Table stickyHeader size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('realtimeTable.trackId')}</TableCell>
            <TableCell>{t('realtimeTable.camera')}</TableCell>
            <TableCell>{t('realtimeTable.event')}</TableCell>
            <TableCell>{t('realtimeTable.gender')}</TableCell>
            <TableCell>{t('realtimeTable.age')}</TableCell>
            <TableCell>{t('realtimeTable.zone')}</TableCell>
            <TableCell>{t('realtimeTable.staff')}</TableCell>
            <TableCell>{t('realtimeTable.time')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {detections.map((row, idx) => (
            <TableRow key={`${row.track_id}-${idx}`} hover>
              <TableCell>#{row.track_id}</TableCell>
              <TableCell>{row.camera_name || `Cam ${row.camera_id}`}</TableCell>
              <TableCell>
                <Chip
                  label={row.event_type}
                  size="small"
                  color={eventColors[row.event_type] || 'default'}
                  variant="outlined"
                />
              </TableCell>
              <TableCell>{row.gender || '—'}</TableCell>
              <TableCell>{row.age_group || '—'}</TableCell>
              <TableCell>{row.zone_label || '—'}</TableCell>
              <TableCell>
                <Chip
                  label={row.is_staff ? t('cameras.yes') : t('cameras.no')}
                  size="small"
                  color={row.is_staff ? 'secondary' : 'default'}
                />
              </TableCell>
              <TableCell>
                {row.timestamp
                  ? format(new Date(row.timestamp), 'HH:mm:ss')
                  : '—'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

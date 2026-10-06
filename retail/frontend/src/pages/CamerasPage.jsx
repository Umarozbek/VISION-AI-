import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  Alert, Box, Button, Card, CardContent, Chip, Collapse,
  Dialog, DialogActions, DialogContent, DialogTitle,
  Grid2 as Grid, IconButton, MenuItem, Switch,
  Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import AddIcon        from '@mui/icons-material/Add';
import DeleteIcon     from '@mui/icons-material/Delete';
import VideocamIcon   from '@mui/icons-material/Videocam';
import VideocamOffIcon from '@mui/icons-material/VideocamOff';
import WifiTetheringIcon from '@mui/icons-material/WifiTethering';
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew';
import {
  clearTestResult, createCamera, deleteCamera,
  fetchCameras, testCameraConnection, updateCamera,
} from '../store/slices/camerasSlice';
import CameraStreamView from '../components/CameraStreamView';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const BRAND_PATHS = {
  hikvision: 'Streaming/Channels/101',
  dahua:     'cam/realmonitor?channel=1&subtype=0',
  uniview:   'media/video1',
  custom:    '',
};

const emptyForm = {
  name: '', location: '', ip_address: '',
  port: 554, username: '', password: '',
  stream_path: 'Streaming/Channels/101',
  brand: 'hikvision', is_entrance: false, active: true,
};

const statusColors = {
  processing: 'success', connecting: 'warning',
  error: 'error', pending: 'default', idle: 'default', stopped: 'default',
};

// ── Bitta kamera kartasi ─────────────────────────────────────────────────────
function CameraCard({ cam, token, onDelete, onToggleActive }) {
  const { t } = useTranslation();
  const [showStream, setShowStream] = useState(false);

  return (
    <Card sx={{ opacity: cam.active ? 1 : 0.6 }}>
      <CardContent sx={{ pb: showStream ? 0 : undefined }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <VideocamIcon color="primary" fontSize="small" />
            <Typography variant="h6">{cam.name}</Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <IconButton
              size="small"
              color={cam.active ? 'success' : 'default'}
              onClick={onToggleActive}
              title={cam.active ? t('cameras.turnOff') : t('cameras.turnOn')}
            >
              <PowerSettingsNewIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              color={showStream ? 'primary' : 'default'}
              onClick={() => setShowStream((v) => !v)}
              title={showStream ? t('cameras.close') : t('cameras.watchLive')}
            >
              {showStream ? <VideocamOffIcon fontSize="small" /> : <VideocamIcon fontSize="small" />}
            </IconButton>
            <IconButton size="small" color="error" onClick={onDelete}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>

        <Typography variant="body2" color="text.secondary" gutterBottom>
          {cam.location}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block">
          {cam.ip_address ? `${cam.ip_address}:${cam.port}` : cam.connection_url_preview}
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, mt: 1.5, mb: showStream ? 1.5 : 0, flexWrap: 'wrap' }}>
          <Chip label={cam.active ? t('cameras.active') : t('cameras.inactive')} size="small"
            color={cam.active ? 'success' : 'default'} />
          {cam.is_entrance && (
            <Chip label={t('cameras.entrance')} size="small" color="info" variant="outlined" />
          )}
          <Chip icon={<WifiTetheringIcon />}
            label={cam.processing_status || 'idle'} size="small"
            color={statusColors[cam.processing_status] || 'default'} variant="outlined" />
        </Box>
      </CardContent>

      {/* Collapsible stream panel */}
      <Collapse in={showStream} unmountOnExit>
        <Box sx={{ px: 2, pb: 2 }}>
          <CameraStreamView
            camera={cam}
            apiBase={API_BASE}
            token={token}
            height={280}
          />
        </Box>
      </Collapse>
    </Card>
  );
}

// ── Asosiy sahifa ─────────────────────────────────────────────────────────────
export default function CamerasPage() {
  const dispatch  = useDispatch();
  const { t }     = useTranslation();
  const { items: cameras, testResult } = useSelector((s) => s.cameras);
  // JWT token — authSlice da saqlanadi
  const token     = useSelector((s) => s.auth?.token ?? '');
  const [open,    setOpen]    = useState(false);
  const [form,    setForm]    = useState(emptyForm);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    dispatch(fetchCameras());
    const timer = setInterval(() => dispatch(fetchCameras()), 10000);
    return () => clearInterval(timer);
  }, [dispatch]);

  const handleBrandChange = (brand) =>
    setForm({ ...form, brand, stream_path: BRAND_PATHS[brand] ?? form.stream_path });

  const buildPayload = () => ({
    name: form.name, location: form.location,
    ip_address: form.ip_address, port: Number(form.port) || 554,
    username: form.username || null, password: form.password || null,
    stream_path: form.stream_path || null,
    is_entrance: form.is_entrance, active: form.active,
  });

  const handleTest = async () => {
    setTesting(true);
    dispatch(clearTestResult());
    await dispatch(testCameraConnection(buildPayload()));
    setTesting(false);
  };

  const handleCreate = async () => {
    await dispatch(createCamera(buildPayload()));
    setForm(emptyForm);
    setOpen(false);
    dispatch(clearTestResult());
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h5" gutterBottom>{t('cameras.title')}</Typography>
          <Typography variant="body2" color="text.secondary">
            {t('cameras.hint')}
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpen(true)}>
          {t('cameras.add')}
        </Button>
      </Box>

      {/* Cards */}
      <Grid container spacing={2}>
        {cameras.map((cam) => (
          <Grid key={cam.id} size={{ xs: 12, md: 6, lg: 4 }}>
            <CameraCard
              cam={cam}
              token={token}
              onDelete={() => dispatch(deleteCamera(cam.id))}
              onToggleActive={() => dispatch(updateCamera({ id: cam.id, payload: { active: !cam.active } }))}
            />
          </Grid>
        ))}
      </Grid>

      {cameras.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {t('cameras.empty')}
        </Alert>
      )}

      {/* Summary table */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t('cameras.table.id')}</TableCell>
                  <TableCell>{t('cameras.table.name')}</TableCell>
                  <TableCell>{t('cameras.table.ip')}</TableCell>
                  <TableCell>{t('cameras.table.aiStatus')}</TableCell>
                  <TableCell>{t('cameras.table.entrance')}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {cameras.map((cam) => (
                  <TableRow key={cam.id}>
                    <TableCell>{cam.id}</TableCell>
                    <TableCell>{cam.name}</TableCell>
                    <TableCell>{cam.ip_address || '—'}</TableCell>
                    <TableCell>
                      <Chip label={cam.processing_status} size="small"
                        color={statusColors[cam.processing_status] || 'default'} />
                    </TableCell>
                    <TableCell>{cam.is_entrance ? t('cameras.yes') : t('cameras.no')}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Add dialog */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('cameras.add')}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField label={t('cameras.name')}      value={form.name}       onChange={(e) => setForm({ ...form, name: e.target.value })}       fullWidth />
          <TextField label={t('cameras.location')}  value={form.location}   onChange={(e) => setForm({ ...form, location: e.target.value })}   fullWidth />
          <TextField label={t('cameras.ipAddress')} value={form.ip_address} onChange={(e) => setForm({ ...form, ip_address: e.target.value })} fullWidth placeholder="192.168.1.64" />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField label={t('cameras.port')} type="number" value={form.port}
              onChange={(e) => setForm({ ...form, port: e.target.value })} sx={{ width: 120 }} />
            <TextField select label={t('cameras.brand')} value={form.brand}
              onChange={(e) => handleBrandChange(e.target.value)} fullWidth>
              <MenuItem value="hikvision">Hikvision</MenuItem>
              <MenuItem value="dahua">Dahua</MenuItem>
              <MenuItem value="uniview">Uniview</MenuItem>
              <MenuItem value="custom">{t('cameras.no')}</MenuItem>
            </TextField>
          </Box>
          <TextField label={t('cameras.login')}  value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} fullWidth />
          <TextField label={t('cameras.password')}  type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} fullWidth />
          <TextField label={t('cameras.streamPath')} value={form.stream_path}
            onChange={(e) => setForm({ ...form, stream_path: e.target.value })}
            fullWidth helperText={t('cameras.streamPathHelper')} />
          <Box sx={{ display: 'flex', gap: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Switch checked={form.is_entrance} onChange={(e) => setForm({ ...form, is_entrance: e.target.checked })} />
              <Typography variant="body2">{t('cameras.entrance')}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Switch checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} />
              <Typography variant="body2">{t('cameras.active')}</Typography>
            </Box>
          </Box>
          {testResult && (
            <Alert severity={testResult.success ? 'success' : 'error'}>
              {testResult.message}
              {testResult.width && ` (${testResult.width}x${testResult.height})`}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>{t('cameras.cancel')}</Button>
          <Button onClick={handleTest} disabled={!form.ip_address || testing}>
            {testing ? t('cameras.testing') : t('cameras.testConnection')}
          </Button>
          <Button variant="contained" onClick={handleCreate}
            disabled={!form.name || !form.location || !form.ip_address}>
            {t('cameras.saveAndStart')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
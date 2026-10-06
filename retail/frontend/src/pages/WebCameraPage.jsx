import { useEffect, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  Alert, Box, Button, Card, CardContent, Chip, Collapse,
  Dialog, DialogActions, DialogContent, DialogTitle,
  Grid2 as Grid, IconButton, MenuItem, Switch,
  TextField, Typography,
} from '@mui/material';
import AddIcon         from '@mui/icons-material/Add';
import DeleteIcon      from '@mui/icons-material/Delete';
import VideocamIcon    from '@mui/icons-material/Videocam';
import VideocamOffIcon from '@mui/icons-material/VideocamOff';
import LaptopIcon      from '@mui/icons-material/Laptop';
import GroupsIcon      from '@mui/icons-material/Groups';
import WifiTetheringIcon from '@mui/icons-material/WifiTethering';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew';
import {
  clearTestResult, createCamera, deleteCamera,
  fetchCameras, testCameraConnection, updateCamera,
} from '../store/slices/camerasSlice';
import CameraStreamView from '../components/CameraStreamView';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const emptyForm = {
  name: '', location: '', device_index: 0,
  is_entrance: false, active: true,
};

const statusColors = {
  processing: 'success', connecting: 'warning',
  error: 'error', pending: 'default', idle: 'default', stopped: 'default',
};

// Redetects "hozir" — so'nggi necha soniya ichidagi track eventlarni track_id bo'yicha unikal qiladi
const LIVE_WINDOW_MS = 4000;

function useNow(intervalMs = 1000) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}

// ── Real-time odamlar hisoblagichi — AI ishlayotganini bir qarashda ko'rsatadi ──
function LiveCounterPanel({ cameras, t }) {
  const now = useNow(1000);
  const realtime = useSelector((s) => s.dashboard?.realtime ?? []);

  if (cameras.length === 0) return null;

  return (
    <Card sx={{ mb: 3, bgcolor: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.25)' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <GroupsIcon color="primary" />
          <Typography variant="h6">{t('webCamera.monitor.title')}</Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('webCamera.monitor.subtitle')}
        </Typography>

        <Grid container spacing={2}>
          {cameras.map((cam) => {
            const camTracks = realtime.filter(
              (d) => d.camera_id === cam.id && d.event_type === 'track'
            );
            const recent = camTracks.filter(
              (d) => now - new Date(d.timestamp).getTime() < LIVE_WINDOW_MS
            );
            const uniqueByTrack = new Map();
            recent.forEach((d) => uniqueByTrack.set(d.track_id, d));
            const people = [...uniqueByTrack.values()];
            const customers = people.filter((d) => !d.is_staff).length;
            const staff = people.filter((d) => d.is_staff).length;
            const total = customers + staff;

            const lastFrameMs = cam.last_frame_at ? new Date(cam.last_frame_at).getTime() : null;
            const secondsSince = lastFrameMs !== null ? Math.floor((now - lastFrameMs) / 1000) : null;
            const isAlive = secondsSince !== null && secondsSince < 15;

            const statusKey = cam.processing_status && t(`webCamera.monitor.status.${cam.processing_status}`, { defaultValue: '' })
              ? cam.processing_status
              : 'idle';

            let lastFrameLabel = t('webCamera.monitor.noSignal');
            if (secondsSince !== null) {
              lastFrameLabel = secondsSince < 2
                ? t('webCamera.monitor.justNow')
                : t('webCamera.monitor.secondsAgo', { count: secondsSince });
            }

            return (
              <Grid key={cam.id} size={{ xs: 12, sm: 6, md: 4 }}>
                <Box sx={{
                  p: 2, borderRadius: 2, height: '100%',
                  bgcolor: 'background.paper',
                  border: '1px solid rgba(148,163,184,0.15)',
                }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Typography variant="subtitle2" noWrap sx={{ maxWidth: 160 }}>{cam.name}</Typography>
                    <Chip
                      size="small"
                      icon={<FiberManualRecordIcon sx={{
                        fontSize: 10,
                        filter: isAlive ? 'drop-shadow(0 0 4px currentColor)' : 'none',
                      }} />}
                      label={t(`webCamera.monitor.status.${statusKey}`)}
                      color={statusColors[cam.processing_status] || 'default'}
                      variant="outlined"
                    />
                  </Box>

                  <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, mt: 1.5 }}>
                    <Typography variant="h3" fontWeight={700} color={isAlive ? 'primary.light' : 'text.disabled'}>
                      {total}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('webCamera.monitor.peopleNow')}
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                    <Chip size="small" label={`${t('webCamera.monitor.customers')}: ${customers}`} />
                    <Chip size="small" label={`${t('webCamera.monitor.staff')}: ${staff}`} />
                  </Box>

                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1.5 }}>
                    {t('webCamera.monitor.lastFrame')}: {lastFrameLabel}
                  </Typography>
                </Box>
              </Grid>
            );
          })}
        </Grid>
      </CardContent>
    </Card>
  );
}

// ── Bitta webkamera kartasi ──────────────────────────────────────────────────
function WebcamCard({ cam, token, onDelete, onToggleActive, t }) {
  const [showStream, setShowStream] = useState(false);

  return (
    <Card sx={{ opacity: cam.active ? 1 : 0.6 }}>
      <CardContent sx={{ pb: showStream ? 0 : undefined }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <LaptopIcon color="primary" fontSize="small" />
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
          {cam.connection_url_preview}
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
export default function WebCameraPage() {
  const dispatch  = useDispatch();
  const { t }     = useTranslation();
  const { items: allCameras, testResult } = useSelector((s) => s.cameras);
  const token     = useSelector((s) => s.auth?.token ?? '');
  const cameras   = useMemo(
    () => allCameras.filter((c) => c.camera_type === 'webcam'),
    [allCameras]
  );

  const [open,    setOpen]    = useState(false);
  const [form,    setForm]    = useState(emptyForm);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    dispatch(fetchCameras());
    const timer = setInterval(() => dispatch(fetchCameras()), 5000);
    return () => clearInterval(timer);
  }, [dispatch]);

  const buildPayload = () => ({
    name: form.name, location: form.location,
    camera_type: 'webcam', device_index: Number(form.device_index) || 0,
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
          <Typography variant="h5" gutterBottom>{t('webCamera.title')}</Typography>
          <Typography variant="body2" color="text.secondary">
            {t('webCamera.subtitle')}
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpen(true)}>
          {t('webCamera.add')}
        </Button>
      </Box>

      {/* Real-time odamlar hisoblagichi */}
      <LiveCounterPanel cameras={cameras} t={t} />

      {/* Cards */}
      <Grid container spacing={2}>
        {cameras.map((cam) => (
          <Grid key={cam.id} size={{ xs: 12, md: 6, lg: 4 }}>
            <WebcamCard
              cam={cam}
              token={token}
              t={t}
              onDelete={() => dispatch(deleteCamera(cam.id))}
              onToggleActive={() => dispatch(updateCamera({ id: cam.id, payload: { active: !cam.active } }))}
            />
          </Grid>
        ))}
      </Grid>

      {cameras.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {t('webCamera.empty')}
        </Alert>
      )}

      {/* Add dialog */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('webCamera.addTitle')}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField label={t('webCamera.name')} value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            fullWidth placeholder={t('webCamera.namePlaceholder')} />
          <TextField label={t('webCamera.location')} value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
            fullWidth placeholder={t('webCamera.locationPlaceholder')} />
          <TextField select label={t('webCamera.device')} value={form.device_index}
            onChange={(e) => setForm({ ...form, device_index: e.target.value })} fullWidth
            helperText={t('webCamera.deviceHint')}>
            <MenuItem value={0}>{t('webCamera.device0')}</MenuItem>
            <MenuItem value={1}>{t('webCamera.device1')}</MenuItem>
            <MenuItem value={2}>{t('webCamera.device2')}</MenuItem>
          </TextField>
          <Box sx={{ display: 'flex', gap: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Switch checked={form.is_entrance} onChange={(e) => setForm({ ...form, is_entrance: e.target.checked })} />
              <Typography variant="body2">{t('webCamera.entrance')}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Switch checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} />
              <Typography variant="body2">{t('webCamera.active')}</Typography>
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
          <Button onClick={() => setOpen(false)}>{t('webCamera.cancel')}</Button>
          <Button onClick={handleTest} disabled={testing}>
            {testing ? t('webCamera.testing') : t('webCamera.testConnection')}
          </Button>
          <Button variant="contained" onClick={handleCreate}
            disabled={!form.name || !form.location}>
            {t('webCamera.saveAndStart')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

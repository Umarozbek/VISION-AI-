import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  Alert, Avatar, Box, Button, Card, CardContent, Chip,
  Dialog, DialogActions, DialogContent, DialogTitle,
  Grid2 as Grid, IconButton, MenuItem, TextField, Tooltip, Typography,
} from '@mui/material';
import AddIcon           from '@mui/icons-material/Add';
import DeleteIcon        from '@mui/icons-material/Delete';
import PhotoCameraIcon   from '@mui/icons-material/PhotoCamera';
import BadgeIcon         from '@mui/icons-material/Badge';
import WorkIcon          from '@mui/icons-material/Work';
import CloseIcon         from '@mui/icons-material/Close';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';
import {
  createStaffCenter, deleteStaffCenter, deleteStaffPhoto, fetchStaffCenter,
  fetchZones, uploadStaffPhoto,
} from '../store/slices/staffSlice';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const DEPARTMENTS = ['sales', 'security', 'warehouse', 'cashier', 'management'];
const MAX_PHOTOS = 5;
const RECOMMENDED_PHOTOS = 2;

const emptyForm = { name: '', badge_id: '', department: 'sales', work_position: '' };

function timeAgo(iso, t) {
  if (!iso) return null;
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return t('staffCenter.secondsAgo', { count: seconds });
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return t('staffCenter.minutesAgo', { count: minutes });
  const hours = Math.floor(minutes / 60);
  return t('staffCenter.hoursAgo', { count: hours });
}

function photoUrl(memberId, photoId, token) {
  return `${API_BASE}/staff/center/${memberId}/photos/${photoId}?access_token=${encodeURIComponent(token)}`;
}

function StaffCard({ member, token, t, onDelete, onUploadPhoto, onDeletePhoto, uploadError }) {
  const fileRef = useRef(null);
  const photos = member.photos || [];
  const mainPhotoUrl = photos.length ? photoUrl(member.id, photos[0].id, token) : null;
  const canAddMore = photos.length < MAX_PHOTOS;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar src={mainPhotoUrl || undefined} sx={{ width: 56, height: 56 }}>
              {!mainPhotoUrl && member.name?.[0]?.toUpperCase()}
            </Avatar>
            <Box>
              <Typography variant="subtitle1" fontWeight={600}>{member.name}</Typography>
              <Typography variant="caption" color="text.secondary">
                <BadgeIcon sx={{ fontSize: 12, verticalAlign: 'text-bottom', mr: 0.3 }} />
                {member.badge_id}
              </Typography>
            </Box>
          </Box>
          <IconButton size="small" color="error" onClick={onDelete}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>

        {/* Referens rasmlar to'plami — bir nechta rasm yuz tanishni aniqroq qiladi */}
        <Box sx={{ display: 'flex', gap: 0.75, mt: 1.5, flexWrap: 'wrap', alignItems: 'center' }}>
          {photos.map((photo) => (
            <Box key={photo.id} sx={{ position: 'relative' }}>
              <Avatar
                variant="rounded"
                src={photoUrl(member.id, photo.id, token)}
                sx={{ width: 40, height: 40 }}
              />
              <IconButton
                size="small"
                onClick={() => onDeletePhoto(member.id, photo.id)}
                sx={{
                  position: 'absolute', top: -6, right: -6, p: 0.1,
                  bgcolor: 'error.main', color: '#fff', width: 16, height: 16,
                  '&:hover': { bgcolor: 'error.dark' },
                }}
              >
                <CloseIcon sx={{ fontSize: 10 }} />
              </IconButton>
            </Box>
          ))}
          {canAddMore && (
            <Tooltip title={t('staffCenter.addPhoto')}>
              <IconButton
                size="small"
                onClick={() => fileRef.current?.click()}
                sx={{
                  width: 40, height: 40, borderRadius: 1,
                  border: '1px dashed', borderColor: 'divider',
                }}
              >
                <PhotoCameraIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Tooltip>
          )}
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) onUploadPhoto(member.id, file);
              e.target.value = '';
            }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
          <Chip size="small" label={t(`staffCenter.departments.${member.department}`, member.department)} />
          {member.work_position && (
            <Chip size="small" icon={<WorkIcon sx={{ fontSize: 14 }} />}
              label={member.work_position} variant="outlined" color="info" />
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mt: 1.5 }}>
          <FiberManualRecordIcon sx={{
            fontSize: 10,
            color: member.is_on_duty ? 'success.main' : 'text.disabled',
            filter: member.is_on_duty ? 'drop-shadow(0 0 3px currentColor)' : 'none',
          }} />
          <Typography variant="body2" color={member.is_on_duty ? 'success.main' : 'text.secondary'}>
            {member.is_on_duty ? t('staffCenter.onDuty') : t('staffCenter.offDuty')}
          </Typography>
        </Box>

        {member.checked_in_at && (
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
            {t('staffCenter.checkedInAgo', { time: timeAgo(member.checked_in_at, t) })}
            {member.last_location ? ` · ${member.last_location}` : ''}
          </Typography>
        )}

        {photos.length === 0 && (
          <Alert severity="warning" variant="outlined" sx={{ mt: 1.5, py: 0 }}>
            {t('staffCenter.noPhotoWarning')}
          </Alert>
        )}
        {photos.length > 0 && photos.length < RECOMMENDED_PHOTOS && (
          <Alert severity="info" variant="outlined" sx={{ mt: 1.5, py: 0 }}>
            {t('staffCenter.morePhotosHint', { count: RECOMMENDED_PHOTOS })}
          </Alert>
        )}
        {uploadError && (
          <Alert severity="error" variant="outlined" sx={{ mt: 1.5, py: 0 }}>
            {uploadError}
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

export default function StaffCenterPage() {
  const dispatch = useDispatch();
  const { t }     = useTranslation();
  const token     = useSelector((s) => s.auth?.token ?? '');
  const { center: staff, zones } = useSelector((s) => s.staff);

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [photoErrors, setPhotoErrors] = useState({});

  useEffect(() => {
    dispatch(fetchStaffCenter());
    dispatch(fetchZones());
    const timer = setInterval(() => dispatch(fetchStaffCenter()), 10000);
    return () => clearInterval(timer);
  }, [dispatch]);

  const handleCreate = async () => {
    await dispatch(createStaffCenter({
      name: form.name, badge_id: form.badge_id,
      department: form.department, work_position: form.work_position || null,
    }));
    setForm(emptyForm);
    setOpen(false);
  };

  const handleUploadPhoto = async (id, file) => {
    setPhotoErrors((prev) => ({ ...prev, [id]: null }));
    const result = await dispatch(uploadStaffPhoto({ id, file }));
    if (uploadStaffPhoto.rejected.match(result)) {
      setPhotoErrors((prev) => ({ ...prev, [id]: result.payload || t('staffCenter.uploadFailed') }));
    }
  };

  const handleDeletePhoto = (id, photoId) => {
    dispatch(deleteStaffPhoto({ id, photoId }));
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h5" gutterBottom>{t('staffCenter.title')}</Typography>
          <Typography variant="body2" color="text.secondary">
            {t('staffCenter.subtitle')}
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpen(true)}>
          {t('staffCenter.add')}
        </Button>
      </Box>

      <Grid container spacing={2}>
        {staff.map((member) => (
          <Grid key={member.id} size={{ xs: 12, sm: 6, md: 4 }}>
            <StaffCard
              member={member}
              token={token}
              t={t}
              onDelete={() => dispatch(deleteStaffCenter(member.id))}
              onUploadPhoto={handleUploadPhoto}
              onDeletePhoto={handleDeletePhoto}
              uploadError={photoErrors[member.id]}
            />
          </Grid>
        ))}
      </Grid>

      {staff.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>{t('staffCenter.empty')}</Alert>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('staffCenter.addTitle')}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField label={t('staffCenter.name')} value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} fullWidth autoFocus />
          <TextField label={t('staffCenter.badgeId')} value={form.badge_id}
            onChange={(e) => setForm({ ...form, badge_id: e.target.value })} fullWidth
            placeholder="STF-005" />
          <TextField select label={t('staffCenter.department')} value={form.department}
            onChange={(e) => setForm({ ...form, department: e.target.value })} fullWidth>
            {DEPARTMENTS.map((d) => (
              <MenuItem key={d} value={d}>{t(`staffCenter.departments.${d}`, d)}</MenuItem>
            ))}
          </TextField>
          <TextField select label={t('staffCenter.workPosition')} value={form.work_position}
            onChange={(e) => setForm({ ...form, work_position: e.target.value })} fullWidth
            helperText={t('staffCenter.workPositionHint')}>
            <MenuItem value="">{t('staffCenter.noPosition')}</MenuItem>
            {zones.map((z) => (
              <MenuItem key={z} value={z}>{z}</MenuItem>
            ))}
          </TextField>
          <Alert severity="info" variant="outlined">
            {t('staffCenter.photoHint')}
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>{t('cameras.cancel')}</Button>
          <Button variant="contained" onClick={handleCreate}
            disabled={!form.name || !form.badge_id}>
            {t('staffCenter.save')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

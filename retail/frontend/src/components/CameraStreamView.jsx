/**
 * CameraStreamView — snapshot polling usuli bilan video ko'rsatadi.
 * MJPEG o'rniga har 100ms da /cameras/{id}/snapshot dan JPEG olib blob URL qiladi.
 * Bu ERR_INCOMPLETE_CHUNKED_ENCODING muammosini hal qiladi.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  Box, Chip, CircularProgress, IconButton, Tooltip, Typography,
} from '@mui/material';
import FullscreenIcon    from '@mui/icons-material/Fullscreen';
import RefreshIcon       from '@mui/icons-material/Refresh';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';

const STATUS_COLOR = {
  processing: '#10b981', connecting: '#f59e0b',
  error: '#ef4444', stopped: '#64748b', idle: '#64748b', pending: '#64748b',
};

export default function CameraStreamView({ camera, apiBase, token, height = 360 }) {
  const { t } = useTranslation();
  const imgRef    = useRef(null);
  const wrapRef   = useRef(null);
  const timerRef  = useRef(null);
  const blobRef   = useRef(null);   // joriy blob URL — memory leak oldini olish

  const [loaded,  setLoaded]  = useState(false);
  const [error,   setError]   = useState(false);
  const [fps,     setFps]     = useState(0);
  const [active,  setActive]  = useState(true);
  const fpsCount  = useRef({ n: 0, t: Date.now() });

  const realtime = useSelector((s) => s.dashboard?.realtime ?? []);
  // Faqat oxirgi 4 soniyadagi "track" eventlarni track_id bo'yicha unikal qilib sanaymiz —
  // aks holda 50 talik global bufer eski/qayta-qayta kelgan eventlarni ham qo'shib hisoblardi.
  const now = Date.now();
  const camDets = realtime.filter(
    (d) => d.camera_id === camera?.id
      && d.event_type === 'track'
      && now - new Date(d.timestamp).getTime() < 4000
  );
  const uniqueByTrack = new Map();
  camDets.forEach((d) => uniqueByTrack.set(d.track_id, d));
  const people       = [...uniqueByTrack.values()];
  const personCount  = people.filter((d) => !d.is_staff).length;
  const staffCount   = people.filter((d) =>  d.is_staff).length;
  // Ism bilan tanilgan xodimlar — bir kishi bir necha track_id bo'lib qolmasligi
  // uchun staff_id bo'yicha ham unikal qilamiz
  const recognizedStaff = [...new Map(
    people.filter((d) => d.is_staff && d.staff_name).map((d) => [d.staff_id ?? d.staff_name, d])
  ).values()];
  const isLive      = camera?.processing_status === 'processing';

  const fetchFrame = useCallback(async () => {
    if (!camera?.id || !apiBase || !token || !active) return;

    try {
      const res = await fetch(
        `${apiBase}/cameras/${camera.id}/snapshot?access_token=${encodeURIComponent(token)}`,
        { cache: 'no-store' }
      );
      if (!res.ok) { setError(true); setLoaded(false); return; }

      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);

      if (imgRef.current) {
        // Eski blob URL ni ozod qil
        if (blobRef.current) URL.revokeObjectURL(blobRef.current);
        blobRef.current = url;
        imgRef.current.src = url;
        setLoaded(true);
        setError(false);

        // FPS hisoblash
        fpsCount.current.n += 1;
        const now = Date.now();
        if (now - fpsCount.current.t >= 1000) {
          setFps(fpsCount.current.n);
          fpsCount.current = { n: 0, t: now };
        }
      } else {
        URL.revokeObjectURL(url);
      }
    } catch {
      setError(true);
      setLoaded(false);
    }
  }, [camera?.id, apiBase, token, active]);

  // Polling loop — har 100ms
  useEffect(() => {
    if (!active) return;
    fetchFrame();
    timerRef.current = setInterval(fetchFrame, 100);
    return () => {
      clearInterval(timerRef.current);
      if (blobRef.current) URL.revokeObjectURL(blobRef.current);
    };
  }, [fetchFrame, active]);

  const handleRefresh = () => {
    setLoaded(false);
    setError(false);
    setActive(false);
    setTimeout(() => setActive(true), 200);
  };

  const statusColor = STATUS_COLOR[camera?.processing_status] ?? '#64748b';

  return (
    <Box ref={wrapRef} sx={{
      position: 'relative', width: '100%',
      bgcolor: '#0a0a0a', borderRadius: 1, overflow: 'hidden',
    }}>
      {/* Stream image */}
      <img
        ref={imgRef}
        alt={`${camera?.name} stream`}
        style={{
          width: '100%', height, objectFit: 'contain',
          display: loaded ? 'block' : 'none',
        }}
      />

      {/* Yuklanmoqda */}
      {!loaded && !error && (
        <Box sx={{ width: '100%', height, display: 'flex', flexDirection: 'column',
                   alignItems: 'center', justifyContent: 'center', gap: 1.5 }}>
          <CircularProgress size={28} sx={{ color: '#6366f1' }} />
          <Typography variant="caption" color="text.secondary">
            {t('cameras.streamLoading')}
          </Typography>
        </Box>
      )}

      {/* Xato */}
      {error && (
        <Box sx={{ width: '100%', height, display: 'flex', flexDirection: 'column',
                   alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          <Typography variant="body2" color="error">{t('cameras.frameUnavailable')}</Typography>
          <Typography variant="caption" color="text.secondary">
            {t('cameras.streamOffline')}
          </Typography>
        </Box>
      )}

      {/* LIVE badge */}
      <Box sx={{ position: 'absolute', top: 8, left: 8,
                 display: 'flex', alignItems: 'center', gap: 0.75, pointerEvents: 'none' }}>
        <FiberManualRecordIcon sx={{
          fontSize: 10, color: statusColor,
          filter: isLive ? 'drop-shadow(0 0 4px #10b981)' : 'none',
        }} />
        <Typography variant="caption" sx={{
          color: '#fff', fontWeight: 600, fontSize: 11,
          textShadow: '0 1px 4px rgba(0,0,0,0.9)',
        }}>
          {isLive ? 'LIVE' : (camera?.processing_status ?? 'IDLE').toUpperCase()}
        </Typography>
        {loaded && fps > 0 && (
          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.45)', fontSize: 10 }}>
            {fps} fps
          </Typography>
        )}
      </Box>

      {/* Boshqaruv */}
      <Box sx={{ position: 'absolute', top: 4, right: 4,
                 display: 'flex', alignItems: 'center', gap: 0.25 }}>
        <Tooltip title={t('cameras.refresh')}>
          <IconButton size="small" onClick={handleRefresh}
            sx={{ color: 'rgba(255,255,255,0.65)', p: 0.5 }}>
            <RefreshIcon sx={{ fontSize: 16 }} />
          </IconButton>
        </Tooltip>
        <Tooltip title={t('cameras.fullscreen')}>
          <IconButton size="small" onClick={() => wrapRef.current?.requestFullscreen?.()}
            sx={{ color: 'rgba(255,255,255,0.65)', p: 0.5 }}>
            <FullscreenIcon sx={{ fontSize: 16 }} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Odamlar soni */}
      {loaded && (personCount > 0 || staffCount > 0) && (
        <Box sx={{ position: 'absolute', bottom: 8, right: 8,
                   display: 'flex', gap: 0.75, pointerEvents: 'none' }}>
          {personCount > 0 && (
            <Chip label={`👤 ${personCount} mijoz`} size="small"
              sx={{ bgcolor: 'rgba(99,102,241,0.85)', color: '#fff',
                    fontWeight: 600, fontSize: 11, height: 22 }} />
          )}
          {staffCount > 0 && (
            <Chip label={`🟢 ${staffCount} xodim`} size="small"
              sx={{ bgcolor: 'rgba(16,185,129,0.85)', color: '#fff',
                    fontWeight: 600, fontSize: 11, height: 22 }} />
          )}
        </Box>
      )}

      {/* Ism bilan tanilgan xodimlar — kim ekani va ish o'rni */}
      {loaded && recognizedStaff.length > 0 && (
        <Box sx={{ position: 'absolute', bottom: 8, left: 8,
                   display: 'flex', flexDirection: 'column', gap: 0.5, pointerEvents: 'none' }}>
          {recognizedStaff.map((s) => (
            <Chip
              key={s.staff_id ?? s.staff_name}
              label={s.staff_position ? `🪪 ${s.staff_name} · ${s.staff_position}` : `🪪 ${s.staff_name}`}
              size="small"
              sx={{ bgcolor: 'rgba(16,185,129,0.85)', color: '#fff',
                    fontWeight: 600, fontSize: 11, height: 22, alignSelf: 'flex-start' }}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}
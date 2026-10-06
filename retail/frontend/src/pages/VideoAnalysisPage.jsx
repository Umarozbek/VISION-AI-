import { useCallback, useEffect, useRef, useState } from 'react';
import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  Alert, Box, Button, Card, CardContent, Chip,
  CircularProgress, Divider, Grid2 as Grid,
  IconButton, LinearProgress, Paper, Table,
  TableBody, TableCell, TableHead, TableRow,
  Tooltip, Typography,
} from '@mui/material';
import UploadFileIcon    from '@mui/icons-material/UploadFile';
import DeleteIcon        from '@mui/icons-material/Delete';
import DownloadIcon      from '@mui/icons-material/Download';
import PictureAsPdfIcon  from '@mui/icons-material/PictureAsPdf';
import VideocamIcon      from '@mui/icons-material/Videocam';
import CheckCircleIcon   from '@mui/icons-material/CheckCircle';
import ErrorIcon         from '@mui/icons-material/Error';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend,
  Line, LineChart, Pie, PieChart, ResponsiveContainer,
  Tooltip as RTooltip, XAxis, YAxis,
} from 'recharts';
import client from '../api/client';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const PIE_COLORS   = ['#6366f1', '#ec4899', '#94a3b8'];
const AGE_COLORS   = ['#6366f1', '#22d3ee', '#10b981', '#f59e0b'];
const GENDER_LABELS = { male: 'Erkak', female: 'Ayol', unknown: "Noma'lum" };
const DIRECTION_LABELS = {
  north: 'Shimol', south: 'Janub', east: 'Sharq', west: "G'arb",
  northeast: 'Sh-Sharq', northwest: "Sh-G'arb",
  southeast: 'J-Sharq', southwest: "J-G'arb",
};

// ── PDF export (pure browser, no extra lib) ──────────────────────────────────
function exportPDF(job) {
  const r = job.result;
  const lines = [
    `VIDEO TAHLIL HISOBOTI`,
    ``,
    `Fayl: ${job.filename}`,
    `Tahlil sanasi: ${new Date(job.started_at).toLocaleString('uz')}`,
    `Davomiylik: ${r.duration_seconds} son  |  FPS: ${r.fps}  |  Ruxsat: ${r.resolution}`,
    ``,
    `── ASOSIY KO'RSATKICHLAR ──`,
    `Jami noyob odamlar: ${r.total_unique_people}`,
    `Jami kadrlar: ${r.total_frames}`,
    ``,
    `── JINS TAQSIMOTI ──`,
    ...Object.entries(r.gender).map(([k, v]) => `  ${GENDER_LABELS[k] || k}: ${v}%`),
    ``,
    `── YOSH GURUHLARI ──`,
    ...Object.entries(r.age).map(([k, v]) => `  ${k}: ${v}%`),
    ``,
    `── YO'NALISH TAHLILI ──`,
    ...Object.entries(r.directions || {})
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `  ${DIRECTION_LABELS[k] || k}: ${v} marta`),
    ``,
    `── TRAFIK OQIMI (har 5 soniyada) ──`,
    ...(r.traffic_timeline || []).slice(0, 30).map((p) => `  ${p.time}  →  ${p.people} kishi`),
    ``,
    `Hisobot Claude Code tomonidan avtomatik yaratildi.`,
  ];

  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `video_report_${job.job_id}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Drop zone component ───────────────────────────────────────────────────────
function DropZone({ onFile, uploading }) {
  const { t } = useTranslation();
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  }, [onFile]);

  return (
    <Box
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !uploading && inputRef.current?.click()}
      sx={{
        border: '2px dashed',
        borderColor: dragging ? 'primary.main' : 'divider',
        borderRadius: 2,
        p: 6,
        textAlign: 'center',
        cursor: uploading ? 'default' : 'pointer',
        bgcolor: dragging ? 'action.hover' : 'background.paper',
        transition: 'all .2s',
        '&:hover': { borderColor: uploading ? 'divider' : 'primary.main' },
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".mp4,.avi,.mov,.mkv,.wmv"
        hidden
        onChange={(e) => e.target.files[0] && onFile(e.target.files[0])}
      />
      {uploading ? (
        <CircularProgress size={40} />
      ) : (
        <>
          <UploadFileIcon sx={{ fontSize: 56, color: 'primary.main', mb: 1 }} />
          <Typography variant="h6">{t('videoAnalysis.dropzone.title')}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {t('videoAnalysis.dropzone.hint')}
          </Typography>
        </>
      )}
    </Box>
  );
}

// ── Progress card ─────────────────────────────────────────────────────────────
function JobProgress({ job }) {
  const { t } = useTranslation();
  const done   = job.status === 'done';
  const failed = job.status === 'failed';
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          {done   && <CheckCircleIcon color="success" />}
          {failed && <ErrorIcon color="error" />}
          {!done && !failed && <CircularProgress size={18} />}
          <Typography variant="subtitle1" fontWeight={600}>{job.filename}</Typography>
          <Chip
            label={done ? t('videoAnalysis.status.done') : failed ? t('videoAnalysis.status.failed') : `${job.progress}%`}
            size="small"
            color={done ? 'success' : failed ? 'error' : 'primary'}
            sx={{ ml: 'auto' }}
          />
        </Box>
        {!done && !failed && (
          <LinearProgress variant="determinate" value={job.progress} sx={{ borderRadius: 1 }} />
        )}
        {failed && (
          <Alert severity="error" sx={{ mt: 1 }}>{job.error}</Alert>
        )}
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          {t('videoAnalysis.startedAt')}: {new Date(job.started_at).toLocaleTimeString()}
          {job.finished_at && `  ·  ${t('videoAnalysis.finishedAt')}: ${new Date(job.finished_at).toLocaleTimeString()}`}
        </Typography>
      </CardContent>
    </Card>
  );
}

// ── Results panel ─────────────────────────────────────────────────────────────
function ResultPanel({ job, token, onDelete }) {
  const { t } = useTranslation();
  const r = job.result;

  const genderLabels = {
    male: t('videoAnalysis.genders.male'),
    female: t('videoAnalysis.genders.female'),
    unknown: t('videoAnalysis.genders.unknown'),
  };
  const directionLabels = {
    north: t('videoAnalysis.directions.north'), south: t('videoAnalysis.directions.south'),
    east: t('videoAnalysis.directions.east'), west: t('videoAnalysis.directions.west'),
    northeast: t('videoAnalysis.directions.northeast'), northwest: t('videoAnalysis.directions.northwest'),
    southeast: t('videoAnalysis.directions.southeast'), southwest: t('videoAnalysis.directions.southwest'),
  };

  const genderData = Object.entries(r.gender).map(([name, value]) => ({
    name: genderLabels[name] || name, value,
  }));
  const ageData = Object.entries(r.age).map(([name, value]) => ({ name, value }));
  const dirData = Object.entries(r.directions || {})
    .sort((a, b) => b[1] - a[1]).slice(0, 6)
    .map(([name, value]) => ({ name: directionLabels[name] || name, value }));

  return (
    <Box>
      {/* header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, flexWrap: 'wrap' }}>
        <CheckCircleIcon color="success" />
        <Typography variant="h6" sx={{ flexGrow: 1 }}>{job.filename} — {t('videoAnalysis.results')}</Typography>
        <Tooltip title={t('videoAnalysis.downloadReport')}>
          <Button
            size="small" variant="outlined" startIcon={<PictureAsPdfIcon />}
            onClick={() => exportPDF(job)}
          >
            {t('videoAnalysis.report')}
          </Button>
        </Tooltip>
        <Tooltip title={t('videoAnalysis.downloadVideo')}>
          <Button
            size="small" variant="outlined" startIcon={<DownloadIcon />}
            component="a"
            href={`${API}/video-analysis/jobs/${job.job_id}/video`}
            target="_blank"
            headers={`Authorization: Bearer ${token}`}
          >
            {t('videoAnalysis.video')}
          </Button>
        </Tooltip>
        <Tooltip title={t('videoAnalysis.deleteResult')}>
          <IconButton size="small" color="error" onClick={onDelete}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      {/* stat cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {[
          { label: t('videoAnalysis.stats.uniquePeople'), value: r.total_unique_people, color: '#6366f1' },
          { label: t('videoAnalysis.stats.duration'),     value: `${r.duration_seconds}s`,  color: '#10b981' },
          { label: t('videoAnalysis.stats.frames'),       value: r.total_frames,        color: '#22d3ee' },
          { label: t('videoAnalysis.stats.fps'),          value: r.fps,                  color: '#f59e0b' },
        ].map((s) => (
          <Grid key={s.label} size={{ xs: 6, sm: 3 }}>
            <Paper sx={{ p: 2, textAlign: 'center', borderTop: `3px solid ${s.color}` }}>
              <Typography variant="h4" fontWeight={700} color={s.color}>{s.value}</Typography>
              <Typography variant="caption" color="text.secondary">{s.label}</Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {/* charts row 1 */}
      <Grid container spacing={2.5} sx={{ mb: 2.5 }}>
        {/* Traffic timeline */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>{t('videoAnalysis.trafficTimeline')}</Typography>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={r.traffic_timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} interval="preserveStartEnd" />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <RTooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
                  <Line type="monotone" dataKey="people" name={t('videoAnalysis.series.people')} stroke="#6366f1"
                    strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Gender pie */}
        <Grid size={{ xs: 12, sm: 6, md: 5 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>{t('videoAnalysis.genderDistribution')}</Typography>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={genderData} dataKey="value" nameKey="name"
                    cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3}>
                    {genderData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <RTooltip formatter={(v) => [`${v}%`, '']}
                    contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* charts row 2 */}
      <Grid container spacing={2.5}>
        {/* Age bar */}
        <Grid size={{ xs: 12, sm: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>{t('videoAnalysis.ageGroups')}</Typography>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={ageData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} unit="%" />
                  <RTooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
                  <Bar dataKey="value" name={t('videoAnalysis.series.percent')} radius={[6, 6, 0, 0]}>
                    {ageData.map((_, i) => <Cell key={i} fill={AGE_COLORS[i % AGE_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Direction bar */}
        <Grid size={{ xs: 12, sm: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>{t('videoAnalysis.movementDirections')}</Typography>
              {dirData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={dirData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                    <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={11} width={60} />
                    <RTooltip contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }} />
                    <Bar dataKey="value" name={t('videoAnalysis.series.count')} fill="#22d3ee" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Typography color="text.secondary" variant="body2" sx={{ mt: 2 }}>
                  {t('videoAnalysis.noDirectionData')}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* heatmap grid */}
      {r.heatmap && r.heatmap.length > 0 && (
        <Card sx={{ mt: 2.5 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>{t('videoAnalysis.heatmapTitle')}</Typography>
            <Box sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(20, 1fr)',
              gap: '2px',
              maxWidth: 400,
            }}>
              {Array.from({ length: 20 }, (_, gy) =>
                Array.from({ length: 20 }, (_, gx) => {
                  const point = r.heatmap.find((p) => p.x === gx && p.y === gy);
                  const intensity = point?.intensity || 0;
                  return (
                    <Box
                      key={`${gx}-${gy}`}
                      title={`x:${gx} y:${gy} — ${(intensity * 100).toFixed(0)}%`}
                      sx={{
                        width: '100%',
                        paddingBottom: '100%',
                        borderRadius: '2px',
                        bgcolor: intensity > 0
                          ? `rgba(99,102,241,${Math.min(intensity + 0.1, 1)})`
                          : 'rgba(255,255,255,0.04)',
                      }}
                    />
                  );
                })
              )}
            </Box>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              {t('videoAnalysis.heatmapHint')}
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function VideoAnalysisPage() {
  const { t } = useTranslation();
  const token     = useSelector((s) => s.auth?.token ?? '');
  const userRole  = useSelector((s) => s.auth?.user?.role ?? '');
  const [jobs,    setJobs]    = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadErr, setUploadErr] = useState(null);
  const [selected, setSelected] = useState(null);   // job_id to show results

  const fetchJobs = useCallback(async () => {
    try {
      const { data } = await client.get('/video-analysis/jobs');
      setJobs(data);
    } catch (_) {}
  }, []);

  useEffect(() => {
    fetchJobs();
    const t = setInterval(fetchJobs, 3000);
    return () => clearInterval(t);
  }, [fetchJobs]);

  // auto-select the latest done job if nothing selected
  useEffect(() => {
    if (!selected) {
      const done = jobs.find((j) => j.status === 'done');
      if (done) setSelected(done.job_id);
    }
  }, [jobs, selected]);

  const handleFile = async (file) => {
    setUploadErr(null);
    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const { data } = await client.post('/video-analysis/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSelected(data.job_id);
      await fetchJobs();
    } catch (e) {
      setUploadErr(e?.response?.data?.detail || t('videoAnalysis.uploadError'));
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (jobId) => {
    try {
      await client.delete(`/video-analysis/jobs/${jobId}`);
      if (selected === jobId) setSelected(null);
      await fetchJobs();
    } catch (_) {}
  };

  if (userRole && userRole !== 'admin') {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error">{t('videoAnalysis.adminOnly')}</Alert>
      </Box>
    );
  }

  const activeJob   = jobs.find((j) => j.job_id === selected);
  const processingJobs = jobs.filter((j) => j.status === 'processing');

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <VideocamIcon color="primary" />
        <Typography variant="h5">{t('videoAnalysis.title')}</Typography>
        <Chip label="Admin" size="small" color="warning" sx={{ ml: 1 }} />
      </Box>

      <Grid container spacing={3}>
        {/* Left column: upload + job list */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <DropZone onFile={handleFile} uploading={uploading} />

            {uploadErr && <Alert severity="error" onClose={() => setUploadErr(null)}>{uploadErr}</Alert>}

            {processingJobs.length > 0 && (
              <Alert severity="info" icon={<CircularProgress size={16} />}>
                {t('videoAnalysis.processingCount', { count: processingJobs.length })}
              </Alert>
            )}

            {jobs.length > 0 && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  {t('videoAnalysis.historyTitle')}
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  {jobs.map((job) => (
                    <Box
                      key={job.job_id}
                      onClick={() => job.status === 'done' && setSelected(job.job_id)}
                      sx={{
                        cursor: job.status === 'done' ? 'pointer' : 'default',
                        outline: selected === job.job_id ? '2px solid' : 'none',
                        outlineColor: 'primary.main',
                        borderRadius: 1,
                      }}
                    >
                      <JobProgress job={job} />
                    </Box>
                  ))}
                </Box>
              </Box>
            )}
          </Box>
        </Grid>

        {/* Right column: results */}
        <Grid size={{ xs: 12, md: 8 }}>
          {activeJob?.status === 'done' ? (
            <ResultPanel
              job={activeJob}
              token={token}
              onDelete={() => handleDelete(activeJob.job_id)}
            />
          ) : (
            <Box sx={{
              height: 400, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
              border: '1px dashed', borderColor: 'divider', borderRadius: 2,
              color: 'text.secondary',
            }}>
              <VideocamIcon sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
              <Typography variant="h6" sx={{ opacity: 0.5 }}>
                {jobs.some((j) => j.status === 'processing')
                  ? t('videoAnalysis.placeholder.processing')
                  : t('videoAnalysis.placeholder.idle')}
              </Typography>
              {jobs.some((j) => j.status === 'processing') && (
                <CircularProgress sx={{ mt: 2 }} />
              )}
            </Box>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}

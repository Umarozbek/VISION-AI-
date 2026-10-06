import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from '@mui/material';
import HeatmapGrid from '../components/HeatmapGrid';
import { fetchCameras } from '../store/slices/camerasSlice';
import { fetchHeatmap } from '../store/slices/dashboardSlice';

export default function HeatmapPage() {
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const { items: cameras } = useSelector((state) => state.cameras);
  const { heatmap } = useSelector((state) => state.dashboard);
  const [selectedCamera, setSelectedCamera] = useState('');

  useEffect(() => {
    dispatch(fetchCameras());
  }, [dispatch]);

  useEffect(() => {
    if (cameras.length && !selectedCamera) {
      setSelectedCamera(cameras[0].id);
    }
  }, [cameras, selectedCamera]);

  useEffect(() => {
    if (selectedCamera) {
      dispatch(fetchHeatmap(selectedCamera));
      const interval = setInterval(
        () => dispatch(fetchHeatmap(selectedCamera)),
        20000
      );
      return () => clearInterval(interval);
    }
    return undefined;
  }, [selectedCamera, dispatch]);

  const camera = cameras.find((c) => c.id === selectedCamera);

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 1 }}>
        {t('heatmap.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('heatmap.subtitle')}
      </Typography>

      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, gap: 2 }}>
            <Typography variant="h6">
              {camera ? `${camera.name} — ${camera.location}` : t('heatmap.selectCamera')}
            </Typography>
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel>{t('heatmap.cameraLabel')}</InputLabel>
              <Select
                value={selectedCamera}
                label={t('heatmap.cameraLabel')}
                onChange={(e) => setSelectedCamera(e.target.value)}
              >
                {cameras.map((cam) => (
                  <MenuItem key={cam.id} value={cam.id}>
                    {cam.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
          <HeatmapGrid data={heatmap} gridSize={heatmap?.grid_size || 20} />
        </CardContent>
      </Card>
    </Box>
  );
}

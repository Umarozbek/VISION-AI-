import { Box, Tooltip, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

function intensityColor(intensity, max) {
  const ratio = max > 0 ? intensity / max : 0;
  if (ratio > 0.75) return '#ef4444';
  if (ratio > 0.5) return '#f59e0b';
  if (ratio > 0.25) return '#22d3ee';
  return '#334155';
}

export default function HeatmapGrid({ data, gridSize = 20 }) {
  const { t } = useTranslation();

  if (!data?.points?.length) {
    return (
      <Typography color="text.secondary" align="center" py={6}>
        {t('heatmap.noData')}
      </Typography>
    );
  }

  const max = data.max_intensity || 1;
  const cellMap = {};
  data.points.forEach((p) => {
    cellMap[`${p.x}-${p.y}`] = p.intensity;
  });

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
        gap: 0.5,
        p: 1,
        bgcolor: '#0b1220',
        borderRadius: 2,
        aspectRatio: '4/3',
      }}
    >
      {Array.from({ length: gridSize * gridSize }).map((_, idx) => {
        const x = idx % gridSize;
        const y = Math.floor(idx / gridSize);
        const intensity = cellMap[`${x}-${y}`] || 0;
        return (
          <Tooltip key={idx} title={`(${x}, ${y}): ${intensity.toFixed(1)}`}>
            <Box
              sx={{
                bgcolor: intensityColor(intensity, max),
                opacity: intensity > 0 ? 0.4 + (intensity / max) * 0.6 : 0.15,
                borderRadius: 0.5,
                minHeight: 12,
                transition: 'all 0.2s',
                '&:hover': { transform: 'scale(1.2)', zIndex: 1 },
              }}
            />
          </Tooltip>
        );
      })}
    </Box>
  );
}

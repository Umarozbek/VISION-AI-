import { Card, CardContent, Stack, Typography, Box } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

const colors = {
  primary: '#6366f1',
  success: '#10b981',
  warning: '#f59e0b',
  info: '#22d3ee',
};

export default function StatCard({ title, value, subtitle, color = 'primary', icon }) {
  const accent = colors[color] || colors.primary;

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
              {value ?? '—'}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              p: 1.2,
              borderRadius: 2,
              bgcolor: `${accent}22`,
              color: accent,
              display: 'flex',
            }}
          >
            {icon || <TrendingUpIcon />}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}

import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { Navigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Chip,
  TextField,
  Typography,
} from '@mui/material';
import StorefrontIcon from '@mui/icons-material/Storefront';
import { login } from '../store/slices/authSlice';

const LANGUAGES = [
  { code: 'uz', flag: '🇺🇿' },
  { code: 'en', flag: '🇬🇧' },
  { code: 'ko', flag: '🇰🇷' },
];

export default function LoginPage() {
  const dispatch = useDispatch();
  const { t, i18n } = useTranslation();
  const { token, loading, error } = useSelector((state) => state.auth);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');

  if (token) return <Navigate to="/" replace />;

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(login({ username, password }));
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        p: 2,
      }}
    >
      <Card sx={{ maxWidth: 420, width: '100%' }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mb: 2 }}>
            {LANGUAGES.map((lang) => (
              <Chip
                key={lang.code}
                size="small"
                label={`${lang.flag} ${lang.code.toUpperCase()}`}
                variant={i18n.language === lang.code ? 'filled' : 'outlined'}
                color={i18n.language === lang.code ? 'primary' : 'default'}
                onClick={() => i18n.changeLanguage(lang.code)}
                sx={{ cursor: 'pointer' }}
              />
            ))}
          </Box>

          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <StorefrontIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="h5" fontWeight={700}>
              {t('app.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('app.tagline')}
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {typeof error === 'string' ? error : t('login.error')}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label={t('login.username')}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              fullWidth
              margin="normal"
              autoFocus
            />
            <TextField
              label={t('login.password')}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fullWidth
              margin="normal"
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              size="large"
              disabled={loading}
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : t('login.submit')}
            </Button>
          </Box>

          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
            {t('login.demo')}
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

import { useState } from 'react';
import {
  AppBar,
  Avatar,
  Box,
  Chip,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  ListItemIcon as MenuItemIcon,
  Toolbar,
  Typography,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import TimelineIcon from '@mui/icons-material/Timeline';
import GridOnIcon from '@mui/icons-material/GridOn';
import PeopleIcon from '@mui/icons-material/People';
import BadgeIcon from '@mui/icons-material/Badge';
import InsightsIcon from '@mui/icons-material/Insights';
import VideocamIcon from '@mui/icons-material/Videocam';
import LaptopIcon from '@mui/icons-material/Laptop';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import LogoutIcon from '@mui/icons-material/Logout';
import LanguageIcon from '@mui/icons-material/Language';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';
import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { logout } from '../../store/slices/authSlice';
import useWebSocket from '../../hooks/useWebSocket';

const DRAWER_WIDTH = 260;

const LANGUAGES = [
  { code: 'uz', flag: '🇺🇿', label: "O'zbekcha" },
  { code: 'en', flag: '🇬🇧', label: 'English' },
  { code: 'ko', flag: '🇰🇷', label: '한국어' },
];

function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [anchorEl, setAnchorEl] = useState(null);
  const current = LANGUAGES.find((l) => l.code === i18n.language) || LANGUAGES[0];

  return (
    <>
      <Chip
        size="small"
        icon={<LanguageIcon sx={{ fontSize: 16 }} />}
        label={`${current.flag} ${current.code.toUpperCase()}`}
        variant="outlined"
        onClick={(e) => setAnchorEl(e.currentTarget)}
        sx={{ mr: 2, cursor: 'pointer' }}
      />
      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={() => setAnchorEl(null)}>
        {LANGUAGES.map((lang) => (
          <MenuItem
            key={lang.code}
            selected={lang.code === i18n.language}
            onClick={() => {
              i18n.changeLanguage(lang.code);
              setAnchorEl(null);
            }}
          >
            <MenuItemIcon sx={{ minWidth: 32, fontSize: 18 }}>{lang.flag}</MenuItemIcon>
            {lang.label}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}

export default function MainLayout() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user, token } = useSelector((state) => state.auth);
  const connected = useSelector((state) => state.websocket.connected);

  useWebSocket(token);

  const navItems = [
    { to: '/', label: t('nav.dashboard'), icon: <DashboardIcon /> },
    { to: '/traffic', label: t('nav.traffic'), icon: <TimelineIcon /> },
    { to: '/heatmap', label: t('nav.heatmap'), icon: <GridOnIcon /> },
    { to: '/staff', label: t('nav.staff'), icon: <PeopleIcon /> },
    { to: '/staff-center', label: t('nav.staffCenter'), icon: <BadgeIcon /> },
    { to: '/insights', label: t('nav.insights'), icon: <InsightsIcon /> },
    { to: '/cameras', label: t('nav.cameras'), icon: <VideocamIcon /> },
    { to: '/web-camera', label: t('nav.webCamera'), icon: <LaptopIcon /> },
    { to: '/video-analysis', label: t('nav.videoAnalysis'), icon: <VideoLibraryIcon />, adminOnly: true },
  ];

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            bgcolor: '#0b1220',
            borderRight: '1px solid rgba(148,163,184,0.12)',
          },
        }}
      >
        <Toolbar sx={{ px: 2.5 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, color: 'primary.light' }}>
            {t('app.title')}
          </Typography>
        </Toolbar>
        <List sx={{ px: 1.5 }}>
          {navItems.filter((item) => !item.adminOnly || user?.role === 'admin').map((item) => (
            <ListItemButton
              key={item.to}
              component={NavLink}
              to={item.to}
              end={item.to === '/'}
              sx={{
                mb: 0.5,
                borderRadius: 2,
                '&.active': {
                  bgcolor: 'rgba(99,102,241,0.18)',
                  color: 'primary.light',
                  '& .MuiListItemIcon-root': { color: 'primary.light' },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>

      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <AppBar
          position="sticky"
          elevation={0}
          sx={{
            bgcolor: 'background.default',
            borderBottom: '1px solid rgba(148,163,184,0.12)',
          }}
        >
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600 }}>
              {t('app.platformTitle')}
            </Typography>
            <LanguageSwitcher />
            <Chip
              size="small"
              icon={
                <FiberManualRecordIcon
                  sx={{ fontSize: 12, color: connected ? 'success.main' : 'error.main' }}
                />
              }
              label={connected ? t('topbar.live') : t('topbar.offline')}
              variant="outlined"
              sx={{ mr: 2 }}
            />
            <Avatar sx={{ width: 32, height: 32, mr: 1, bgcolor: 'primary.main', fontSize: 14 }}>
              {user?.username?.[0]?.toUpperCase()}
            </Avatar>
            <Typography variant="body2" sx={{ mr: 2 }}>
              {user?.username}
            </Typography>
            <IconButton onClick={handleLogout} color="inherit" size="small" title={t('topbar.logout')}>
              <LogoutIcon />
            </IconButton>
          </Toolbar>
        </AppBar>

        <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}

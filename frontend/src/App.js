import React, { useState, useEffect } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Link
} from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Container,
  Box,
  Typography,
  IconButton,
  Badge,
  Alert,
  CircularProgress,
  Paper
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  SensorDoor as SensorIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Storage as StorageIcon,
  Email as EmailIcon,
  CloudDownload as DownloadIcon
} from '@mui/icons-material';
import axios from 'axios';
import './App.css';

// Import Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AlertsPage from './pages/Alerts';
import CasesPage from './pages/Cases';
import SensorsPage from './pages/Sensors';
import ReportsPage from './pages/Reports';
import SystemHealthPage from './pages/SystemHealth';
import IOCPage from './pages/IOCs';
import TimelinePage from './pages/Timeline';

// API Base URL
const API_BASE = 'http://localhost:5000/api';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notificationCount, setNotificationCount] = useState(0);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
    
    // Fetch notification count
    if (token) {
      fetchNotificationCount();
    }
  }, []);

  const fetchNotificationCount = async () => {
    try {
      const response = await axios.get(`${API_BASE}/alerts`);
      const highSeverityAlerts = response.data.filter(alert => 
        alert.severity === 'HIGH' && alert.status === 'OPEN'
      );
      setNotificationCount(highSeverityAlerts.length);
    } catch (error) {
      console.error('Error fetching notification count:', error);
    }
  };

  const handleLogin = (userData, token) => {
    setUser(userData);
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <Router>
      <Box sx={{ display: 'flex' }}>
        {/* App Bar */}
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <IconButton
              color="inherit"
              edge="start"
              sx={{ mr: 2 }}
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              🚀 CyberSOC Platform
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <IconButton color="inherit">
                <Badge badgeContent={notificationCount} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
              <Typography variant="body2">
                Welcome, {user.full_name || user.username}
              </Typography>
              <IconButton color="inherit" onClick={handleLogout}>
                <LogoutIcon />
              </IconButton>
            </Box>
          </Toolbar>
        </AppBar>

        {/* Sidebar */}
        <Drawer
          variant="permanent"
          sx={{
            width: 240,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: 240, boxSizing: 'border-box' },
          }}
        >
          <Toolbar />
          <Box sx={{ overflow: 'auto' }}>
            <List>
              <ListItem button component={Link} to="/">
                <ListItemIcon><DashboardIcon /></ListItemIcon>
                <ListItemText primary="Dashboard" />
              </ListItem>
              <ListItem button component={Link} to="/alerts">
                <ListItemIcon>
                  <Badge badgeContent={notificationCount} color="error">
                    <WarningIcon />
                  </Badge>
                </ListItemIcon>
                <ListItemText primary="Alerts" />
              </ListItem>
              <ListItem button component={Link} to="/cases">
                <ListItemIcon><SecurityIcon /></ListItemIcon>
                <ListItemText primary="Cases" />
              </ListItem>
              <ListItem button component={Link} to="/sensors">
                <ListItemIcon><SensorIcon /></ListItemIcon>
                <ListItemText primary="Sensors" />
              </ListItem>
              <ListItem button component={Link} to="/timeline">
                <ListItemIcon><TimelineIcon /></ListItemIcon>
                <ListItemText primary="Timeline" />
              </ListItem>
              <ListItem button component={Link} to="/iocs">
                <ListItemIcon><StorageIcon /></ListItemIcon>
                <ListItemText primary="IOCs" />
              </ListItem>
              <ListItem button component={Link} to="/reports">
                <ListItemIcon><AssessmentIcon /></ListItemIcon>
                <ListItemText primary="Reports" />
              </ListItem>
              <ListItem button component={Link} to="/system-health">
                <ListItemIcon><SettingsIcon /></ListItemIcon>
                <ListItemText primary="System Health" />
              </ListItem>
            </List>
          </Box>
        </Drawer>

        {/* Main Content */}
        <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
          <Toolbar />
          <Container maxWidth="xl">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/cases" element={<CasesPage />} />
              <Route path="/sensors" element={<SensorsPage />} />
              <Route path="/timeline" element={<TimelinePage />} />
              <Route path="/iocs" element={<IOCPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/system-health" element={<SystemHealthPage />} />
            </Routes>
          </Container>
        </Box>
      </Box>
    </Router>
  );
}

export default App;

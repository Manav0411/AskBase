import type { ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  Tabs,
  Tab,
} from '@mui/material'
import { LogoutOutlined } from '@mui/icons-material'
import { useAuthStore } from '../store/authStore'

interface LayoutProps {
  children: ReactNode
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false
  disablePadding?: boolean
}

export default function Layout({ children, maxWidth = 'xl', disablePadding = false }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)

  const currentTab = location.pathname.startsWith('/chat')
    ? '/chat'
    : location.pathname.startsWith('/documents')
    ? '/documents'
    : location.pathname.startsWith('/about')
    ? '/about'
    : false

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: string) => {
    navigate(newValue)
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <AppBar position="static" elevation={0}>
        <Toolbar sx={{ py: 1 }}>
          <Box 
            sx={{ 
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontWeight: 700,
              fontSize: '1.5rem',
              mr: 4,
              letterSpacing: '-0.02em',
            }}
          >
            AskBase
          </Box>

          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            textColor="inherit"
            sx={{ 
              flexGrow: 1,
              '& .MuiTabs-indicator': {
                backgroundColor: '#3b82f6',
                height: 3,
                borderRadius: '3px 3px 0 0',
              },
            }}
          >
            <Tab label="Documents" value="/documents" />
            <Tab label="Chat" value="/chat" />
            <Tab label="About" value="/about" />
          </Tabs>

          {user && (
            <Box sx={{ 
              mr: 3, 
              px: 2, 
              py: 0.5, 
              backgroundColor: '#1a1a1a',
              borderRadius: '8px',
              border: '1px solid #2a2a2a',
            }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {user.email}
              </Typography>
              <Typography 
                component="span" 
                variant="caption" 
                sx={{ 
                  color: '#3b82f6',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  fontSize: '0.7rem',
                  letterSpacing: '0.05em',
                }}
              >
                {user.role}
              </Typography>
            </Box>
          )}

          <Button
            color="inherit"
            startIcon={<LogoutOutlined />}
            onClick={handleLogout}
            sx={{
              color: '#ffffff',
              '&:hover': {
                backgroundColor: '#1a1a1a',
                color: '#3b82f6',
              },
            }}
          >
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      <Box
        component="main"
        sx={{
          flex: 1,
          display: 'flex',
          justifyContent: 'center',
          overflow: 'auto',
          backgroundColor: 'background.default',
          '&::-webkit-scrollbar': {
            width: '10px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#0a0a0a',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#2a2a2a',
            borderRadius: '5px',
            '&:hover': {
              background: '#3a3a3a',
            },
          },
        }}
      >
        <Container
          maxWidth={maxWidth}
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            py: disablePadding ? 0 : 3,
          }}
        >
          {children}
        </Container>
      </Box>
    </Box>
  )
}

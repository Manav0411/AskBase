import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material'
import { login as apiLogin } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { AxiosError } from 'axios'
import type { ApiError } from '../types'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const authLogin = useAuthStore((state) => state.login)

  const loginMutation = useMutation({
    mutationFn: () => apiLogin(email, password),
    onSuccess: (data) => {
      authLogin(data.access_token, email)
      navigate('/documents')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      return
    }
    loginMutation.mutate()
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        width: '100vw',
        backgroundColor: 'background.default',
        padding: 3,
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.15) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%)',
          pointerEvents: 'none',
        },
      }}
    >
      <Card 
        sx={{ 
          width: '100%', 
          maxWidth: 450, 
          backdropFilter: 'blur(10px)',
          backgroundColor: 'rgba(20, 20, 20, 0.8)',
          border: '1px solid #2a2a2a',
          position: 'relative',
          zIndex: 1,
        }}
      >
        <CardContent sx={{ p: 5 }}>
          <Box 
            sx={{ 
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontWeight: 700,
              fontSize: '2.5rem',
              textAlign: 'center',
              mb: 1,
              letterSpacing: '-0.03em',
            }}
          >
            AskBase
          </Box>
          <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
            Sign in to access your documents
          </Typography>

          {loginMutation.isError && (
            <Alert 
              severity="error" 
              sx={{ 
                mb: 2,
                backgroundColor: 'rgba(255, 71, 87, 0.1)',
                border: '1px solid rgba(255, 71, 87, 0.3)',
              }}
            >
              {(() => {
                const error = loginMutation.error as AxiosError<ApiError>
                const detail = error?.response?.data?.detail
                return typeof detail === 'string' ? detail : 'Login failed. Please check your credentials.'
              })()}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              label="Email"
              type="email"
              fullWidth
              margin="normal"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loginMutation.isPending}
              required
              autoFocus
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                  },
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#3b82f6',
                },
              }}
            />

            <TextField
              label="Password"
              type="password"
              fullWidth
              margin="normal"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loginMutation.isPending}
              required
              sx={{
                '& .MuiOutlinedInput-root': {
                  '&.Mui-focused fieldset': {
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                  },
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#3b82f6',
                },
              }}
            />

            <Button
              type="submit"
              variant="contained"
              fullWidth
              size="large"
              sx={{ 
                mt: 3,
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 600,
              }}
              disabled={loginMutation.isPending || !email || !password}
            >
              {loginMutation.isPending ? (
                <CircularProgress size={24} sx={{ color: '#0a0a0a' }} />
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 3, display: 'block', textAlign: 'center' }}>
            Test credentials: admin@example.com / admin123
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}

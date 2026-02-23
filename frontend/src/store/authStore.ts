import { create } from 'zustand'
import { jwtDecode } from 'jwt-decode'
import type { User } from '../types'

interface JwtPayload {
  sub: string
  role: string
  exp: number
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  login: (token: string, email: string) => void
  logout: () => void
  initializeAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  login: (token: string, email: string) => {
    try {
      const decoded = jwtDecode<JwtPayload>(token)
      const user: User = {
        id: parseInt(decoded.sub),
        email: email,
        role: decoded.role as User['role'],
        created_at: new Date().toISOString(),
      }

      localStorage.setItem('auth_token', token)
      localStorage.setItem('user', JSON.stringify(user))

      set({
        token,
        user,
        isAuthenticated: true,
      })
    } catch (error) {
      console.error('Failed to decode token:', error)
      set({ token: null, user: null, isAuthenticated: false })
    }
  },

  logout: () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    set({
      token: null,
      user: null,
      isAuthenticated: false,
    })
  },

  initializeAuth: () => {
    const token = localStorage.getItem('auth_token')
    const userJson = localStorage.getItem('user')

    if (token && userJson) {
      try {
        const user = JSON.parse(userJson) as User
        const decoded = jwtDecode<JwtPayload>(token)
        const isExpired = decoded.exp * 1000 < Date.now()
        
        if (!isExpired) {
          set({
            token,
            user,
            isAuthenticated: true,
          })
        } else {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('user')
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
      }
    }
  },
}))

useAuthStore.getState().initializeAuth()

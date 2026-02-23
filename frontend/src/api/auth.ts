import { apiClient } from './client'
import type { LoginResponse, User } from '../types'

export const login = async (
  email: string,
  password: string
): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/auth/login', {
    email: email,
    password: password,
  })
  return response.data
}

export const getUsers = async (): Promise<User[]> => {
  const response = await apiClient.get<User[]>('/users/')
  return response.data
}

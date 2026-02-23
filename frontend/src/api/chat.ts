import { apiClient } from './client'
import type {
  Conversation,
  PaginatedConversations,
  CreateConversationRequest,
  SendMessageRequest,
  SendMessageResponse,
} from '../types'

export const getConversations = async (
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedConversations> => {
  const skip = (page - 1) * pageSize
  const response = await apiClient.get<PaginatedConversations>('/conversations/', {
    params: { skip, limit: pageSize },
  })
  return response.data
}

export const getConversation = async (
  conversationId: string
): Promise<Conversation> => {
  const response = await apiClient.get<Conversation>(`/conversations/${conversationId}`)
  return response.data
}

export const createConversation = async (
  documentId: string,
  title?: string
): Promise<Conversation> => {
  const data: CreateConversationRequest = {
    document_id: documentId,
    ...(title && { title }),
  }
  const response = await apiClient.post<Conversation>('/conversations/', data)
  return response.data
}

export const sendMessage = async (
  conversationId: string,
  content: string
): Promise<SendMessageResponse> => {
  const data: SendMessageRequest = { message: content }
  const response = await apiClient.post<SendMessageResponse>(
    `/conversations/${conversationId}/messages`,
    data
  )
  return response.data
}

export const deleteConversation = async (conversationId: string): Promise<void> => {
  await apiClient.delete(`/conversations/${conversationId}`)
}

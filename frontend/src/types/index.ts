export interface User {
  id: number
  email: string
  role: 'admin' | 'hr' | 'engineer' | 'intern'
  created_at: string
  is_active?: number
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface Document {
  id: string
  original_filename: string
  stored_filename: string
  file_path: string
  uploaded_by: number
  uploaded_at: string
  status: 'processing' | 'completed' | 'failed'
}

export interface Message {
  id: number
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  confidence_score: number | null
}

export interface Conversation {
  id: string
  user_id: number
  document_id: string
  title: string
  created_at: string
  updated_at: string
  messages?: Message[]
  document?: Document
  suggested_questions?: string[]  // AI-generated suggested questions
}

export interface PaginatedResponse<T> {
  items: T[]
  pagination: {
    total: number
    page: number
    page_size: number
    total_pages: number
  }
}

export type PaginatedDocuments = PaginatedResponse<Document>
export type PaginatedConversations = PaginatedResponse<Conversation>

export interface DocumentPermission {
  id: number
  document_id: string
  permission_type: 'user' | 'role'
  granted_to: string
  granted_at: string
}

export interface ShareDocumentRequest {
  permission_type: 'user' | 'role'
  granted_to: string
}

export interface UploadDocumentRequest {
  file: File
  allowed_roles?: string[]
  allowed_user_ids?: number[]
}

export interface CreateConversationRequest {
  document_id: string
  title?: string
}

export interface SendMessageRequest {
  message: string
}

export interface SendMessageResponse {
  conversation_id: string
  message: Message
  assistant_reply: Message
}

export interface ApiError {
  detail: string | Record<string, any>
}

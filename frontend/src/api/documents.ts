import { apiClient } from './client'
import type {
  Document,
  PaginatedDocuments,
  ShareDocumentRequest,
  DocumentPermission,
} from '../types'

export const getAccessibleDocuments = async (
  page: number = 1,
  pageSize: number = 10
): Promise<PaginatedDocuments> => {
  const skip = (page - 1) * pageSize
  const response = await apiClient.get<PaginatedDocuments>('/documents/accessible', {
    params: { skip, limit: pageSize },
  })
  return response.data
}

export const getAllDocuments = async (
  page: number = 1,
  pageSize: number = 10
): Promise<PaginatedDocuments> => {
  const skip = (page - 1) * pageSize
  const response = await apiClient.get<PaginatedDocuments>('/documents/', {
    params: { skip, limit: pageSize },
  })
  return response.data
}

export const getDocument = async (documentId: string): Promise<Document> => {
  const response = await apiClient.get<Document>(`/documents/${documentId}`)
  return response.data
}

export const uploadDocument = async (
  file: File,
  allowedRoles?: string[]
): Promise<Document> => {
  const formData = new FormData()
  formData.append('file', file)
  
  if (allowedRoles && allowedRoles.length > 0) {
    formData.append('allowed_roles', JSON.stringify(allowedRoles))
  }

  const response = await apiClient.post<Document>('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const deleteDocument = async (documentId: string): Promise<void> => {
  await apiClient.delete(`/documents/${documentId}`)
}

export const shareDocument = async (
  documentId: string,
  permissionType: 'user' | 'role',
  grantedTo: string
): Promise<DocumentPermission> => {
  const data: ShareDocumentRequest = {
    permission_type: permissionType,
    granted_to: grantedTo,
  }
  const response = await apiClient.post<DocumentPermission>(`/documents/${documentId}/share`, data)
  return response.data
}

export const getDocumentPermissions = async (
  documentId: string
): Promise<DocumentPermission[]> => {
  const response = await apiClient.get<DocumentPermission[]>(`/documents/${documentId}/permissions`)
  return response.data
}

export const revokeDocumentPermission = async (
  documentId: string,
  permissionId: number
): Promise<void> => {
  await apiClient.delete(`/documents/${documentId}/share/${permissionId}`)
}

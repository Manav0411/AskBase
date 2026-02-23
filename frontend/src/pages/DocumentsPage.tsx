import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Skeleton,
  Alert,
  Pagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tabs,
  Tab,
  LinearProgress,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Chip,
  CircularProgress,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Select,
  MenuItem,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material'
import {
  ChatOutlined,
  UploadFileOutlined,
  DeleteOutline,
  ShareOutlined,
  ExpandMoreOutlined,
  PersonOutline,
  GroupOutlined,
} from '@mui/icons-material'
import Layout from '../components/Layout'
import {
  getAccessibleDocuments,
  getAllDocuments,
  uploadDocument,
  deleteDocument,
  getDocumentPermissions,
  shareDocument,
  revokeDocumentPermission,
} from '../api/documents'
import { createConversation } from '../api/chat'
import { useAuthStore } from '../store/authStore'
import type { Document } from '../types'

export default function DocumentsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useAuthStore((state) => state.user)
  const isAdmin = user?.role === 'admin'
  
  const [page, setPage] = useState(1)
  const pageSize = 10
  const [currentTab, setCurrentTab] = useState(0)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedRoles, setSelectedRoles] = useState<string[]>([])
  const [shareDialogOpen, setShareDialogOpen] = useState(false)
  const [selectedDocumentForSharing, setSelectedDocumentForSharing] = useState<Document | null>(null)
  const [newPermissionValue, setNewPermissionValue] = useState('')
  const [expandedDocument, setExpandedDocument] = useState<string | false>(false)

  const {
    data: documentsData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['documents', currentTab === 0 ? 'accessible' : currentTab === 1 ? 'all' : 'all-for-permissions', page, pageSize],
    queryFn: () =>
      currentTab === 0
        ? getAccessibleDocuments(page, pageSize)
        : getAllDocuments(page, pageSize),
    refetchInterval: (query) => {
      if (currentTab === 2) return false
      const hasProcessingDocs = query.state.data?.items?.some((doc: Document) => doc.status === 'processing')
      return hasProcessingDocs ? 3000 : false
    },
    enabled: currentTab !== 2,
  })

  const { data: allDocsForPermissions, isLoading: isLoadingAllDocs } = useQuery({
    queryKey: ['documents', 'all-for-permissions-full'],
    queryFn: () => getAllDocuments(1, 1000),
    enabled: currentTab === 2 && isAdmin,
  })

  const processingCount = documentsData?.items?.filter(doc => doc.status === 'processing').length || 0
  const prevProcessingCountRef = useRef<number>(0)

  useEffect(() => {
    if (prevProcessingCountRef.current > 0 && processingCount < prevProcessingCountRef.current) {
      console.log('Documents finished processing, refreshing all tabs...')
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    }
    prevProcessingCountRef.current = processingCount
  }, [processingCount, queryClient])

  const createConversationMutation = useMutation({
    mutationFn: (params: { documentId: string; title?: string }) =>
      createConversation(params.documentId, params.title),
    onSuccess: (conversation) => {
      navigate(`/chat/${conversation.id}`)
    },
  })

  const uploadMutation = useMutation({
    mutationFn: ({ file, roles }: { file: File; roles?: string[] }) =>
      uploadDocument(file, roles),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setUploadDialogOpen(false)
      setSelectedFile(null)
      setSelectedRoles([])
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteDocument(id),
    onMutate: async (deletedId) => {
      await queryClient.cancelQueries({ queryKey: ['documents'] })

      const previousData = queryClient.getQueryData([
        'documents',
        currentTab === 0 ? 'accessible' : 'all',
        page,
        pageSize,
      ])

      queryClient.setQueryData(
        ['documents', currentTab === 0 ? 'accessible' : 'all', page, pageSize],
        (old: any) => {
          if (!old) return old
          return {
            ...old,
            items: old.items.filter((doc: any) => doc.id !== deletedId),
            pagination: {
              ...old.pagination,
              total: old.pagination.total - 1,
            },
          }
        }
      )

      return { previousData }
    },
    onError: (error: any, _deletedId, context) => {
      console.error('Delete error:', error?.response?.data)
      if (context?.previousData) {
        queryClient.setQueryData(
          ['documents', currentTab === 0 ? 'accessible' : 'all', page, pageSize],
          context.previousData
        )
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const shareMutation = useMutation({
    mutationFn: ({ documentId, permissionType, grantedTo }: {
      documentId: string
      permissionType: 'user' | 'role'
      grantedTo: string
    }) => shareDocument(documentId, permissionType, grantedTo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['permissions'] })
      setShareDialogOpen(false)
      setNewPermissionValue('')
      setSelectedDocumentForSharing(null)
    },
  })

  const revokeMutation = useMutation({
    mutationFn: ({ documentId, permissionId }: {
      documentId: string
      permissionId: number
    }) => revokeDocumentPermission(documentId, permissionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['permissions'] })
    },
  })

  const handleStartChat = (documentId: string, documentName: string) => {
    createConversationMutation.mutate({
      documentId,
      title: `Chat about ${documentName}`,
    })
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        alert('Please select a PDF file')
        return
      }
      if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB')
        return
      }
      setSelectedFile(file)
    }
  }

  const handleRoleChange = (role: string) => {
    setSelectedRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]
    )
  }

  const handleUpload = () => {
    if (selectedFile) {
      uploadMutation.mutate({
        file: selectedFile,
        roles: selectedRoles.length > 0 ? selectedRoles : undefined,
      })
    }
  }

  const handleDelete = (id: string, filename: string) => {
    if (window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      deleteMutation.mutate(id)
    }
  }

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value)
  }

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue)
    setPage(1)
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const handleOpenShareDialog = (doc: Document) => {
    setSelectedDocumentForSharing(doc)
    setShareDialogOpen(true)
  }

  const handleSharePermission = () => {
    if (selectedDocumentForSharing && newPermissionValue.trim()) {
      shareMutation.mutate({
        documentId: selectedDocumentForSharing.id,
        permissionType: 'role',
        grantedTo: newPermissionValue.trim(),
      })
    }
  }

  const handleCloseShareDialog = () => {
    setShareDialogOpen(false)
    shareMutation.reset()
    setNewPermissionValue('')
    setSelectedDocumentForSharing(null)
  }

  const handleRevokePermission = (documentId: string, permissionId: number, grantedTo: string) => {
    if (window.confirm(`Are you sure you want to revoke access for "${grantedTo}"?`)) {
      revokeMutation.mutate({ documentId, permissionId })
    }
  }

  return (
    <Layout maxWidth="xl">
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: 3,
          animation: 'fadeIn 0.5s ease-out',
          '@keyframes fadeIn': {
            from: {
              opacity: 0,
              transform: 'translateY(20px)',
            },
            to: {
              opacity: 1,
              transform: 'translateY(0)',
            },
          },
        }}
      >
        {/* Page header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography 
              variant="h4" 
              gutterBottom 
              sx={{ 
                mb: 1, 
                fontWeight: 700,
                background: 'linear-gradient(135deg, #ffffff 0%, #3b82f6 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Documents
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {isAdmin
                ? 'Manage documents and start conversations'
                : 'Documents you have access to. Start a chat to ask questions about any document.'}
            </Typography>
          </Box>
          {isAdmin && (
            <Button
              variant="contained"
              startIcon={<UploadFileOutlined />}
              onClick={() => setUploadDialogOpen(true)}
              sx={{
                px: 3,
                py: 1.5,
                fontWeight: 600,
              }}
            >
              Upload Document
            </Button>
          )}
        </Box>

        {/* Processing indicator banner */}
        {processingCount > 0 && (
          <Alert 
            severity="info" 
            icon={<CircularProgress size={20} />}
            sx={{
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              color: '#3b82f6',
              '& .MuiAlert-icon': {
                color: '#3b82f6',
              },
            }}
          >
            <strong>{processingCount}</strong> document{processingCount > 1 ? 's are' : ' is'} being processed.
            The page will auto-update when processing completes.
          </Alert>
        )}

        {/* Admin tabs */}
        {isAdmin && (
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={currentTab} onChange={handleTabChange}>
              <Tab label="My Documents" />
              <Tab label="All Documents" />
              <Tab label="Document Access" />
            </Tabs>
          </Box>
        )}

        {/* Error state */}
        {isError && (
          <Alert severity="error">
            Failed to load documents. Please try again.
          </Alert>
        )}

        {/* Upload error */}
        {uploadMutation.isError && (
          <Alert severity="error">
            Upload failed. Please check file size and format.
          </Alert>
        )}

        {/* Delete error */}
        {deleteMutation.isError && (
          <Alert severity="error" onClose={() => deleteMutation.reset()}>
            {(() => {
              const error = deleteMutation.error as any
              const detail = error?.response?.data?.detail
              return typeof detail === 'string' ? detail : 'Failed to delete document. Please try again.'
            })()}
          </Alert>
        )}

        {/* Loading state */}
        {(isLoading || (currentTab === 2 && isLoadingAllDocs)) && (
          <Box>
            <Skeleton variant="rectangular" height={60} sx={{ mb: 1 }} />
            <Skeleton variant="rectangular" height={60} sx={{ mb: 1 }} />
            <Skeleton variant="rectangular" height={60} />
          </Box>
        )}

        {currentTab !== 2 && !isLoading && documentsData && (
          <>
            {documentsData.items.length === 0 ? (
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary">
                  No documents available yet
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {isAdmin
                    ? 'Upload your first document to get started'
                    : 'Contact an administrator to get access to documents'}
                </Typography>
              </Paper>
            ) : (
              <>
                <TableContainer 
                  component={Paper}
                  sx={{
                    backgroundColor: 'rgba(20, 20, 20, 0.6)',
                    backdropFilter: 'blur(10px)',
                    '& .MuiTableRow-root': {
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        backgroundColor: 'rgba(59, 130, 246, 0.05)',
                        transform: 'translateX(4px)',
                      },
                    },
                  }}
                >
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 700, fontSize: '0.9rem' }}>Document Name</TableCell>
                        <TableCell sx={{ fontWeight: 700, fontSize: '0.9rem' }}>Status</TableCell>
                        <TableCell sx={{ fontWeight: 700, fontSize: '0.9rem' }}>Uploaded</TableCell>
                        <TableCell align="right" sx={{ fontWeight: 700, fontSize: '0.9rem' }}>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {documentsData.items.map((doc) => (
                        <TableRow key={doc.id} hover>
                          <TableCell>{doc.original_filename}</TableCell>
                          <TableCell>
                            {doc.status === 'processing' ? (
                              <Tooltip title="Document is being processed. This may take a few moments...">
                                <Chip
                                  icon={<CircularProgress size={16} />}
                                  label="Processing"
                                  color="warning"
                                  size="small"
                                  sx={{
                                    animation: 'pulse 2s ease-in-out infinite',
                                    '@keyframes pulse': {
                                      '0%, 100%': { opacity: 1 },
                                      '50%': { opacity: 0.7 },
                                    },
                                  }}
                                />
                              </Tooltip>
                            ) : doc.status === 'completed' ? (
                              <Chip label="Ready" color="success" size="small" />
                            ) : (
                              <Chip label="Failed" color="error" size="small" />
                            )}
                          </TableCell>
                          <TableCell>{formatDate(doc.uploaded_at)}</TableCell>
                          <TableCell align="right">
                            <Tooltip
                              title={
                                doc.status === 'processing'
                                  ? 'Document is still processing. Please wait...'
                                  : doc.status === 'failed'
                                  ? 'Document processing failed. Please try uploading again.'
                                  : 'Start a conversation about this document'
                              }
                            >
                              <span>
                                <Button
                                  variant="contained"
                                  size="small"
                                  startIcon={<ChatOutlined />}
                                  onClick={() => handleStartChat(doc.id, doc.original_filename)}
                                  disabled={doc.status !== 'completed' || createConversationMutation.isPending}
                                  sx={{ mr: 1 }}
                                >
                                  Start Chat
                                </Button>
                              </span>
                            </Tooltip>
                            {isAdmin && (
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleDelete(doc.id, doc.original_filename)}
                                disabled={deleteMutation.isPending}
                              >
                                <DeleteOutline />
                              </IconButton>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {/* Pagination */}
                {documentsData.pagination.total_pages > 1 && (
                  <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                    <Pagination
                      count={documentsData.pagination.total_pages}
                      page={page}
                      onChange={handlePageChange}
                      color="primary"
                    />
                  </Box>
                )}

                {/* Pagination info */}
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center' }}>
                  Showing {documentsData.items.length} of {documentsData.pagination.total} documents
                </Typography>
              </>
            )}
          </>
        )}

        {/* Document Access Tab - Permissions Management */}
        {currentTab === 2 && !isLoadingAllDocs && allDocsForPermissions && (
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Manage document permissions. Click on a document to view and manage who has access.
            </Typography>
            
            {allDocsForPermissions.items.length === 0 ? (
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary">
                  No documents available
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Upload documents to manage permissions
                </Typography>
              </Paper>
            ) : (
              <Box>
                {allDocsForPermissions.items.map((doc) => (
                  <DocumentPermissionsAccordion
                    key={doc.id}
                    doc={doc}
                    expanded={expandedDocument === doc.id}
                    onExpand={() => setExpandedDocument(expandedDocument === doc.id ? false : doc.id)}
                    onShare={() => handleOpenShareDialog(doc)}
                    onRevoke={handleRevokePermission}
                    formatDate={formatDate}
                  />
                ))}
              </Box>
            )}
          </Box>
        )}

        {/* Upload Dialog */}
        <Dialog 
          open={uploadDialogOpen} 
          onClose={() => setUploadDialogOpen(false)} 
          maxWidth="sm" 
          fullWidth
          PaperProps={{
            sx: {
              backgroundColor: 'rgba(20, 20, 20, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid #2a2a2a',
            },
          }}
        >
          <DialogTitle sx={{ fontWeight: 700, fontSize: '1.5rem' }}>Upload Document</DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Select a PDF file to upload (max 10MB)
            </Typography>
            <Button
              variant="outlined"
              component="label"
              fullWidth
              sx={{ mb: 2 }}
            >
              Choose File
              <input
                type="file"
                hidden
                accept="application/pdf"
                onChange={handleFileSelect}
              />
            </Button>
            {selectedFile && (
              <Alert severity="info" sx={{ mb: 3 }}>
                Selected: {selectedFile.name} ({formatFileSize(selectedFile.size)})
              </Alert>
            )}

            {/* Access Control Section */}
            <Box sx={{ mt: 3, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Access Control
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Choose who can access this document. If none selected, only you will have access.
              </Typography>

              {/* Role Selection */}
              <FormControl component="fieldset">
                <FormLabel component="legend">Allow Access by Role</FormLabel>
                <FormGroup>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedRoles.includes('hr')}
                        onChange={() => handleRoleChange('hr')}
                      />
                    }
                    label="HR"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedRoles.includes('engineer')}
                        onChange={() => handleRoleChange('engineer')}
                      />
                    }
                    label="Engineer"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedRoles.includes('intern')}
                        onChange={() => handleRoleChange('intern')}
                      />
                    }
                    label="Intern"
                  />
                </FormGroup>
              </FormControl>
            </Box>

            {uploadMutation.isPending && <LinearProgress sx={{ mt: 2 }} />}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setUploadDialogOpen(false)} disabled={uploadMutation.isPending}>
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              variant="contained"
              disabled={!selectedFile || uploadMutation.isPending}
            >
              Upload
            </Button>
          </DialogActions>
        </Dialog>

        {/* Share Document Dialog */}
        <Dialog 
          open={shareDialogOpen} 
          onClose={handleCloseShareDialog} 
          maxWidth="sm" 
          fullWidth
          PaperProps={{
            sx: {
              backgroundColor: 'rgba(20, 20, 20, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid #2a2a2a',
            },
          }}
        >
          <DialogTitle sx={{ fontWeight: 700, fontSize: '1.5rem' }}>Share Document</DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {selectedDocumentForSharing?.original_filename}
            </Typography>
            
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Select Role</InputLabel>
              <Select
                value={newPermissionValue}
                onChange={(e) => {
                  setNewPermissionValue(e.target.value)
                  shareMutation.reset() 
                }}
                label="Select Role"
              >
                <MenuItem value="hr">HR</MenuItem>
                <MenuItem value="engineer">Engineer</MenuItem>
                <MenuItem value="intern">Intern</MenuItem>
              </Select>
            </FormControl>

            {shareMutation.isError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {shareMutation.error instanceof Error 
                  ? (shareMutation.error as any)?.response?.data?.detail || shareMutation.error.message
                  : 'Failed to share document. Please check the input and try again.'}
              </Alert>
            )}
            {shareMutation.isPending && <LinearProgress sx={{ mt: 2 }} />}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseShareDialog} disabled={shareMutation.isPending}>
              Cancel
            </Button>
            <Button
              onClick={handleSharePermission}
              variant="contained"
              disabled={!newPermissionValue.trim() || shareMutation.isPending}
            >
              Share
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Layout>
  )
}

function DocumentPermissionsAccordion({ 
  doc, 
  expanded, 
  onExpand, 
  onShare, 
  onRevoke, 
  formatDate 
}: {
  doc: Document
  expanded: boolean
  onExpand: () => void
  onShare: () => void
  onRevoke: (documentId: string, permissionId: number, grantedTo: string) => void
  formatDate: (date: string) => string
}) {
  const { data: permissions, isLoading } = useQuery({
    queryKey: ['permissions', doc.id],
    queryFn: () => getDocumentPermissions(doc.id),
    enabled: expanded,
  })

  return (
    <Accordion expanded={expanded} onChange={onExpand}>
      <AccordionSummary expandIcon={<ExpandMoreOutlined />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
          <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
            {doc.original_filename}
          </Typography>
          <Chip 
            label={`Uploaded: ${formatDate(doc.uploaded_at)}`} 
            size="small" 
            variant="outlined"
          />
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle2">Access Permissions</Typography>
            <Button
              size="small"
              variant="outlined"
              startIcon={<ShareOutlined />}
              onClick={(e) => {
                e.stopPropagation()
                onShare()
              }}
            >
              Add Permission
            </Button>
          </Box>

          {isLoading && <CircularProgress size={24} />}

          {permissions && permissions.length === 0 && (
            <Alert severity="info">
              No explicit permissions set. Only the uploader and admins can access this document.
            </Alert>
          )}

          {permissions && permissions.length > 0 && (
            <List dense>
              {permissions.map((perm) => (
                <ListItem key={perm.id} divider>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {perm.permission_type === 'role' ? (
                          <GroupOutlined fontSize="small" color="primary" />
                        ) : (
                          <PersonOutline fontSize="small" color="primary" />
                        )}
                        <Typography variant="body2">
                          <strong>{perm.permission_type === 'role' ? 'Role:' : 'User ID:'}</strong> {perm.granted_to}
                        </Typography>
                      </Box>
                    }
                    secondary={`Granted: ${formatDate(perm.granted_at)}`}
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      size="small"
                      color="error"
                      onClick={() => onRevoke(doc.id, perm.id, perm.granted_to)}
                    >
                      <DeleteOutline fontSize="small" />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
              )}
            </Box>
          </AccordionDetails>
        </Accordion>
      )
    }


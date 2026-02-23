import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Grid,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  TextField,
  Button,
  Typography,
  Paper,
  IconButton,
  Skeleton,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  SendOutlined,
  DeleteOutline,
  SmartToyOutlined,
  PersonOutline,
} from '@mui/icons-material'
import Layout from '../components/Layout'
import {
  getConversations,
  getConversation,
  sendMessage,
  deleteConversation,
} from '../api/chat'
import type { Message } from '../types'

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [messageInput, setMessageInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const isValidConversationId: boolean = !!(conversationId && conversationId.trim())

  const { data: conversationsData } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => getConversations(1, 100),
  })

  const { data: conversation, isLoading: conversationLoading, isError: conversationError } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => getConversation(conversationId!),
    enabled: isValidConversationId,
    retry: false,
  })

  const sendMessageMutation = useMutation({
    mutationFn: (content: string) => sendMessage(conversationId!, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] })
      setMessageInput('')
    },
  })

  const deleteConversationMutation = useMutation({
    mutationFn: (id: string) => deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      navigate('/documents')
    },
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversation?.messages])

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    if (messageInput.trim()) {
      sendMessageMutation.mutate(messageInput)
    }
  }

  const handleDeleteConversation = (id: string) => {
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      deleteConversationMutation.mutate(id)
    }
  }

  const formatTime = (dateString: string): string => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    })
  }

  return (
    <Layout maxWidth="xl" disablePadding>
      <Grid container spacing={2} sx={{ flex: 1, p: 3, overflow: 'hidden' }}>
        {/* Left sidebar - Conversations list */}
        <Grid size={{ xs: 12, md: 3 }} sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <Paper 
            sx={{ 
              flex: 1, 
              display: 'flex', 
              flexDirection: 'column', 
              overflow: 'hidden',
              backgroundColor: 'rgba(20, 20, 20, 0.6)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <Box 
              sx={{ 
                p: 2.5, 
                borderBottom: '1px solid #2a2a2a',
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%)',
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 700 }}>Conversations</Typography>
            </Box>
            <List 
              sx={{ 
                flex: 1, 
                overflow: 'auto',
                '&::-webkit-scrollbar': {
                  width: '8px',
                },
                '&::-webkit-scrollbar-track': {
                  background: '#0a0a0a',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: '#2a2a2a',
                  borderRadius: '4px',
                  '&:hover': {
                    background: '#3a3a3a',
                  },
                },
              }}
            >
              {conversationsData?.items.map((conv) => (
                <ListItem key={conv.id} disablePadding>
                  <ListItemButton
                    selected={conv.id === conversationId}
                    onClick={() => {
                      console.log('Navigating to conversation:', conv.id)
                      navigate(`/chat/${conv.id}`)
                    }}
                    sx={{
                      transition: 'all 0.2s ease',
                      borderLeft: conv.id === conversationId ? '3px solid #3b82f6' : '3px solid transparent',
                      backgroundColor: conv.id === conversationId ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                      '&:hover': {
                        backgroundColor: 'rgba(59, 130, 246, 0.05)',
                        borderLeftColor: '#3b82f6',
                        transform: 'translateX(4px)',
                      },
                    }}
                  >
                    <ListItemText
                      primary={conv.title}
                      secondary={new Date(conv.created_at).toLocaleDateString()}
                      primaryTypographyProps={{
                        fontWeight: conv.id === conversationId ? 600 : 400,
                      }}
                    />
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteConversation(conv.id)
                      }}
                      sx={{
                        color: 'text.secondary',
                        '&:hover': {
                          color: '#ff4757',
                        },
                      }}
                    >
                      <DeleteOutline fontSize="small" />
                    </IconButton>
                  </ListItemButton>
                </ListItem>
              ))}
              {conversationsData?.items.length === 0 && (
                <ListItem>
                  <ListItemText
                    primary="No conversations yet"
                    secondary="Start by selecting a document"
                  />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>

        {/* Right main area - Messages and input */}
        <Grid size={{ xs: 12, md: 9 }} sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <Paper 
            sx={{ 
              flex: 1, 
              display: 'flex', 
              flexDirection: 'column', 
              overflow: 'hidden',
              backgroundColor: 'rgba(20, 20, 20, 0.6)',
              backdropFilter: 'blur(10px)',
            }}
          >
            {/* Conversation header */}
            {conversation && (
              <Box 
                sx={{ 
                  p: 2.5, 
                  borderBottom: '1px solid #2a2a2a',
                  background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%)',
                }}
              >
                <Typography variant="h6" sx={{ fontWeight: 700 }}>{conversation.title}</Typography>
                <Typography variant="caption" color="text.secondary">
                  Document: {conversation.document?.original_filename || 'Unknown'}
                </Typography>
              </Box>
            )}

            {/* Messages area */}
            <Box 
              sx={{ 
                flex: 1, 
                overflow: 'auto', 
                p: 2.5,
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
              {conversationLoading && (
                <Box>
                  <Skeleton variant="rectangular" height={60} sx={{ mb: 2 }} />
                  <Skeleton variant="rectangular" height={60} sx={{ mb: 2 }} />
                  <Skeleton variant="rectangular" height={60} />
                </Box>
              )}

              {conversationError && (
                <Alert severity="error">
                  Failed to load conversation. Please try again.
                </Alert>
              )}

              {!isValidConversationId && (
                <Box sx={{ textAlign: 'center', mt: 10 }}>
                  <Typography variant="h6" color="text.secondary">
                    Select a conversation to start chatting
                  </Typography>
                </Box>
              )}

              {conversation?.messages && conversation.messages.length === 0 && (
                <Box sx={{ textAlign: 'center', mt: 10 }}>
                  <Typography variant="h6" color="text.secondary">
                    No messages yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Start the conversation by asking a question about the document
                  </Typography>
                </Box>
              )}

              {/* Render messages */}
              {conversation?.messages?.map((message: Message) => (
                <Box
                  key={message.id}
                  sx={{
                    display: 'flex',
                    justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                    mb: 2,
                    animation: 'slideUp 0.3s ease-out',
                    '@keyframes slideUp': {
                      from: {
                        opacity: 0,
                        transform: 'translateY(10px)',
                      },
                      to: {
                        opacity: 1,
                        transform: 'translateY(0)',
                      },
                    },
                  }}
                >
                  <Paper
                    sx={{
                      p: 2.5,
                      maxWidth: '75%',
                      backgroundColor: message.role === 'user'
                        ? 'rgba(59, 130, 246, 0.1)'
                        : 'rgba(20, 20, 20, 0.8)',
                      border: message.role === 'user'
                        ? '1px solid rgba(59, 130, 246, 0.3)'
                        : '1px solid #2a2a2a',
                      color: 'text.primary',
                      backdropFilter: 'blur(10px)',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {message.role === 'user' ? (
                        <PersonOutline fontSize="small" sx={{ mr: 1, color: '#3b82f6' }} />
                      ) : (
                        <SmartToyOutlined fontSize="small" sx={{ mr: 1, color: '#8b5cf6' }} />
                      )}
                      <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary' }}>
                        {message.role === 'user' ? 'You' : 'AI Assistant'} •{' '}
                        {formatTime(message.timestamp)}
                      </Typography>
                    </Box>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                      {message.content}
                    </Typography>
                    {/* Display confidence score for assistant messages */}
                    {message.role === 'assistant' && message.confidence_score !== null && (
                      <Box sx={{ mt: 1.5, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            color: message.confidence_score >= 0.75 ? '#3b82f6' : message.confidence_score >= 0.4 ? '#fbbf24' : '#ef4444',
                            fontWeight: 600,
                            fontSize: '0.75rem',
                          }}
                        >
                          Confidence: {(message.confidence_score * 100).toFixed(0)}%
                        </Typography>
                        <Typography variant="caption">
                          {message.confidence_score >= 0.75 ? '🔵' : message.confidence_score >= 0.4 ? '🟡' : '🔴'}
                        </Typography>
                      </Box>
                    )}
                  </Paper>
                </Box>
              ))}

              {/* AI typing indicator */}
              {sendMessageMutation.isPending && (
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <SmartToyOutlined fontSize="small" sx={{ mr: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    AI is typing
                  </Typography>
                  <CircularProgress size={16} sx={{ ml: 1 }} />
                </Box>
              )}

              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </Box>

            {/* Message input */}
            {isValidConversationId && (
              <Box 
                sx={{ 
                  p: 2.5, 
                  borderTop: '1px solid #2a2a2a',
                  backgroundColor: 'rgba(10, 10, 10, 0.5)',
                  backdropFilter: 'blur(10px)',
                }}
              >
                <form onSubmit={handleSendMessage}>
                  <Box sx={{ display: 'flex', gap: 1.5 }}>
                    <TextField
                      fullWidth
                      placeholder="Ask a question about the document..."
                      value={messageInput}
                      onChange={(e) => setMessageInput(e.target.value)}
                      disabled={sendMessageMutation.isPending}
                      multiline
                      maxRows={4}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          backgroundColor: 'rgba(20, 20, 20, 0.6)',
                          '&:hover fieldset': {
                            borderColor: '#3b82f6',
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: '#3b82f6',
                            borderWidth: 2,
                          },
                        },
                      }}
                    />
                    <Button
                      type="submit"
                      variant="contained"
                      endIcon={<SendOutlined />}
                      disabled={!messageInput.trim() || sendMessageMutation.isPending}
                      sx={{
                        px: 3,
                        minWidth: '120px',
                        fontWeight: 600,
                      }}
                    >
                      Send
                    </Button>
                  </Box>
                </form>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Layout>
  )
}

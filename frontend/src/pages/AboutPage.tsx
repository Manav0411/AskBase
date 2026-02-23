import {
  Box,
  Card,
  CardContent,
  Typography,
  Container,
  Stack,
} from '@mui/material'
import {
  ChatOutlined,
  DescriptionOutlined,
  SecurityOutlined,
  SmartToyOutlined,
} from '@mui/icons-material'
import Layout from '../components/Layout'

export default function AboutPage() {
  return (
    <Layout maxWidth="md">
      <Container>
        <Stack spacing={4} sx={{ py: 4 }}>
          {/* Header */}
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
              About AskBase
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ mt: 2 }}>
              Your intelligent document management and chat assistant
            </Typography>
          </Box>

          {/* Overview Card */}
          <Card elevation={2}>
            <CardContent sx={{ p: 4 }}>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                What is AskBase?
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                AskBase is a powerful application that combines document management with
                intelligent conversational AI. Upload your documents and interact with them
                through natural language conversations, making information retrieval and
                knowledge management effortless.
              </Typography>
            </CardContent>
          </Card>

          {/* Features Section */}
          <Box>
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
              Key Features
            </Typography>
            <Stack spacing={2}>
              {/* Document Management Feature */}
              <Card elevation={1}>
                <CardContent sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <DescriptionOutlined color="primary" sx={{ fontSize: 40, mt: 0.5 }} />
                  <Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                      Document Management
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Upload, organize, and manage your documents with ease. Support for
                      multiple file formats with secure storage and quick access.
                    </Typography>
                  </Box>
                </CardContent>
              </Card>

              {/* AI Chat Feature */}
              <Card elevation={1}>
                <CardContent sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <SmartToyOutlined color="primary" sx={{ fontSize: 40, mt: 0.5 }} />
                  <Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                      AI-Powered Chat
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Engage in intelligent conversations about your documents. Ask questions,
                      get summaries, and extract insights using advanced AI technology.
                    </Typography>
                  </Box>
                </CardContent>
              </Card>

              {/* Real-time Conversations Feature */}
              <Card elevation={1}>
                <CardContent sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <ChatOutlined color="primary" sx={{ fontSize: 40, mt: 0.5 }} />
                  <Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                      Real-time Conversations
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Create and manage multiple conversation threads. Keep your discussions
                      organized and easily revisit past conversations.
                    </Typography>
                  </Box>
                </CardContent>
              </Card>

              {/* Security Feature */}
              <Card elevation={1}>
                <CardContent sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                  <SecurityOutlined color="primary" sx={{ fontSize: 40, mt: 0.5 }} />
                  <Box>
                    <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                      Secure & Private
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Your data is protected with enterprise-grade security. Role-based
                      access control ensures that only authorized users can access your content.
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Stack>
          </Box>

          {/* Footer */}
          <Box sx={{ textAlign: 'center', pt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              © {new Date().getFullYear()} AskBase. Making knowledge accessible.
            </Typography>
          </Box>
        </Stack>
      </Container>
    </Layout>
  )
}

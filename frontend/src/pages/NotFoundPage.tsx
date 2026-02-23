import { Box, Typography, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        gap: 2,
      }}
    >
      <Typography variant="h1" color="primary">
        404
      </Typography>
      <Typography variant="h5" color="text.secondary">
        Page Not Found
      </Typography>
      <Button variant="contained" onClick={() => navigate('/documents')}>
        Go to Documents
      </Button>
    </Box>
  )
}

import { Paper, Typography, Box, Divider, Chip } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import DescriptionIcon from '@mui/icons-material/Description';

const ResultDisplay = ({ result }) => {
  const { status, message, document_id } = result;
  const isSuccess = status === 'success' || status === 'completed';

  return (
    <Paper
      sx={{
        p: 3,
        backgroundColor: 'background.paper'
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          mb: 2
        }}
      >
        {isSuccess ? (
          <CheckCircleIcon color="success" sx={{ fontSize: 30 }} />
        ) : (
          <ErrorIcon color="error" sx={{ fontSize: 30 }} />
        )}
        <Typography
          variant="h6"
          color={isSuccess ? 'success.main' : 'error.main'}
        >
          {message}
        </Typography>
      </Box>

      {isSuccess && document_id && (
        <>
          <Divider sx={{ my: 2 }} />
          
          <Box sx={{ mb: 3 }}>
            <Chip
              icon={<DescriptionIcon />}
              label={`Belge ID: ${document_id}`}
              color="primary"
              variant="outlined"
            />
          </Box>

          <Typography variant="body2" color="text.secondary">
            Belgeniz başarıyla işlendi ve sistemde kayıt altına alındı.
          </Typography>
        </>
      )}
    </Paper>
  );
};

export default ResultDisplay; 
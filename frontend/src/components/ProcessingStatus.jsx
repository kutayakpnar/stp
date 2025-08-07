import { Box, CircularProgress, Typography, Paper } from '@mui/material';

const ProcessingStatus = () => {
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
          gap: 2
        }}
      >
        <CircularProgress size={30} color="primary" />
        <Box>
          <Typography variant="h6" color="primary">
            Döküman İşleniyor
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Yapay zeka sistemi dökümanı analiz ediyor...
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default ProcessingStatus; 
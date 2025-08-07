import { useState } from 'react';
import { Box, TextField, Button, Typography, Paper } from '@mui/material';
import { toast } from 'react-toastify';

const LoginForm = ({ onLogin, onSwitchToRegister }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // App.jsx'teki handleLogin fonksiyonunu kullan
      await onLogin(formData);
    } catch (error) {
      console.error('Login form error:', error);
      // Error handling is done in App.jsx
    }
  };

  return (
    <Paper sx={{ p: 4, maxWidth: 400, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" component="h1" gutterBottom align="center" color="primary">
        Giriş Yap
      </Typography>
      
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
        <TextField
          fullWidth
          label="E-posta"
          name="username"
          type="email"
          value={formData.username}
          onChange={handleChange}
          margin="normal"
          required
          autoFocus
        />
        
        <TextField
          fullWidth
          label="Şifre"
          name="password"
          type="password"
          value={formData.password}
          onChange={handleChange}
          margin="normal"
          required
        />
        
        <Button
          type="submit"
          fullWidth
          variant="contained"
          color="primary"
          sx={{ mt: 3, mb: 2 }}
        >
          Giriş Yap
        </Button>
        
        <Button
          fullWidth
          variant="text"
          onClick={onSwitchToRegister}
          sx={{ mt: 1 }}
        >
          Hesabınız yok mu? Kayıt olun
        </Button>
      </Box>
    </Paper>
  );
};

export default LoginForm; 
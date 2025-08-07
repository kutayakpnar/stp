import { useState } from 'react';
import { Box, TextField, Button, Typography, Paper } from '@mui/material';
import { toast } from 'react-toastify';

const RegisterForm = ({ onRegister, onSwitchToLogin }) => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    password_confirm: ''
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

    // Şifre kontrolü
    if (formData.password !== formData.password_confirm) {
      toast.error('Şifreler eşleşmiyor!');
      return;
    }

    // Email kontrolü
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      toast.error('Geçerli bir email adresi giriniz!');
      return;
    }

    try {
      // password_confirm'i API'ye göndermeden önce kaldır
      const { password_confirm, ...submitData } = formData;
      
      // Email'i username olarak da kullan
      submitData.username = submitData.email;

      const response = await fetch('http://localhost:8000/api/v1/users/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Kayıt başarısız');
      }

      // Sadece onRegister'ı çağır, toast mesajını kaldır
      onRegister(data);
      onSwitchToLogin();
    } catch (error) {
      toast.error(error.message);
    }
  };

  return (
    <Paper sx={{ p: 4, maxWidth: 400, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" component="h1" gutterBottom align="center" color="primary">
        Kayıt Ol
      </Typography>
      
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
        <TextField
          fullWidth
          label="Ad Soyad"
          name="full_name"
          value={formData.full_name}
          onChange={handleChange}
          margin="normal"
          required
          autoFocus
        />
        
        <TextField
          fullWidth
          label="E-posta"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          margin="normal"
          required
          helperText="E-posta adresiniz kullanıcı adınız olarak kullanılacaktır"
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

        <TextField
          fullWidth
          label="Şifre Tekrar"
          name="password_confirm"
          type="password"
          value={formData.password_confirm}
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
          Kayıt Ol
        </Button>
        
        <Button
          fullWidth
          variant="text"
          onClick={onSwitchToLogin}
          sx={{ mt: 1 }}
        >
          Zaten hesabınız var mı? Giriş yapın
        </Button>
      </Box>
    </Paper>
  );
};

export default RegisterForm; 
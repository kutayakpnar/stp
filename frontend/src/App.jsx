import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Container, Typography, Paper, Alert, Box, Button } from '@mui/material';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import FileUpload from './components/FileUpload';
import ProcessingStatus from './components/ProcessingStatus';
import ResultDisplay from './components/ResultDisplay';
import RegisterForm from './components/RegisterForm';
import LoginForm from './components/LoginForm';
import DecisionsHistory from './components/DecisionsHistory';
import RealTimeStatus from './components/RealTimeStatus';
import { useSSE } from './hooks/useSSE';
import LogoutIcon from '@mui/icons-material/Logout';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// TEB Bankacılık teması
const theme = createTheme({
  palette: {
    primary: {
      main: '#2E7D32',
      light: '#4CAF50',
      dark: '#1B5E20',
    },
    secondary: {
      main: '#1976D2',
      light: '#42A5F5',
      dark: '#1565C0',
    },
    background: {
      default: '#F5F5F5',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#263238',
      secondary: '#546E7A',
    },
  },
  typography: {
    fontFamily: '"Segoe UI", "Helvetica Neue", Arial, sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.05)',
          borderRadius: 8,
        },
      },
    },
  },
});

function App() {
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [user, setUser] = useState(null);
  const [showRegister, setShowRegister] = useState(false);
  const [loading, setLoading] = useState(true);

  // SSE hook'u kullan
  const { 
    processingSteps, 
    isConnected, 
    connectionError, 
    clearProcessingSteps 
  } = useSSE(user);

  // Sayfa yüklendiğinde oturum kontrolü
  useEffect(() => {
    const checkSession = async () => {
      try {
        console.log('🔍 Session kontrolü başlatılıyor...');
        const response = await fetch(`${API_BASE_URL}/users/me`, {
          credentials: 'include'
        });
        
        console.log('📡 Session check response:', {
          status: response.status,
          ok: response.ok,
          url: response.url
        });
        
        if (response.ok) {
          const userData = await response.json();
          console.log('✅ User data received:', userData);
          setUser(userData);
        } else {
          console.log('❌ Session check failed:', response.status);
          // 401 ise token süresi dolmuş, normal durum
          if (response.status !== 401) {
            console.error('Beklenmeyen hata:', response.status);
          }
        }
      } catch (error) {
        console.error('🚫 Session check error:', error);
        console.error('Error details:', {
          message: error.message,
          stack: error.stack
        });
      } finally {
        console.log('✅ Session check tamamlandı, loading false yapılıyor');
        setLoading(false);
      }
    };

    checkSession();
  }, []);

  const handleFileUpload = async (uploadedFile) => {
    setFile(uploadedFile);
    setProcessing(true);
    setResult(null);
    
    // Önceki processing step'leri temizle
    clearProcessingSteps();

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const response = await fetch(`${API_BASE_URL}/process-document/`, {
        method: 'POST',
        credentials: 'include', // Cookie'leri gönder
        body: formData,
      });

      const data = await response.json();
      console.log('Backend response:', { status: response.status, data });

      if (!response.ok) {
        if (response.status === 401) {
          // Token süresi dolmuşsa çıkış yap
          handleLogout();
          return;
        }
        throw new Error(data.detail || 'Bir hata oluştu');
      }

      setResult(data);
      toast.success(data.message || 'Döküman başarıyla işlendi');
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.message);
      setResult({
        status: 'error',
        message: error.message
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleTextSubmit = async (text) => {
    setProcessing(true);
    setResult(null);
    
    // Önceki processing step'leri temizle
    clearProcessingSteps();

    try {
      const formData = new FormData();
      formData.append('text', text);

      const response = await fetch(`${API_BASE_URL}/process-text/`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          handleLogout();
          return;
        }
        throw new Error(data.detail || 'Bir hata oluştu');
      }

      setResult(data);
      toast.success(data.message || 'Metin başarıyla işlendi');
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.message);
      setResult({
        status: 'error',
        message: error.message
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleLogin = async (credentials) => {
    try {
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await fetch(`${API_BASE_URL}/users/login`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Giriş başarısız');
      }

      setUser(data.user);
      toast.success('Giriş başarılı!');
    } catch (error) {
      console.error('Login error:', error);
      toast.error(error.message);
      throw error;
    }
  };

  const handleRegister = async (userData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/register`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Kayıt başarısız');
      }

      toast.success('Kayıt başarılı! Giriş yapabilirsiniz.');
      setShowRegister(false);
    } catch (error) {
      console.error('Register error:', error);
      toast.error(error.message);
      throw error;
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/users/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setResult(null);
      setFile(null);
      clearProcessingSteps(); // Çıkış yaparken step'leri temizle
      toast.info('Çıkış yapıldı');
    }
  };

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <Container maxWidth="md" sx={{ py: 4 }}>
          <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="50vh" gap={2}>
            <Typography variant="h6" color="primary">STP Banking System</Typography>
            <Typography>Oturum kontrol ediliyor...</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <div style={{ 
                width: '20px', 
                height: '20px', 
                border: '2px solid #f3f3f3',
                borderTop: '2px solid #2E7D32',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              <Typography variant="body2" color="text.secondary">
                Lütfen bekleyiniz...
              </Typography>
            </Box>
            <style>
              {`
                @keyframes spin {
                  0% { transform: rotate(0deg); }
                  100% { transform: rotate(360deg); }
                }
              `}
            </style>
          </Box>
        </Container>
      </ThemeProvider>
    );
  }

  if (!user) {
    return (
      <ThemeProvider theme={theme}>
        <Container maxWidth="sm" sx={{ py: 4 }}>
          <Paper sx={{ p: 4 }}>
            <Typography variant="h4" align="center" gutterBottom color="primary">
              STP Banking System
            </Typography>
            <Typography variant="subtitle1" align="center" gutterBottom sx={{ mb: 3 }}>
              AI-Powered Document Processing
            </Typography>
            
            {showRegister ? (
              <RegisterForm 
                onRegister={handleRegister}
                onSwitchToLogin={() => setShowRegister(false)}
              />
            ) : (
              <LoginForm 
                onLogin={handleLogin}
                onSwitchToRegister={() => setShowRegister(true)}
              />
            )}
          </Paper>
        </Container>
        <ToastContainer position="bottom-right" theme="colored" />
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{
          display: 'flex',
          flexDirection: 'column',
          gap: 3
        }}>
          <Paper 
            sx={{ 
              p: 3, 
              mb: 3, 
              backgroundColor: 'primary.main',
              color: 'white',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <Box>
              <Typography variant="h5" gutterBottom>
                Hoş Geldiniz, {user.full_name || user.email}
              </Typography>
              <Typography variant="body1">
                Bu sistem, müşteri talimatlarını yapay zeka teknolojisi ile otomatik olarak işlemektedir. 
                Lütfen işlemek istediğiniz dökümanı yükleyin.
              </Typography>
              
              {/* SSE Bağlantı Durumu */}
              <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.8 }}>
                Real-time bağlantı: {isConnected ? '🟢 Aktif' : '🔴 Kapalı'}
              </Typography>
            </Box>
            <Button 
              variant="outlined" 
              onClick={handleLogout}
              startIcon={<LogoutIcon />}
              sx={{ 
                color: 'white', 
                borderColor: 'white',
                '&:hover': {
                  borderColor: 'white',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)'
                }
              }}
            >
              Çıkış
            </Button>
          </Paper>

          <FileUpload onFileUpload={handleFileUpload} onTextSubmit={handleTextSubmit} />
          
          {/* Real-time Status Component - SSE ile güncellenir */}
          <RealTimeStatus 
            processingSteps={processingSteps}
            isConnected={isConnected}
            connectionError={connectionError}
            show={processing || processingSteps.length > 0}
            isProcessing={processing}
          />
          
          {/* Eski processing status - fallback olarak */}
          {processing && processingSteps.length === 0 && <ProcessingStatus />}
          
          {result && <ResultDisplay result={result} />}

          <DecisionsHistory user={user} />
        </Box>
      </Container>
      <ToastContainer 
        position="bottom-right"
        theme="colored"
        autoClose={5000}
        toastStyle={{ 
          fontSize: '14px',
        }}
        style={{
          '--toastify-color-success': '#4CAF50',
          '--toastify-color-error': '#f44336',
        }}
      />
    </ThemeProvider>
  );
}

export default App;

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Paper, Typography, List, ListItem, ListItemIcon, ListItemText, TextField, Button, Tabs, Tab } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import { toast } from 'react-toastify';

const FileUpload = ({ onFileUpload, onTextSubmit }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [textInput, setTextInput] = useState('');

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleTextSubmit = () => {
    if (!textInput.trim()) {
      toast.error('Lütfen işlenecek metni girin');
      return;
    }
    
    onTextSubmit(textInput);
    setTextInput('');
  };

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Sadece PDF, JPG ve PNG dosyaları kabul edilmektedir.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error('Dosya boyutu 10MB\'dan küçük olmalıdır.');
      return;
    }

    onFileUpload(file);
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png']
    },
    multiple: false
  });

  return (
    <Box>
      <Tabs 
        value={activeTab} 
        onChange={handleTabChange} 
        sx={{ 
          mb: 3,
          '& .MuiTab-root': { 
            fontWeight: 500,
            fontSize: '1rem',
          }
        }}
      >
        <Tab 
          icon={<CloudUploadIcon />} 
          label="Dosya Yükle" 
          iconPosition="start"
        />
        <Tab 
          icon={<TextFieldsIcon />} 
          label="Metin Gir" 
          iconPosition="start"
        />
      </Tabs>

      {activeTab === 0 ? (
        // Dosya Yükleme Alanı
        <>
          <Paper
            {...getRootProps()}
            sx={{
              p: 4,
              backgroundColor: isDragActive ? 'background.paper' : 'background.default',
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              '&:hover': {
                borderColor: 'primary.main',
                backgroundColor: 'background.paper'
              }
            }}
          >
            <input {...getInputProps()} />
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 2
              }}
            >
              <CloudUploadIcon
                sx={{
                  fontSize: 60,
                  color: isDragActive ? 'primary.main' : 'grey.500'
                }}
              />
              <Typography
                variant="h6"
                color={isDragActive ? 'primary.main' : 'text.primary'}
                align="center"
              >
                {isDragActive
                  ? 'Dökümanı buraya bırakın'
                  : 'Bankacılık dökümanını yüklemek için tıklayın veya sürükleyin'}
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                PDF, JPG veya PNG formatında (maksimum 10MB)
              </Typography>
            </Box>
          </Paper>

          <Paper sx={{ mt: 3, p: 2, backgroundColor: 'background.paper' }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Desteklenen Döküman Türleri:
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <CheckCircleOutlineIcon color="primary" fontSize="small" />
                </ListItemIcon>
                <ListItemText 
                  primary="EFT ve Havale Talimatları"
                  secondary="Para transferi işlemleri için talimat formları"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckCircleOutlineIcon color="primary" fontSize="small" />
                </ListItemIcon>
                <ListItemText 
                  primary="Hesap Açılış Formları"
                  secondary="Bireysel ve kurumsal hesap açılış belgeleri"
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckCircleOutlineIcon color="primary" fontSize="small" />
                </ListItemIcon>
                <ListItemText 
                  primary="Kredi Başvuru Formları"
                  secondary="Bireysel ve ticari kredi başvuru dökümanları"
                />
              </ListItem>
            </List>
          </Paper>
        </>
      ) : (
        // Metin Girişi Alanı
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom color="primary">
            Metin Girişi
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            İşlenmesini istediğiniz bankacılık talimatını buraya yazabilirsiniz.
          </Typography>
          <TextField
            multiline
            rows={6}
            fullWidth
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Örnek: EFT talimatı - Gönderen: Ahmet Yılmaz, IBAN: TR33..., Tutar: 1000 TL"
            sx={{ mb: 2 }}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={handleTextSubmit}
            disabled={!textInput.trim()}
            sx={{ 
              minWidth: 150,
              '&.Mui-disabled': {
                backgroundColor: 'action.disabledBackground',
                color: 'action.disabled'
              }
            }}
          >
            İşle
          </Button>
        </Paper>
      )}
    </Box>
  );
};

export default FileUpload; 
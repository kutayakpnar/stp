import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Chip,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  Collapse,
  IconButton
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Upload as UploadIcon,
  Visibility as VisibilityIcon,
  Psychology as PsychologyIcon,
  Gavel as GavelIcon,
  CloudUpload as CloudUploadIcon,
  TextFields as TextFieldsIcon,
  Done as DoneIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Timeline as TimelineIcon,
  List as ListIcon
} from '@mui/icons-material';
import ProcessingStepper from './ProcessingStepper';

const getStepIcon = (stepName, status = 'completed') => {
  const iconProps = { 
    fontSize: 'small',
    color: status === 'error' ? 'error' : 'success'
  };

  if (stepName.includes('Başlatıldı') || stepName.includes('Başlangıç')) {
    return <InfoIcon {...iconProps} />;
  }
  if (stepName.includes('Dosya') || stepName.includes('Yüklendi')) {
    return <UploadIcon {...iconProps} />;
  }
  if (stepName.includes('OCR')) {
    return <VisibilityIcon {...iconProps} />;
  }
  if (stepName.includes('NLP') || stepName.includes('Analiz')) {
    return <PsychologyIcon {...iconProps} />;
  }
  if (stepName.includes('Karar')) {
    return <GavelIcon {...iconProps} />;
  }
  if (stepName.includes('Tamamlandı')) {
    return <DoneIcon {...iconProps} />;
  }
  if (stepName.includes('Hata')) {
    return <ErrorIcon {...iconProps} />;
  }
  
  return <CheckCircleIcon {...iconProps} />;
};

const getStepDetails = (details) => {
  if (!details || Object.keys(details).length === 0) {
    return null;
  }

  return (
    <Box sx={{ mt: 1 }}>
      {Object.entries(details).map(([key, value]) => (
        <Typography 
          key={key} 
          variant="caption" 
          display="block"
          sx={{ color: 'text.secondary', ml: 2 }}
        >
          <strong>{key}:</strong> {value}
        </Typography>
      ))}
    </Box>
  );
};

const RealTimeStatus = ({ 
  processingSteps, 
  isConnected, 
  connectionError,
  show = false,
  isProcessing = false
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [showDetails, setShowDetails] = useState(false);

  if (!show && processingSteps.length === 0) {
    return null;
  }

  const hasError = processingSteps.some(step => 
    step.step.includes('Hata') || step.details?.status === 'error'
  );
  
  const isCompleted = processingSteps.some(step => 
    step.step.includes('Tamamlandı')
  );

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Paper 
      elevation={2} 
      sx={{ 
        mt: 2,
        backgroundColor: hasError ? '#fff5f5' : (isCompleted ? '#f0f8f0' : 'background.paper'),
        border: hasError ? '1px solid #ffccd5' : (isCompleted ? '1px solid #c8e6c9' : 'none')
      }}
    >
      {/* Header */}
      <Box sx={{ p: 3, pb: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            📡 Gerçek Zamanlı İşlem Takibi
          </Typography>
          
          {/* Bağlantı durumu */}
          <Chip 
            size="small"
            label={isConnected ? "🟢 Bağlı" : "🔴 Bağlantı Yok"}
            color={isConnected ? "success" : "error"}
            variant="outlined"
          />
        </Box>

        {/* Bağlantı hatası */}
        {connectionError && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            {connectionError} - Otomatik yeniden bağlanma deneniyor...
          </Alert>
        )}

        {/* İşlem durumu */}
        {processingSteps.length > 0 && !isCompleted && !hasError && (
          <LinearProgress 
            sx={{ mb: 2 }} 
            variant="indeterminate"
            color="primary"
          />
        )}

        {/* Tabs */}
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab 
            icon={<TimelineIcon />} 
            label="İşlem Adımları" 
            iconPosition="start"
          />
          <Tab 
            icon={<ListIcon />} 
            label={`Detaylı Loglar (${processingSteps.length})`}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <Box sx={{ p: 3, pt: 0 }}>
        {/* Tab 0: Process Stepper */}
        {tabValue === 0 && (
          <Box sx={{ mt: 2 }}>
            <ProcessingStepper 
              processingSteps={processingSteps}
              isProcessing={isProcessing}
            />
          </Box>
        )}

        {/* Tab 1: Detailed Logs */}
        {tabValue === 1 && (
          <Box sx={{ mt: 2 }}>
            {processingSteps.length > 0 ? (
              <>
                {/* Genişlet/Daralt butonu */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    İşlem geçmişi ({processingSteps.length} adım)
                  </Typography>
                  <IconButton 
                    size="small" 
                    onClick={() => setShowDetails(!showDetails)}
                  >
                    {showDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                </Box>

                {/* Son 3 adımı her zaman göster */}
                <List dense>
                  {processingSteps.slice(-3).map((step) => (
                    <ListItem key={step.id} sx={{ py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        {getStepIcon(step.step, step.details?.status)}
                      </ListItemIcon>
                      
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {step.step}
                            </Typography>
                            
                            {/* Status chip */}
                            {step.details?.status === 'error' && (
                              <Chip 
                                label="Hata" 
                                size="small" 
                                color="error" 
                                variant="outlined"
                              />
                            )}
                            
                            {step.step.includes('Tamamlandı') && (
                              <Chip 
                                label="✅ Başarılı" 
                                size="small" 
                                color="success" 
                                variant="outlined"
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(step.timestamp).toLocaleTimeString('tr-TR')}
                            </Typography>
                            {getStepDetails(step.details)}
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                </List>

                {/* Tüm adımları göster (Collapse) */}
                {processingSteps.length > 3 && (
                  <Collapse in={showDetails}>
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 2, mb: 1, display: 'block' }}>
                      Önceki adımlar:
                    </Typography>
                    <List dense>
                      {processingSteps.slice(0, -3).map((step) => (
                        <ListItem key={step.id} sx={{ py: 0.5, opacity: 0.7 }}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            {getStepIcon(step.step, step.details?.status)}
                          </ListItemIcon>
                          
                          <ListItemText
                            primary={
                              <Typography variant="body2">
                                {step.step}
                              </Typography>
                            }
                            secondary={
                              <Typography variant="caption" color="text.secondary">
                                {new Date(step.timestamp).toLocaleTimeString('tr-TR')}
                              </Typography>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Collapse>
                )}
              </>
            ) : (
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  İşlem başladığında loglar burada görünecek...
                </Typography>
              </Box>
            )}
          </Box>
        )}

        {/* Durum mesajları */}
        {isCompleted && (
          <Alert severity="success" sx={{ mt: 2 }}>
            🎉 Belge işleme tamamlandı! Sonuçları aşağıda görebilirsiniz.
          </Alert>
        )}

        {hasError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            ❌ İşlem sırasında hata oluştu. Lütfen tekrar deneyin.
          </Alert>
        )}
      </Box>
    </Paper>
  );
};

export default RealTimeStatus; 
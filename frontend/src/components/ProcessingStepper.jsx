import React from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Typography,
  Chip,
  CircularProgress,
  Paper
} from '@mui/material';
import {
  Upload as UploadIcon,
  Visibility as VisibilityIcon,
  Psychology as PsychologyIcon,
  Gavel as GavelIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  RadioButtonUnchecked as PendingIcon
} from '@mui/icons-material';

// Tüm işlem adımları tanımı
const PROCESS_STEPS = [
  {
    id: 'upload',
    label: 'Dosya Yükleme',
    description: 'Belge sisteme yükleniyor',
    icon: UploadIcon,
    keywords: ['İşlem Başlatıldı', 'Dosya Okundu', 'Dosya Tipi Kontrolü', 'Veritabanı Kaydı', 'Belge Yüklendi']
  },
  {
    id: 'ocr',
    label: 'OCR İşlemi',
    description: 'Belgeden metin çıkarılıyor',
    icon: VisibilityIcon,
    keywords: ['OCR İşlemi Başlatıldı', 'OCR Tamamlandı']
  },
  {
    id: 'nlp',
    label: 'NLP Analizi',
    description: 'Metin analiz edilip veriler çıkarılıyor',
    icon: PsychologyIcon,
    keywords: ['NLP Analizi Başlatıldı', 'NLP Analizi Tamamlandı']
  },
  {
    id: 'decision',
    label: 'Karar Verme',
    description: 'İş kuralları uygulanıp karar veriliyor',
    icon: GavelIcon,
    keywords: ['Karar Verme Başlatıldı', 'Karar Verme Tamamlandı', 'İşlem Tamamlandı']
  }
];

const ProcessingStepper = ({ processingSteps, isProcessing = false }) => {
  // Mevcut adımları analiz et
  const getStepStatus = (step) => {
    const stepNames = processingSteps.map(ps => ps.step);
    
    // Bu adımla ilgili herhangi bir step var mı?
    const hasMatchingStep = stepNames.some(stepName => 
      step.keywords.some(keyword => stepName.includes(keyword))
    );
    
    // Hata var mı?
    const hasError = processingSteps.some(ps => 
      step.keywords.some(keyword => ps.step.includes(keyword)) && 
      (ps.step.includes('Hata') || ps.details?.status === 'error')
    );
    
    // Tamamlandı mı?
    const isCompleted = stepNames.some(stepName => 
      step.keywords.some(keyword => {
        if (step.id === 'upload') {
          return keyword === 'Belge Yüklendi' && stepName.includes(keyword);
        }
        if (step.id === 'ocr') {
          return keyword === 'OCR Tamamlandı' && stepName.includes(keyword);
        }
        if (step.id === 'nlp') {
          return keyword === 'NLP Analizi Tamamlandı' && stepName.includes(keyword);
        }
        if (step.id === 'decision') {
          return (keyword === 'Karar Verme Tamamlandı' || keyword === 'İşlem Tamamlandı') && stepName.includes(keyword);
        }
        return false;
      })
    );
    
    // Başlatıldı mı?
    const isStarted = stepNames.some(stepName => 
      step.keywords.some(keyword => stepName.includes(keyword))
    );
    
    if (hasError) return 'error';
    if (isCompleted) return 'completed';
    if (isStarted) return 'active';
    return 'pending';
  };
  
  // Aktif adımı bul
  const getActiveStep = () => {
    for (let i = 0; i < PROCESS_STEPS.length; i++) {
      const status = getStepStatus(PROCESS_STEPS[i]);
      if (status === 'active') return i;
      if (status === 'pending') return Math.max(0, i - 1);
    }
    
    // Eğer hiçbir adım aktif değilse, son tamamlanan adımı bul
    for (let i = PROCESS_STEPS.length - 1; i >= 0; i--) {
      const status = getStepStatus(PROCESS_STEPS[i]);
      if (status === 'completed') return i;
    }
    
    return isProcessing ? 0 : -1;
  };
  
  const activeStep = getActiveStep();
  
  // Step icon'unu belirle
  const getStepIcon = (step, status) => {
    const IconComponent = step.icon;
    
    if (status === 'error') {
      return <ErrorIcon color="error" />;
    } else if (status === 'completed') {
      return <CheckCircleIcon color="success" />;
    } else if (status === 'active') {
      return (
        <Box sx={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <CircularProgress size={20} thickness={4} />
          <Box sx={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}>
            <IconComponent sx={{ fontSize: 12, color: 'primary.main' }} />
          </Box>
        </Box>
      );
    } else {
      return <PendingIcon color="disabled" />;
    }
  };
  
  // Her adım için detay bilgisi
  const getStepDetails = (step) => {
    const relatedSteps = processingSteps.filter(ps => 
      step.keywords.some(keyword => ps.step.includes(keyword))
    );
    
    if (relatedSteps.length === 0) return null;
    
    const latestStep = relatedSteps[relatedSteps.length - 1];
    
    return (
      <Box sx={{ mt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Son Durum: {latestStep.step}
        </Typography>
        {latestStep.details && Object.keys(latestStep.details).length > 0 && (
          <Box sx={{ mt: 0.5 }}>
            {Object.entries(latestStep.details).slice(0, 2).map(([key, value]) => (
              <Typography 
                key={key} 
                variant="caption" 
                display="block"
                sx={{ color: 'text.secondary' }}
              >
                {key}: {value}
              </Typography>
            ))}
          </Box>
        )}
        <Typography variant="caption" color="text.secondary">
          {new Date(latestStep.timestamp).toLocaleTimeString('tr-TR')}
        </Typography>
      </Box>
    );
  };
  
  if (!isProcessing && processingSteps.length === 0) {
    return null;
  }
  
  return (
    <Paper elevation={2} sx={{ p: 3, mt: 2 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        🔄 İşlem Adımları
        {isProcessing && (
          <Chip 
            label="İşleniyor" 
            size="small" 
            color="primary" 
            variant="outlined"
          />
        )}
      </Typography>
      
      <Stepper activeStep={activeStep} orientation="vertical">
        {PROCESS_STEPS.map((step, index) => {
          const status = getStepStatus(step);
          const isActive = index === activeStep;
          
          return (
            <Step key={step.id} completed={status === 'completed'}>
              <StepLabel
                StepIconComponent={() => getStepIcon(step, status)}
                error={status === 'error'}
              >
                <Box>
                  <Typography 
                    variant="subtitle2" 
                    sx={{ 
                      fontWeight: isActive ? 600 : 400,
                      color: status === 'error' ? 'error.main' : 
                             status === 'completed' ? 'success.main' :
                             isActive ? 'primary.main' : 'text.primary'
                    }}
                  >
                    {step.label}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {step.description}
                  </Typography>
                </Box>
              </StepLabel>
              
              <StepContent>
                {getStepDetails(step)}
              </StepContent>
            </Step>
          );
        })}
      </Stepper>
      
      {/* Genel durum */}
      <Box sx={{ mt: 2, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary">
          <strong>Toplam Adım:</strong> {processingSteps.length} | 
          <strong> Durum:</strong> {
            PROCESS_STEPS.some(step => getStepStatus(step) === 'error') ? ' ❌ Hata' :
            PROCESS_STEPS.every(step => getStepStatus(step) === 'completed') ? ' ✅ Tamamlandı' :
            isProcessing ? ' 🔄 İşleniyor' : ' ⏸️ Beklemede'
          }
        </Typography>
      </Box>
    </Paper>
  );
};

export default ProcessingStepper; 
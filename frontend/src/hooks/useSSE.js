import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const useSSE = (user) => {
  const [processingSteps, setProcessingSteps] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef(null);
  const [connectionError, setConnectionError] = useState(null);

  // Processing step'i ekle
  const addProcessingStep = useCallback((step, details = {}) => {
    const newStep = {
      id: Date.now(),
      step,
      details,
      timestamp: new Date().toISOString(),
      status: 'completed'
    };
    
    setProcessingSteps(prev => [...prev, newStep]);
  }, []);

  // Processing step'leri temizle
  const clearProcessingSteps = useCallback(() => {
    setProcessingSteps([]);
  }, []);

  // SSE bağlantısını başlat
  const connect = useCallback(() => {
    if (!user || eventSourceRef.current) {
      return; // Zaten bağlı veya user yok
    }

    console.log('🔌 SSE bağlantısı kuruluyor...');

    try {
      const eventSource = new EventSource(`${API_BASE_URL}/sse/stream`, {
        withCredentials: true
      });

      eventSource.onopen = () => {
        console.log('✅ SSE bağlantısı açıldı');
        setIsConnected(true);
        setConnectionError(null);
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 SSE mesajı alındı:', data);

          switch (data.type) {
            case 'connected':
              console.log('🔗 SSE bağlantısı onaylandı:', data.data.message);
              break;

            case 'processing_step':
              addProcessingStep(data.data.step, data.data.details);
              break;

            case 'processing_complete':
              addProcessingStep('İşlem Tamamlandı', {
                result: data.data.decision || 'Başarılı',
                status: data.data.status
              });
              console.log('✅ İşlem tamamlandı:', data.data);
              break;

            case 'processing_error':
              addProcessingStep('Hata Oluştu', {
                error: data.data.error,
                status: 'error'
              });
              console.error('❌ İşlem hatası:', data.data.error);
              break;

            case 'document_uploaded':
              addProcessingStep('Belge Yüklendi', {
                document_id: data.data.document_id,
                filename: data.data.filename
              });
              break;

            case 'keepalive':
              // Keepalive mesajları için özel işlem yapma
              break;

            default:
              console.log('🔍 Bilinmeyen SSE mesajı:', data);
          }
        } catch (error) {
          console.error('❌ SSE mesaj parse hatası:', error, event.data);
        }
      };

      eventSource.onerror = (error) => {
        console.error('❌ SSE bağlantı hatası:', error);
        setIsConnected(false);
        setConnectionError('Bağlantı hatası oluştu');
        
        // Bağlantıyı kapat
        eventSource.close();
        eventSourceRef.current = null;
        
        // 3 saniye sonra yeniden bağlanmayı dene
        setTimeout(() => {
          if (user) {
            console.log('🔄 SSE yeniden bağlanma deneniyor...');
            connect();
          }
        }, 3000);
      };

      eventSourceRef.current = eventSource;

    } catch (error) {
      console.error('❌ SSE başlatma hatası:', error);
      setConnectionError('Bağlantı başlatılamadı');
    }
  }, [user, addProcessingStep]);

  // SSE bağlantısını kapat
  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      console.log('🔌 SSE bağlantısı kapatılıyor...');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  // User değiştiğinde bağlantıyı yönet
  useEffect(() => {
    if (user) {
      connect();
    } else {
      disconnect();
    }

    // Cleanup function
    return () => {
      disconnect();
    };
  }, [user, connect, disconnect]);

  // Component unmount olduğunda bağlantıyı kapat
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    processingSteps,
    isConnected,
    connectionError,
    clearProcessingSteps,
    addProcessingStep, // Manuel step ekleme için
    connect,
    disconnect
  };
}; 
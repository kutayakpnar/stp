import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging():
    """
    Logging konfigürasyonu - hem terminale hem dosyaya yazar
    """
    # Log dizinini oluştur
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Log dosyası adı (günlük)
    log_filename = f"{log_dir}/stp_system_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Root logger'ı ayarla
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Formatter - detaylı log formatı
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (terminale yazma) - mevcut davranış
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler (dosyaya yazma) - YENİ
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_filename,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler'ları ekle (mevcut handler'ları temizle önce)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Uvicorn logger'larını da aynı şekilde ayarla
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    
    # FastAPI request logger'ı özelleştir
    logging.getLogger("app").setLevel(logging.INFO)
    
    return log_filename

def log_document_processing_start(user_id: int, document_name: str):
    """
    Belge işleme başlangıcını logla
    """
    logger = logging.getLogger("app.document_processing")
    logger.info("="*80)
    logger.info(f"🚀 YENİ BELGE İŞLEME BAŞLADI")
    logger.info(f"👤 Kullanıcı ID: {user_id}")
    logger.info(f"📄 Belge Adı: {document_name}")
    logger.info(f"⏰ Başlangıç Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)

def log_processing_step(step_name: str, details: dict = None):
    """
    İşleme adımını logla
    """
    logger = logging.getLogger("app.processing_steps")
    logger.info(f"📍 ADIM: {step_name}")
    if details:
        for key, value in details.items():
            logger.info(f"   └── {key}: {value}")

def log_document_processing_end(user_id: int, decision: str, processing_time: float):
    """
    Belge işleme sonucunu logla
    """
    logger = logging.getLogger("app.document_processing")
    logger.info("="*80)
    logger.info(f"🏁 BELGE İŞLEME TAMAMLANDI")
    logger.info(f"👤 Kullanıcı ID: {user_id}")
    logger.info(f"✅ Karar: {decision}")
    logger.info(f"⏱️ Toplam Süre: {processing_time:.2f} saniye")
    logger.info(f"⏰ Bitiş Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)

def log_error(error_location: str, error_message: str, user_id: int = None):
    """
    Hata durumlarını özel olarak logla
    """
    logger = logging.getLogger("app.errors")
    logger.error("❌ HATA OLUŞTU!")
    logger.error(f"📍 Konum: {error_location}")
    logger.error(f"💬 Hata: {error_message}")
    if user_id:
        logger.error(f"👤 Kullanıcı ID: {user_id}")
    logger.error("-"*40) 
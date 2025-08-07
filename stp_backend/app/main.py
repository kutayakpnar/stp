from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.endpoints import document, user, sse
from app.db.base_class import Base
from app.db.session import engine
import logging

# Logging'i başlat - uygulama başlarken
log_filename = setup_logging()

# Logger'ı al ve sistem başlatma mesajını logla
logger = logging.getLogger("app.startup")
logger.info("🔧 STP Banking System başlatılıyor...")
logger.info(f"📝 Log dosyası: {log_filename}")

# Create database tables
Base.metadata.create_all(bind=engine)
logger.info("🗄️ Veritabanı tabloları oluşturuldu")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url="/api/v1/openapi.json"
)

# CORS ayarları
origins = [
    "http://localhost",
    "http://localhost:5173",  # Vite default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("🌐 CORS middleware konfigüre edildi")

# API routes
app.include_router(user.router, prefix="/api/v1/users", tags=["users"])
app.include_router(document.router, prefix="/api/v1", tags=["documents"])
app.include_router(sse.router, prefix="/api/v1/sse", tags=["real-time"])

logger.info("🚀 API routes yüklendi - Sistem hazır!")
logger.info("📡 SSE endpoint: /api/v1/sse/stream") 
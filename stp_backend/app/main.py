from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
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

# Custom OpenAPI schema function
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="🏦 STP Banking System API",
        version=settings.app_version,
        description="""
## 🚀 AI-Powered Banking STP System

Bu API, bankacılık süreçlerinde müşteri talimatlarını yapay zeka ile otomatik işler.

**Özellikler:** PDF/JPG/PNG belge işleme, OCR, NLP analizi, otomatik karar verme, gerçek zamanlı takip

**Teknoloji:** FastAPI, PostgreSQL, OpenAI GPT-4o, Tesseract OCR, JWT Auth, SSE
        """,
        routes=app.routes,
        tags=[
            {
                "name": "users",
                "description": "👤 Kullanıcı yönetimi - Kayıt, giriş, kimlik doğrulama"
            },
            {
                "name": "documents", 
                "description": "📄 Belge işleme - Dosya yükleme, OCR, NLP analizi, karar verme"
            },
            {
                "name": "real-time",
                "description": "📡 Gerçek zamanlı iletişim - Server-Sent Events"
            }
        ],
        contact={
            "name": "STP Banking System",
            "email": "support@stpbanking.com",
            "url": "https://github.com/kutayakpnar/stp"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "Development Server"
            }
        ]
    )
    
    # Security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "cookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "JWT token stored in HttpOnly cookie"
        }
    }
    
    # Global security requirement
    openapi_schema["security"] = [{"cookieAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="🏦 STP Banking System",
    version=settings.app_version,
    description="AI-Powered Banking Document Processing System",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set custom OpenAPI schema
app.openapi = custom_openapi

# CORS ayarları
origins = [
    "http://localhost",
    "http://localhost:5173",  # Vite default port
    "http://localhost:3000",  # React default port
    "https://stpbanking.com", # Production frontend (if exists)
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

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """API ana sayfası - Sistem bilgileri ve bağlantılar"""
    return {
        "message": "🏦 STP Banking System API",
        "version": settings.app_version,
        "status": "🟢 Aktif",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "frontend_url": "http://localhost:5173",
        "features": [
            "📄 AI-Powered Document Processing",
            "👁️ OCR Text Extraction", 
            "🧠 NLP Analysis with GPT-4o",
            "⚖️ Automated Decision Making",
            "📡 Real-time Updates via SSE",
            "🔐 JWT Authentication"
        ]
    }

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Sistem sağlık kontrolü"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "timestamp": "2024-01-01T00:00:00Z"
    }

logger.info("🚀 API routes yüklendi - Sistem hazır!")
logger.info("📡 SSE endpoint: /api/v1/sse/stream")
logger.info("📚 API Documentation: http://localhost:8000/docs")
logger.info("📖 ReDoc Documentation: http://localhost:8000/redoc") 
# 🐳 STP Banking System - Docker Setup

Bu dokümantasyon, STP Banking System'i Docker ile nasıl çalıştıracağınızı açıklar.

## 📋 Gereksinimler

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **Make** (opsiyonel, kolaylık için)
- En az **4GB RAM**
- En az **10GB disk alanı**

## 🚀 Hızlı Başlangıç

### 1. Repository'yi Klonlayın
```bash
git clone https://github.com/kutayakpnar/stp.git
cd stp
```

### 2. Environment Dosyasını Ayarlayın
```bash
cp .env.example .env
# .env dosyasını düzenleyin ve OpenAI API key'inizi ekleyin
```

### 3. Sistemi Başlatın
```bash
make up
# veya
docker-compose up -d
```

### 4. Servislere Erişin
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432

## 🛠️ Make Komutları

```bash
make help          # Tüm komutları göster
make build         # Docker image'larını build et
make up            # Servisleri başlat
make down          # Servisleri durdur
make restart       # Servisleri yeniden başlat
make logs          # Tüm logları göster
make logs-backend  # Backend loglarını göster
make logs-frontend # Frontend loglarını göster
make logs-db       # Database loglarını göster
make shell-backend # Backend container'ına gir
make shell-db      # Database container'ına gir
make clean         # Docker kaynaklarını temizle
make health        # Servislerin sağlığını kontrol et
```

## 🏗️ Servis Detayları

### 🔧 Backend (FastAPI)
- **Port**: 8000
- **Technology**: Python 3.11, FastAPI, SQLAlchemy
- **Features**: OCR, NLP, JWT Auth, SSE
- **Health Check**: `/health`

### ⚛️ Frontend (React)
- **Port**: 3000
- **Technology**: React, Vite, Material-UI, Nginx
- **Features**: Document upload, Real-time updates
- **Health Check**: `/health`

### 🗄️ Database (PostgreSQL)
- **Port**: 5432
- **Version**: PostgreSQL 15
- **User**: postgres
- **Password**: mysecretpassword
- **Database**: postgres

### 🔄 Redis (Opsiyonel)
- **Port**: 6379
- **Version**: Redis 7
- **Usage**: Caching, Session storage

## 📊 Monitoring ve Logs

### Log Görüntüleme
```bash
# Tüm servislerin logları
docker-compose logs -f

# Belirli bir servisin logları
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Health Check
```bash
# Manuel health check
curl http://localhost:8000/health
curl http://localhost:3000/health

# Make ile
make health
```

### Servis Durumu
```bash
docker-compose ps
# veya
make status
```

## 🔒 Güvenlik

### Production'da Değiştirilmesi Gerekenler
1. **JWT Secret Key** - `.env` dosyasında
2. **Database Password** - `docker-compose.yml` içinde
3. **SSL Sertifikaları** - Nginx için
4. **OpenAI API Key** - `.env` dosyasında

### Güvenlik Özellikleri
- Non-root user kullanımı
- Health check'ler
- Security headers (Nginx)
- Environment variable'lar
- Volume permissions

## 🧪 Test Etme

```bash
# Backend testleri
make test
# veya
docker-compose exec backend python -m pytest

# Manuel test
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'
```

## 🔧 Geliştirme

### Development Mode
```bash
# Development environment
docker-compose -f docker-compose.dev.yml up

# Hot reload için volume mount
# docker-compose.dev.yml dosyasında source code mount edilir
```

### Debug
```bash
# Backend container'ına gir
make shell-backend

# Database'e bağlan
make shell-db

# Log dosyalarını kontrol et
docker-compose exec backend ls -la logs/
```

## 🗄️ Database İşlemleri

### Backup
```bash
make backup-db
# veya
docker-compose exec postgres pg_dump -U postgres postgres > backup.sql
```

### Restore
```bash
make restore-db BACKUP=backup.sql
# veya
docker-compose exec -T postgres psql -U postgres -d postgres < backup.sql
```

### Migration
```bash
# Alembic migration
docker-compose exec backend alembic upgrade head
```

## 🐛 Troubleshooting

### Yaygın Sorunlar

1. **Port çakışması**
   ```bash
   # Portları değiştir docker-compose.yml'de
   ports:
     - "8001:8000"  # Backend
     - "3001:3000"  # Frontend
   ```

2. **Disk alanı**
   ```bash
   # Docker kaynaklarını temizle
   make clean
   docker system df  # Disk kullanımını kontrol et
   ```

3. **Memory sorunu**
   ```bash
   # Container resource limit'leri ekle
   deploy:
     resources:
       limits:
         memory: 512M
   ```

4. **Database bağlantı sorunu**
   ```bash
   # Database'in hazır olmasını bekle
   docker-compose logs postgres
   docker-compose exec postgres pg_isready -U postgres
   ```

### Log Analizi
```bash
# Error logları filtrele
docker-compose logs backend | grep ERROR

# Belirli tarih aralığı
docker-compose logs --since="2024-01-01" --until="2024-01-02"
```

## 📈 Production Deployment

### Production Compose
```bash
# Production profili ile başlat
make prod-up
# veya
docker-compose --profile production up -d
```

### Nginx Load Balancer
Production ortamında Nginx reverse proxy kullanılır:
- SSL termination
- Static file serving
- Load balancing
- GZIP compression

### Environment Konfigürasyonu
```bash
# Production .env
NODE_ENV=production
DATABASE_URL=postgresql://user:password@db-host:5432/db
OPENAI_API_KEY=your-production-key
SECRET_KEY=your-super-secure-secret
```

## 📞 Destek

Sorun yaşıyorsanız:
1. Bu README'yi kontrol edin
2. GitHub Issues'a bakın
3. Yeni issue açın

## 📝 Lisans

MIT License - Detaylar için `LICENSE` dosyasını inceleyin. 
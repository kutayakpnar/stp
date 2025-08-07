from datetime import datetime, timedelta
from jose import jwt
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def create_access_token(data: dict) -> str:
    """JWT token oluştur"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token oluşturma hatası: {str(e)}")
        raise

def verify_token(token: str) -> dict:
    """JWT token doğrula ve payload'ı döndür"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token süresi dolmuş")
        raise ValueError("Token süresi dolmuş")
    except jwt.JWTError as e:
        logger.error(f"Token doğrulama hatası: {str(e)}")
        raise ValueError("Geçersiz token")
    except Exception as e:
        logger.error(f"Beklenmeyen token hatası: {str(e)}")
        raise ValueError("Token işleme hatası") 
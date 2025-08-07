from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.user_service import create_user, authenticate_user, get_user_by_username
from app.services.jwt_service import create_access_token
from app.schemas.user import UserCreate, User, UserLogin, UserResponse
from app.dependencies import get_current_user
from app.models.user import User as UserModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/register", 
    response_model=UserResponse,
    summary="👤 Yeni Kullanıcı Kaydı",
    description="Sisteme yeni kullanıcı kaydı. Email, şifre ve tam ad gereklidir.",
    responses={
        201: {
            "description": "Kullanıcı başarıyla oluşturuldu",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "email": "kullanici@example.com",
                        "full_name": "John Doe"
                    }
                }
            }
        },
        400: {
            "description": "Kayıt hatası - Email zaten kullanımda",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Kullanıcı kaydı başarısız. Email zaten kullanımda olabilir."
                    }
                }
            }
        }
    }
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Yeni kullanıcı kaydı"""
    try:
        return create_user(db, user)
    except Exception as e:
        logger.error(f"Kullanıcı kaydı hatası: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Kullanıcı kaydı başarısız. Kullanıcı adı veya email zaten kullanımda olabilir."
        )

@router.post(
    "/login",
    summary="🔐 Kullanıcı Girişi",
    description="Email ve şifre ile giriş. Başarılı giriş sonrası JWT token cookie olarak ayarlanır.",
    responses={
        200: {
            "description": "Başarılı giriş",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": 1,
                            "email": "kullanici@example.com",
                            "full_name": "John Doe"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Giriş başarısız - Yanlış bilgiler"
        }
    }
)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Kullanıcı girişi ve token oluşturma"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Token oluştur
    access_token = create_access_token(
        data={"sub": user.username}
    )
    
    # Token'ı HttpOnly cookie olarak ayarla
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,  # Production'da True yapılmalı
        samesite="lax",
        max_age=1800  # 30 dakika
    )
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@router.post(
    "/logout",
    summary="🚪 Çıkış Yap",
    description="Kullanıcı oturumunu sonlandırır ve JWT token'ı siler.",
    responses={
        200: {
            "description": "Başarılı çıkış"
        }
    }
)
async def logout(response: Response):
    """Kullanıcı çıkışı"""
    response.delete_cookie(key="access_token")
    return {"message": "Başarıyla çıkış yapıldı"}

@router.get(
    "/me", 
    response_model=UserResponse,
    summary="👤 Mevcut Kullanıcı Bilgileri",
    description="Oturum açmış kullanıcının bilgilerini getirir. JWT token gereklidir.",
    responses={
        200: {
            "description": "Kullanıcı bilgileri"
        },
        401: {
            "description": "Kimlik doğrulama hatası"
        }
    }
)
async def read_users_me(
    current_user: UserModel = Depends(get_current_user)
):
    """Mevcut kullanıcı bilgilerini getir"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name
    } 
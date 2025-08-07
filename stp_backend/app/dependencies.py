from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import OAuth2PasswordBearer
from app.services.jwt_service import verify_token
from app.services.user_service import get_user_by_username
from sqlalchemy.orm import Session
from app.db.session import get_db
import logging
from typing import Optional

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/login", auto_error=False)

async def get_token_from_cookie(
    request: Request,
    access_token: Optional[str] = Cookie(None)
) -> Optional[str]:
    """Cookie'den token'ı al"""
    if access_token and access_token.startswith('Bearer '):
        return access_token.split(' ')[1]
    return None

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    cookie_token: Optional[str] = Depends(get_token_from_cookie),
    db: Session = Depends(get_db)
):
    """Token'dan mevcut kullanıcıyı getir"""
    # Önce cookie'den token'ı kontrol et, yoksa header'dan al
    final_token = cookie_token or token
    
    if not final_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kimlik doğrulama gerekli",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_token(final_token)
        username: str = payload.get("sub")
        if username is None:
            raise ValueError("Token içeriği geçersiz")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bulunamadı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user 
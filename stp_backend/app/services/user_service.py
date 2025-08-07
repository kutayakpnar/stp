from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
import hashlib
import logging

logger = logging.getLogger(__name__)

def get_password_hash(password: str) -> str:
    """Basit SHA-256 hash"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifre doğrulama"""
    return get_password_hash(plain_password) == hashed_password

def get_user_by_username(db: Session, username: str) -> User:
    """Kullanıcı adına göre kullanıcı getir"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> User:
    """Email'e göre kullanıcı getir"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    """Yeni kullanıcı oluştur"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Yeni kullanıcı oluşturuldu: {user.username}")
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Kullanıcı oluşturma hatası: {str(e)}")
        raise

def authenticate_user(db: Session, username: str, password: str) -> User:
    """Kullanıcı girişi doğrulama"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user 
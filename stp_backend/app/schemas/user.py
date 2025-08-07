from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    username: Optional[str] = None  # Email adresi username olarak kullanılacak

    def __init__(self, **data):
        super().__init__(**data)
        if self.username is None:
            self.username = self.email

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True 
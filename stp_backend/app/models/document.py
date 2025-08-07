from sqlalchemy import Column, Integer, String, DateTime, Text, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_content = Column(LargeBinary, nullable=True)  # Dosya içeriği
    file_size = Column(Integer, nullable=True)  # Dosya boyutu (bytes)
    raw_text = Column(Text, nullable=True)  # OCR'dan çıkan ham metin
    extracted_data = Column(Text, nullable=True)  # JSON formatında çıkarılan veriler
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to users table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    decisions = relationship("Decision", back_populates="document") 
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, types
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime
import json

class JSONType(types.TypeDecorator):
    impl = types.JSON
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            # JSON'u string'e çevirirken Türkçe karakterleri koru
            return json.dumps(value, ensure_ascii=False)
        return value

class Decision(Base):
    __tablename__ = "decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Decision Results
    decision = Column(String(20), nullable=False, index=True)  # APPROVED, REJECTED, MANUAL_REVIEW, PENDING
    confidence = Column(Float, default=0.0)
    decision_reasons = Column(JSONType)  # JSON array of reasons
    required_actions = Column(JSONType)  # JSON array of required actions
    next_steps = Column(JSONType)  # JSON array of next steps
    estimated_processing_time = Column(String(50))
    
    # Document Analysis
    document_type = Column(String(50), index=True)  # eft_form, loan_application, etc.
    intent = Column(String(200))
    priority = Column(String(10), default="NORMAL")  # LOW, NORMAL, HIGH, URGENT
    
    # Risk Assessment
    risk_level = Column(String(20), index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors = Column(JSONType)  # JSON array of risk factors
    fraud_indicators = Column(JSONType)  # JSON array of fraud indicators
    compliance_check = Column(String(10), default="UNKNOWN")  # PASS, FAIL, UNKNOWN
    
    # Validation Results
    tckn_valid = Column(String(10), default="UNKNOWN")  # VALID, INVALID, UNKNOWN
    iban_valid = Column(String(10), default="UNKNOWN")  # VALID, INVALID, UNKNOWN
    amount_valid = Column(String(10), default="UNKNOWN")  # VALID, INVALID, UNKNOWN
    date_valid = Column(String(10), default="UNKNOWN")  # VALID, INVALID, UNKNOWN
    validation_confidence = Column(Float, default=0.0)
    
    # Transaction Details (extracted)
    customer_name = Column(String(200))
    customer_tckn = Column(String(11))
    sender_iban = Column(String(32))
    receiver_iban = Column(String(32))
    transaction_amount = Column(Float)
    transaction_currency = Column(String(3), default="TL")
    transaction_type = Column(String(50))
    
    # Processing Info
    processing_time = Column(Float)  # seconds
    ocr_confidence = Column(Float)
    nlp_confidence = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Manual Review Info
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Reviewer user ID
    review_date = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    final_decision = Column(String(20), nullable=True)  # Manual override
    
    # Relationships
    document = relationship("Document", back_populates="decisions")
    user = relationship("User", foreign_keys=[user_id], back_populates="decisions")
    reviewer = relationship("User", foreign_keys=[reviewed_by]) 
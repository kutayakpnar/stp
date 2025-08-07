from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class DocumentType(str, Enum):
    EFT_FORM = "eft_form"
    LOAN_APPLICATION = "loan_application"
    ACCOUNT_OPENING = "account_opening"
    COMPLAINT = "complaint"
    OTHER = "other"

class Priority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"

class Customer(BaseModel):
    name: Optional[str] = None
    tckn: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    birth_date: Optional[str] = None
    monthly_income: Optional[float] = None

class Account(BaseModel):
    iban: Optional[str] = None
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None

class Transaction(BaseModel):
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = "TL"
    transaction_date: Optional[str] = None
    description: Optional[str] = None

class Loan(BaseModel):
    loan_amount: Optional[float] = None
    loan_term: Optional[int] = None
    loan_purpose: Optional[str] = None
    interest_rate: Optional[float] = None
    monthly_installment: Optional[float] = None

class DocumentAnalysis(BaseModel):
    document_type: Optional[DocumentType] = DocumentType.OTHER
    confidence: float = 0.0
    intent: Optional[str] = None
    priority: Priority = Priority.NORMAL

class Validation(BaseModel):
    tckn_valid: bool = False
    iban_valid: bool = False
    amount_valid: bool = False
    date_valid: bool = False
    confidence_score: float = 0.0

class ExtractedEntities(BaseModel):
    customer: Customer = Customer()
    sender_account: Optional[Account] = None
    receiver_account: Optional[Account] = None
    transaction: Optional[Transaction] = None
    loan: Optional[Loan] = None
    document_analysis: DocumentAnalysis = DocumentAnalysis()
    validation: Validation = Validation()

class NLPAnalysisResult(BaseModel):
    success: bool = False
    message: str = ""
    entities: Optional[ExtractedEntities] = None
    processing_time: float = 0.0 
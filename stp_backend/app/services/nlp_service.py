import openai
import json
import logging
import time
from typing import Dict, Any, Optional
from app.core.config import settings
from app.schemas.nlp import NLPAnalysisResult, ExtractedEntities

logger = logging.getLogger(__name__)

class NLPService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        
    def analyze_document(self, text: str, document_id: Optional[int] = None) -> NLPAnalysisResult:
        """
        Ana belge analiz fonksiyonu
        OCR'dan gelen metni GPT ile analiz eder ve structured output döner
        """
        start_time = time.time()
        
        try:
            logger.info(f"Document {document_id} için NLP analizi başlıyor...")
            
            # GPT ile entity extraction
            entities = self._extract_entities_with_gpt(text)
            
            processing_time = time.time() - start_time
            
            result = NLPAnalysisResult(
                success=True,
                message="Belge analizi başarıyla tamamlandı",
                entities=entities,
                processing_time=processing_time
            )
            
            logger.info(f"Document {document_id} NLP analizi tamamlandı. Süre: {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"NLP analizi hatası: {e}")
            return NLPAnalysisResult(
                success=False,
                message=f"Analiz hatası: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    def _extract_entities_with_gpt(self, text: str) -> ExtractedEntities:
        """GPT-4o mini ile entity extraction"""
        
        system_prompt = """
Sen bir Türk bankacılık uzmanısın. Verilen belgedeki bilgileri çıkarıp JSON formatında döndürmelisin.

Çıkaracağın bilgiler:
1. Müşteri bilgileri (ad, TCKN, telefon, email, adres, doğum tarihi, aylık gelir)
2. Hesap bilgileri (gönderici ve alıcı IBAN, hesap no, banka adı, hesap sahibi)
3. İşlem bilgileri (tür, tutar, para birimi, tarih, açıklama)
4. Kredi bilgileri (tutar, vade, amaç, faiz oranı, taksit, teminat)
5. Belge tipi ve müşteri niyeti

ÖNEMLI:
- Birden fazla IBAN varsa gönderici/alıcı olarak ayır
- Tutarları sadece sayısal değer olarak ver (1000.50 formatında)
- Tarihleri YYYY-MM-DD formatında ver
- TCKN'leri 11 haneli kontrol et
- Belirsiz bilgileri null olarak bırak

Türkçe bankacılık terimleri:
- "hesabımızdan" = gönderici hesap
- "hesabına" = alıcı hesap  
- "nolu hesaba" = alıcı hesap
- "tutarını" = işlem tutarı
- "aktarmak" = para transferi
"""

        user_prompt = f"""
Aşağıdaki bankacılık belgesini analiz et ve JSON formatında döndür:

BELGE METNİ:
{text}

JSON formatı şu şekilde olmalı:
{{
  "customer": {{
    "name": "string veya null",
    "tckn": "string veya null", 
    "phone": "string veya null",
    "email": "string veya null",
    "address": "string veya null",
    "birth_date": "YYYY-MM-DD veya null",
    "monthly_income": number veya null
  }},
  "sender_account": {{
    "iban": "string veya null",
    "account_number": "string veya null", 
    "bank_name": "string veya null",
    "account_holder": "string veya null"
  }},
  "receiver_account": {{
    "iban": "string veya null",
    "account_number": "string veya null",
    "bank_name": "string veya null", 
    "account_holder": "string veya null"
  }},
  "transaction": {{
    "transaction_type": "eft|wire_transfer|loan_payment|deposit|withdrawal|other",
    "amount": number veya null,
    "currency": "TL|USD|EUR",
    "transaction_date": "YYYY-MM-DD veya null",
    "description": "string veya null"
  }},
  "loan": {{
    "loan_amount": number veya null,
    "loan_term": number veya null,
    "loan_purpose": "string veya null",
    "interest_rate": number veya null,
    "monthly_installment": number veya null
  }},
  "document_analysis": {{
    "document_type": "eft_form|loan_application|account_opening|complaint|other",
    "confidence": number (0-100),
    "intent": "string",
    "priority": "LOW|NORMAL|HIGH|URGENT"
  }}
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Düşük temperature = daha tutarlı sonuçlar
                max_tokens=2000,
                response_format={"type": "json_object"}  # Structured output
            )
            
            content = response.choices[0].message.content
            logger.info(f"GPT yanıtı alındı: {len(content)} karakter")
            
            # JSON parse et
            parsed_data = json.loads(content)
            logger.info(f"Parsed data: {parsed_data}")
            
            # Pydantic model'e çevir
            entities = ExtractedEntities(**parsed_data)
            
            return entities
            
        except json.JSONDecodeError as e:
            logger.error(f"GPT JSON parse hatası: {e}")
            return ExtractedEntities()
            
        except Exception as e:
            logger.error(f"GPT API hatası: {e}")
            return ExtractedEntities()

nlp_service = NLPService() 
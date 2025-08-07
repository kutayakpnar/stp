import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.decision import Decision
from app.services.validation_service import validation_service
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class DecisionService:
    
    def make_decision(self, parsed_data: Dict[Any, Any]) -> Dict[str, Any]:
        """
        NLP'den gelen verilere göre karar ver - Sadece APPROVED veya REJECTED
        """
        try:
            # Validation service'i kullanarak verileri doğrula
            validation = validation_service.validate_data(parsed_data)
            
            # Varsayılan değerler
            decision = "REJECTED"
            confidence = 0.0
            reasons = []
            
            document_type = parsed_data.get("document_analysis", {}).get("document_type", "").lower()
            intent = parsed_data.get("document_analysis", {}).get("intent", "").lower()
            
            # Belge tipini intent'ten de anlamaya çalış
            combined_text = f"{document_type} {intent}".lower()
            
            # EFT/Para transferi belgeleri
            if any(keyword in combined_text for keyword in ["eft", "transfer", "aktarım", "havale", "para", "ödeme"]):
                # Temel bilgi kontrolü
                sender_iban = parsed_data.get("sender_account", {}).get("iban")
                receiver_iban = parsed_data.get("receiver_account", {}).get("iban")
                amount = parsed_data.get("transaction", {}).get("amount")
                
                if sender_iban and receiver_iban and amount:
                    # Validation skoruna göre karar ver
                    if validation["validation_score"] >= 60:  # %60 ve üzeri onay
                        decision = "APPROVED"
                        confidence = validation["validation_score"]
                        reasons.append("Para transferi onaylandı")
                        reasons.append(f"Validation skoru: %{validation['validation_score']:.1f}")
                        
                        # Hangi validasyonlar geçti
                        if validation["tckn_valid"]:
                            reasons.append("TCKN doğrulandı")
                        if validation["iban_valid"]:
                            reasons.append("IBAN'lar doğrulandı")
                        if validation["amount_valid"]:
                            reasons.append("İşlem tutarı geçerli")
                    else:
                        # %60'ın altı red
                        decision = "REJECTED"
                        confidence = validation["validation_score"]
                        reasons.append("Para transferi reddedildi")
                        reasons.append(f"Validation skoru yetersiz: %{validation['validation_score']:.1f}")
                        
                        # Hangi validasyonlar başarısız
                        if not validation["tckn_valid"]:
                            reasons.append("TCKN doğrulanamadı")
                        if not validation["iban_valid"]:
                            reasons.append("IBAN doğrulanamadı")
                        if not validation["amount_valid"]:
                            reasons.append("İşlem tutarı geçersiz")
                else:
                    reasons.append("Eksik transfer bilgileri")
                    reasons.append("IBAN veya tutar bilgisi eksik")
            
            # Kredi başvuruları
            elif any(keyword in combined_text for keyword in ["kredi", "loan", "başvuru", "application"]) and "limit" not in combined_text:
                customer_name = parsed_data.get("customer", {}).get("name")
                monthly_income = parsed_data.get("customer", {}).get("monthly_income")
                loan_amount = parsed_data.get("loan", {}).get("loan_amount")
                
                if customer_name and loan_amount:
                    # Kredi başvurusu temel kriterleri
                    if loan_amount <= 5000000:  # 5M TL altı
                        if monthly_income and monthly_income > 0:
                            # DTI (Debt-to-Income) hesabı
                            max_loan = monthly_income * 60  # 60 aylık maaş
                            if loan_amount <= max_loan:
                                decision = "APPROVED"
                                confidence = 85.0
                                reasons.append("Kredi başvurusu onaylandı")
                                reasons.append(f"Kredi tutarı: {loan_amount:,.0f} TL")
                                reasons.append(f"Aylık gelir: {monthly_income:,.0f} TL")
                                reasons.append("Gelir/kredi oranı uygun")
                            else:
                                decision = "REJECTED"
                                confidence = 30.0
                                reasons.append("Kredi başvurusu reddedildi")
                                reasons.append("Talep edilen tutar gelire göre yüksek")
                                reasons.append(f"Maksimum kredi: {max_loan:,.0f} TL")
                        else:
                            # Gelir bilgisi yoksa varsayılan değerlendirme
                            if loan_amount <= 100000:  # 100K altı düşük riskli
                                decision = "APPROVED"
                                confidence = 70.0
                                reasons.append("Kredi başvurusu onaylandı")
                                reasons.append("Düşük tutarlı kredi başvurusu")
                            else:
                                decision = "REJECTED"
                                confidence = 40.0
                                reasons.append("Kredi başvurusu reddedildi")
                                reasons.append("Gelir bilgisi eksik ve yüksek tutar")
                    else:
                        decision = "REJECTED"
                        confidence = 20.0
                        reasons.append("Kredi başvurusu reddedildi")
                        reasons.append("Kredi tutarı limit aşımı (5M TL)")
                else:
                    decision = "REJECTED"
                    confidence = 10.0
                    reasons.append("Kredi başvurusu reddedildi")
                    reasons.append("Eksik müşteri bilgileri")
            
            # Limit arttırım talepleri
            elif any(keyword in combined_text for keyword in ["limit", "arttırım", "artırım", "increase"]):
                customer_name = parsed_data.get("customer", {}).get("name")
                monthly_income = parsed_data.get("customer", {}).get("monthly_income")
                
                if "kredi" in combined_text:
                    # Kredi limit arttırımı
                    requested_amount = parsed_data.get("loan", {}).get("loan_amount") or parsed_data.get("transaction", {}).get("amount")
                    
                    if customer_name:
                        if requested_amount and requested_amount <= 2000000:  # 2M TL altı
                            if monthly_income and monthly_income >= 15000:  # 15K+ maaş
                                decision = "APPROVED"
                                confidence = 80.0
                                reasons.append("Kredi limit artırımı onaylandı")
                                reasons.append(f"Talep edilen limit: {requested_amount:,.0f} TL")
                                reasons.append("Gelir durumu uygun")
                            else:
                                decision = "REJECTED"
                                confidence = 35.0
                                reasons.append("Kredi limit artırımı reddedildi")
                                reasons.append("Gelir durumu yetersiz (min 15K TL)")
                        else:
                            decision = "REJECTED"
                            confidence = 25.0
                            reasons.append("Kredi limit artırımı reddedildi")
                            reasons.append("Talep edilen tutar yüksek (max 2M TL)")
                    else:
                        decision = "REJECTED"
                        confidence = 15.0
                        reasons.append("Kredi limit artırımı reddedildi")
                        reasons.append("Müşteri bilgileri eksik")
                        
                else:
                    # EFT/Transfer limit arttırımı
                    requested_amount = parsed_data.get("transaction", {}).get("amount") or 50000  # Varsayılan
                    
                    if customer_name:
                        if requested_amount <= 500000:  # 500K TL altı EFT limiti
                            decision = "APPROVED"
                            confidence = 75.0
                            reasons.append("Transfer limit artırımı onaylandı")
                            reasons.append(f"Yeni transfer limiti: {requested_amount:,.0f} TL")
                            reasons.append("Standart limit artırımı")
                        else:
                            decision = "REJECTED"
                            confidence = 30.0
                            reasons.append("Transfer limit artırımı reddedildi")
                            reasons.append("Talep edilen limit yüksek (max 500K TL)")
                    else:
                        decision = "REJECTED"
                        confidence = 20.0
                        reasons.append("Transfer limit artırımı reddedildi")
                        reasons.append("Müşteri bilgileri eksik")
            
            else:
                # Eğer hiçbir kategori bulunamazsa, veriler var mı kontrol et
                sender_iban = parsed_data.get("sender_account", {}).get("iban")
                receiver_iban = parsed_data.get("receiver_account", {}).get("iban")
                amount = parsed_data.get("transaction", {}).get("amount")
                
                if sender_iban and receiver_iban and amount:
                    # IBAN ve tutar varsa para transferi olarak değerlendir
                    if validation["validation_score"] >= 60:
                        decision = "APPROVED"
                        confidence = validation["validation_score"]
                        reasons.append("Bankacılık işlemi onaylandı")
                        reasons.append("Transfer bilgileri tespit edildi")
                    else:
                        decision = "REJECTED"
                        confidence = validation["validation_score"]
                        reasons.append("Bankacılık işlemi reddedildi")
                        reasons.append("Validation skoru yetersiz")
                else:
                    reasons.append("Bilinmeyen belge tipi")
                    reasons.append(f"Tespit edilen: {document_type}")
                    reasons.append(f"Niyet: {intent}")
                    reasons.append("Desteklenen: Transfer, Kredi, Limit Artırımı")
            
            return {
                "decision": decision,
                "confidence": confidence,
                "reasons": reasons,
                "validation": validation
            }
            
        except Exception as e:
            logger.error(f"Karar verme hatası: {e}")
            return {
                "decision": "REJECTED",
                "confidence": 0.0,
                "reasons": [f"Sistem hatası: {str(e)}"],
                "validation": {"validation_score": 0}
            }
    
    def save_decision(
        self, 
        db: Session, 
        parsed_data: Dict[Any, Any],
        decision_data: Dict[str, Any],
        document_id: int,
        user_id: int,
        ocr_confidence: float = 0.0
    ) -> Decision:
        """
        Kararı veritabanına kaydet
        """
        try:
            # JSON verilerini düzgün encode et
            def encode_json_data(data):
                if isinstance(data, (dict, list)):
                    return json.loads(json.dumps(data, ensure_ascii=False))
                return data
            
            # Karar kaydı oluştur
            decision = Decision(
                document_id=document_id,
                user_id=user_id,
                
                # Karar sonucu
                decision=decision_data["decision"],
                confidence=decision_data["confidence"],
                decision_reasons=encode_json_data(decision_data["reasons"]),
                
                # Validation sonuçları
                tckn_valid="VALID" if decision_data.get("validation", {}).get("tckn_valid") else "INVALID",
                iban_valid="VALID" if decision_data.get("validation", {}).get("iban_valid") else "INVALID",
                amount_valid="VALID" if decision_data.get("validation", {}).get("amount_valid") else "INVALID",
                validation_confidence=decision_data.get("validation", {}).get("validation_score", 0),
                
                # Belge analizi
                document_type=parsed_data["document_analysis"]["document_type"],
                intent=parsed_data["document_analysis"]["intent"],
                priority=parsed_data["document_analysis"]["priority"],
                
                # İşlem detayları
                customer_name=parsed_data["customer"]["name"],
                customer_tckn=parsed_data["customer"]["tckn"],
                sender_iban=parsed_data["sender_account"]["iban"],
                receiver_iban=parsed_data["receiver_account"]["iban"],
                transaction_amount=parsed_data["transaction"]["amount"],
                transaction_currency=parsed_data["transaction"]["currency"],
                transaction_type=parsed_data["transaction"]["transaction_type"],
                
                # İşlem bilgileri
                processing_time=0.0,  # Bu alan artık kullanılmıyor
                ocr_confidence=ocr_confidence,
                nlp_confidence=parsed_data["document_analysis"]["confidence"]
            )
            
            db.add(decision)
            db.commit()
            db.refresh(decision)
            
            logger.info(f"Decision kaydedildi: ID {decision.id}, Decision: {decision.decision}")
            return decision
            
        except Exception as e:
            logger.error(f"Decision kaydetme hatası: {e}")
            db.rollback()
            raise
    
    def get_user_decisions(
        self, 
        db: Session, 
        user_id: int, 
        limit: int = 100, 
        offset: int = 0
    ):
        """
        Kullanıcının kararlarını getir
        """
        return (
            db.query(Decision)
            .filter(Decision.user_id == user_id)
            .order_by(Decision.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

decision_service = DecisionService() 
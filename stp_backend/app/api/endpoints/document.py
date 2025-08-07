from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.services.ocr_service import ocr_service
from app.services.nlp_service import nlp_service
from app.services.decision_service import decision_service
from app.dependencies import get_current_user
from app.core.logging_config import (
    log_document_processing_start, 
    log_processing_step, 
    log_document_processing_end,
    log_error
)
from app.core.sse_manager import sse_manager
from PIL import Image
import io
import logging
from datetime import datetime
import json
import time
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process-document/")
async def process_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        # İşleme başlangıcını logla
        log_document_processing_start(current_user.id, file.filename)
        
        # SSE: İşlem başlangıcı
        await sse_manager.send_processing_step(
            current_user.id, 
            "İşlem Başlatıldı", 
            {"filename": file.filename}
        )
        
        logger.info(f"Dosya işleme başlatıldı: {file.filename}")
        
        # Kısa delay - UI için gerçekçi görünüm
        await asyncio.sleep(0.5)
        
        # Dosya içeriğini oku
        file_content = await file.read()
        
        # SSE: Dosya okuma
        await sse_manager.send_processing_step(
            current_user.id, 
            "Dosya Okundu", 
            {
                "size": f"{len(file_content)} bytes",
                "type": file.content_type
            }
        )
        
        log_processing_step("Dosya Okuma", {
            "Dosya Adı": file.filename,
            "Dosya Boyutu": f"{len(file_content)} bytes",
            "İçerik Tipi": file.content_type
        })
        
        # Kısa delay
        await asyncio.sleep(0.3)
        
        # Dosya tipini kontrol et
        if not file.content_type:
            await sse_manager.send_processing_error(current_user.id, "Dosya tipi belirlenemedi")
            log_error("Dosya Tipi Kontrolü", "Dosya tipi belirlenemedi", current_user.id)
            raise HTTPException(status_code=400, detail="Dosya tipi belirlenemedi")
        
        # Desteklenen dosya tiplerini kontrol et
        supported_types = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
        if file.content_type not in supported_types:
            await sse_manager.send_processing_error(
                current_user.id, 
                f"Desteklenmeyen dosya tipi: {file.content_type}"
            )
            log_error("Dosya Tipi Kontrolü", f"Desteklenmeyen dosya tipi: {file.content_type}", current_user.id)
            raise HTTPException(
                status_code=400, 
                detail=f"Desteklenmeyen dosya tipi: {file.content_type}. Desteklenen tipler: {', '.join(supported_types)}"
            )
        
        # SSE: Dosya tipi kontrolü
        await sse_manager.send_processing_step(
            current_user.id, 
            "Dosya Tipi Kontrolü", 
            {"result": "✅ Geçerli"}
        )
        
        log_processing_step("Dosya Tipi Kontrolü", {"Sonuç": "✅ Geçerli"})
        
        # Kısa delay
        await asyncio.sleep(0.4)
        
        # Dosyayı veritabanına kaydet
        try:
            db_document = Document(
                file_name=file.filename,
                file_type=file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown',
                content_type=file.content_type,
                file_content=file_content,
                file_size=len(file_content),
                status="processing",
                user_id=current_user.id,
                updated_at=datetime.utcnow()
            )
            
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            
            # SSE: Veritabanı kaydı
            await sse_manager.send_document_uploaded(
                current_user.id, 
                db_document.id, 
                file.filename
            )
            
            # Kısa delay
            await asyncio.sleep(0.3)
            
            await sse_manager.send_processing_step(
                current_user.id, 
                "Veritabanı Kaydı", 
                {"document_id": db_document.id}
            )
            
            log_processing_step("Veritabanı Kaydı", {
                "Document ID": db_document.id,
                "Durum": "✅ Başarılı"
            })
            
            logger.info(f"Dosya veritabanına kaydedildi. ID: {db_document.id}")
            
        except Exception as e:
            await sse_manager.send_processing_error(current_user.id, f"Veritabanı hatası: {str(e)}")
            log_error("Veritabanı Kaydı", str(e), current_user.id)
            logger.error(f"Veritabanı kayıt hatası: {e}")
            raise HTTPException(status_code=500, detail=f"Veritabanı kayıt hatası: {e}")
        
        # OCR işlemini gerçekleştir
        try:
            # SSE: OCR başlangıcı
            await sse_manager.send_processing_step(
                current_user.id, 
                "OCR İşlemi Başlatıldı", 
                {"file_type": file.content_type}
            )
            
            log_processing_step("OCR Başlatılıyor", {"İşlenen Dosya": file.content_type})
            
            # OCR için gerçekçi delay (1-2 saniye)
            await asyncio.sleep(1.5)
            
            if file.content_type == "application/pdf":
                # PDF için OCR
                raw_text = ocr_service.extract_text_from_pdf(file_content)
            else:
                # Görüntü için OCR
                image = Image.open(io.BytesIO(file_content))
                raw_text = ocr_service.extract_text_from_image(image, "banking_document")
            
            # SSE: OCR tamamlandı
            await sse_manager.send_processing_step(
                current_user.id, 
                "OCR Tamamlandı", 
                {
                    "text_length": len(raw_text),
                    "preview": raw_text[:100] + "..." if len(raw_text) > 100 else raw_text
                }
            )
            
            log_processing_step("OCR Tamamlandı", {
                "Çıkarılan Metin Uzunluğu": f"{len(raw_text)} karakter",
                "İlk 100 Karakter": raw_text[:100] + "..." if len(raw_text) > 100 else raw_text
            })
            
            logger.info("OCR işlemi tamamlandı, NLP analizi başlıyor...")
            
            # Kısa delay
            await asyncio.sleep(0.5)
            
            # NLP analizi yap
            # SSE: NLP başlangıcı
            await sse_manager.send_processing_step(
                current_user.id, 
                "NLP Analizi Başlatıldı", 
                {"text_length": len(raw_text)}
            )
            
            log_processing_step("NLP Analizi Başlatılıyor", {"Metin Uzunluğu": len(raw_text)})
            
            # NLP için gerçekçi delay (2-3 saniye)
            await asyncio.sleep(2.0)
            
            nlp_result = nlp_service.analyze_document(raw_text, db_document.id)
            
            # SSE: NLP tamamlandı
            await sse_manager.send_processing_step(
                current_user.id, 
                "NLP Analizi Tamamlandı", 
                {
                    "success": nlp_result.success,
                    "document_type": nlp_result.entities.document_analysis.document_type if nlp_result.success else "N/A",
                    "intent": nlp_result.entities.document_analysis.intent if nlp_result.success else "N/A",
                    "processing_time": f"{nlp_result.processing_time:.2f}s"
                }
            )
            
            log_processing_step("NLP Analizi Tamamlandı", {
                "Başarılı": "✅" if nlp_result.success else "❌",
                "Belge Tipi": nlp_result.entities.document_analysis.document_type if nlp_result.success else "N/A",
                "Niyet": nlp_result.entities.document_analysis.intent if nlp_result.success else "N/A",
                "İşlem Süresi": f"{nlp_result.processing_time:.2f}s"
            })
            
            # Kısa delay
            await asyncio.sleep(0.7)
            
            # OCR ve NLP sonuçlarını veritabanında güncelle
            db_document.raw_text = raw_text
            
            # Decision'ı ayrı tabloya kaydet
            decision_record = None
            if nlp_result.success:
                extracted_data = {
                    "nlp_analysis": nlp_result.dict(),
                    "ocr_confidence": getattr(raw_text, 'confidence', 0),
                    "processing_time": nlp_result.processing_time
                }
                db_document.extracted_data = json.dumps(extracted_data, ensure_ascii=False, default=str)
                db_document.status = "completed"
                
                # Karar ver ve kaydet
                try:
                    # SSE: Karar verme başlangıcı
                    await sse_manager.send_processing_step(
                        current_user.id, 
                        "Karar Verme Başlatıldı", 
                        {
                            "customer": nlp_result.entities.customer.name if nlp_result.entities.customer else "N/A",
                            "amount": nlp_result.entities.transaction.amount if nlp_result.entities.transaction else "N/A"
                        }
                    )
                    
                    log_processing_step("Karar Verme Süreci Başlatılıyor", {
                        "Müşteri": nlp_result.entities.customer.name if nlp_result.entities.customer else "N/A",
                        "TCKN": nlp_result.entities.customer.tckn if nlp_result.entities.customer else "N/A",
                        "Tutar": nlp_result.entities.transaction.amount if nlp_result.entities.transaction else "N/A"
                    })
                    
                    # Karar verme için gerçekçi delay (1 saniye)
                    await asyncio.sleep(1.0)
                    
                    parsed_data = nlp_result.entities.dict()
                    decision_data = decision_service.make_decision(parsed_data)
                    
                    ocr_confidence = getattr(raw_text, 'confidence', 0)
                    decision_record = decision_service.save_decision(
                        db=db,
                        parsed_data=parsed_data,
                        decision_data=decision_data,
                        document_id=db_document.id,
                        user_id=current_user.id,
                        ocr_confidence=ocr_confidence
                    )
                    
                    # SSE: Karar tamamlandı
                    await sse_manager.send_processing_step(
                        current_user.id, 
                        "Karar Verme Tamamlandı", 
                        {
                            "decision": decision_data["decision"],
                            "confidence": f"{decision_data['confidence']:.1f}%",
                            "validation_score": f"{decision_data['validation']['validation_score']:.1f}%",
                            "reasons_count": len(decision_data["reasons"])
                        }
                    )
                    
                    log_processing_step("Karar Verme Tamamlandı", {
                        "Decision ID": decision_record.id,
                        "Karar": decision_data["decision"],
                        "Güven Skoru": f"{decision_data['confidence']:.1f}%",
                        "Validation Skoru": f"{decision_data['validation']['validation_score']:.1f}%",
                        "Sebepler": len(decision_data["reasons"])
                    })
                    
                    logger.info(f"Decision kaydedildi: ID {decision_record.id}")
                except Exception as e:
                    await sse_manager.send_processing_error(current_user.id, f"Karar verme hatası: {str(e)}")
                    log_error("Karar Verme", str(e), current_user.id)
                    logger.error(f"Decision kaydetme hatası: {e}")
                
                logger.info(f"NLP analizi başarılı: {nlp_result.entities.document_analysis.document_type}")
            else:
                db_document.status = "failed"
                await sse_manager.send_processing_error(current_user.id, nlp_result.message)
                log_error("NLP Analizi", nlp_result.message, current_user.id)
                logger.error(f"NLP analizi başarısız: {nlp_result.message}")
            
            db_document.updated_at = datetime.utcnow()
            db.commit()
            
            # Son delay - kullanıcının sonucu görmesi için
            await asyncio.sleep(0.5)
            
            # İşleme bitişini logla
            processing_time = time.time() - start_time
            final_decision = decision_record.decision if decision_record else "FAILED"
            log_document_processing_end(current_user.id, final_decision, processing_time)
            
            # Response hazırla
            response_data = {
                "document_id": db_document.id,
                "status": db_document.status,
                "message": "Belge başarıyla işlendi ve analiz edildi",
                "raw_text_length": len(raw_text),
                "nlp_analysis": nlp_result.dict() if nlp_result.success else None,
                "processing_time": nlp_result.processing_time,
                "decision_id": decision_record.id if decision_record else None,
                "decision": decision_record.decision if decision_record else None,
                "decision_confidence": decision_record.confidence if decision_record else None
            }
            
            # SSE: İşlem tamamlandı
            await sse_manager.send_processing_complete(current_user.id, response_data)
            
            return response_data
            
        except Exception as e:
            await sse_manager.send_processing_error(current_user.id, f"OCR/NLP hatası: {str(e)}")
            log_error("OCR/NLP İşlemi", str(e), current_user.id)
            logger.error(f"OCR/NLP işlemi hatası: {e}")
            # Hata durumunda status'ü güncelle
            db_document.status = "failed"
            db_document.updated_at = datetime.utcnow()
            db.commit()
            
            # Hata durumunda da süreyi logla
            processing_time = time.time() - start_time
            log_document_processing_end(current_user.id, "ERROR", processing_time)
            
            raise HTTPException(status_code=500, detail=f"Belge analizi hatası: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        await sse_manager.send_processing_error(current_user.id, f"Sistem hatası: {str(e)}")
        log_error("Genel Hata", str(e), current_user.id)
        logger.error(f"Genel hata: {e}")
        
        # Beklenmeyen hata durumunda da süreyi logla
        processing_time = time.time() - start_time
        log_document_processing_end(current_user.id, "SYSTEM_ERROR", processing_time)
        
        raise HTTPException(status_code=500, detail=f"İşlem hatası: {e}")

@router.post("/process-text/")
async def process_text(
    text: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        # SSE: Metin işleme başlangıcı
        await sse_manager.send_processing_step(
            current_user.id, 
            "Metin İşleme Başlatıldı", 
            {"text_length": len(text)}
        )
        
        logger.info("Metin işleme başlatıldı")
        
        if not text.strip():
            await sse_manager.send_processing_error(current_user.id, "Boş metin gönderilemez")
            raise HTTPException(status_code=400, detail="Boş metin gönderilemez")
        
        # Kısa delay
        await asyncio.sleep(0.3)
        
        # Metni veritabanına kaydet
        try:
            # SSE: Veritabanı kaydı başlangıcı
            await sse_manager.send_processing_step(
                current_user.id, 
                "Metin Veritabanına Kaydediliyor", 
                {"size": f"{len(text.encode('utf-8'))} bytes"}
            )
            
            db_document = Document(
                file_name="text_input.txt",
                file_type="txt",
                content_type="text/plain",
                file_content=text.encode('utf-8'),
                file_size=len(text.encode('utf-8')),
                raw_text=text,
                status="processing",
                user_id=current_user.id,
                updated_at=datetime.utcnow()
            )
            
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            
            # SSE: Veritabanı kaydı tamamlandı
            await sse_manager.send_processing_step(
                current_user.id, 
                "Veritabanı Kaydı Tamamlandı", 
                {"document_id": db_document.id}
            )
            
            logger.info(f"Metin veritabanına kaydedildi. ID: {db_document.id}")
            
        except Exception as e:
            await sse_manager.send_processing_error(current_user.id, f"Veritabanı hatası: {str(e)}")
            logger.error(f"Veritabanı kayıt hatası: {e}")
            raise HTTPException(status_code=500, detail=f"Veritabanı kayıt hatası: {e}")
        
        # Kısa delay
        await asyncio.sleep(0.5)
        
        # NLP analizi yap
        try:
            # SSE: NLP başlangıcı
            await sse_manager.send_processing_step(
                current_user.id, 
                "NLP Analizi Başlatıldı", 
                {"text_length": len(text)}
            )
            
            logger.info("NLP analizi başlıyor...")
            
            # NLP için gerçekçi delay (1.5 saniye)
            await asyncio.sleep(1.5)
            
            nlp_result = nlp_service.analyze_document(text, db_document.id)
            
            # SSE: NLP tamamlandı
            await sse_manager.send_processing_step(
                current_user.id, 
                "NLP Analizi Tamamlandı", 
                {
                    "success": nlp_result.success,
                    "document_type": nlp_result.entities.document_analysis.document_type if nlp_result.success else "N/A",
                    "intent": nlp_result.entities.document_analysis.intent if nlp_result.success else "N/A",
                    "processing_time": f"{nlp_result.processing_time:.2f}s"
                }
            )
            
            # Kısa delay
            await asyncio.sleep(0.5)
            
            # Decision'ı ayrı tabloya kaydet
            decision_record = None
            if nlp_result.success:
                extracted_data = {
                    "nlp_analysis": nlp_result.dict(),
                    "processing_time": nlp_result.processing_time
                }
                db_document.extracted_data = json.dumps(extracted_data, ensure_ascii=False, default=str)
                db_document.status = "completed"
                
                # Karar ver ve kaydet
                try:
                    # SSE: Karar verme başlangıcı
                    await sse_manager.send_processing_step(
                        current_user.id, 
                        "Karar Verme Başlatıldı", 
                        {
                            "customer": nlp_result.entities.customer.name if nlp_result.entities.customer else "N/A",
                            "amount": nlp_result.entities.transaction.amount if nlp_result.entities.transaction else "N/A"
                        }
                    )
                    
                    # Karar verme için delay
                    await asyncio.sleep(0.8)
                    
                    parsed_data = nlp_result.entities.dict()
                    decision_data = decision_service.make_decision(parsed_data)
                    
                    decision_record = decision_service.save_decision(
                        db=db,
                        parsed_data=parsed_data,
                        decision_data=decision_data,
                        document_id=db_document.id,
                        user_id=current_user.id,
                        ocr_confidence=100.0  # Text input için %100
                    )
                    
                    # SSE: Karar tamamlandı
                    await sse_manager.send_processing_step(
                        current_user.id, 
                        "Karar Verme Tamamlandı", 
                        {
                            "decision": decision_data["decision"],
                            "confidence": f"{decision_data['confidence']:.1f}%",
                            "validation_score": f"{decision_data['validation']['validation_score']:.1f}%",
                            "reasons_count": len(decision_data["reasons"])
                        }
                    )
                    
                    logger.info(f"Decision kaydedildi: ID {decision_record.id}")
                except Exception as e:
                    await sse_manager.send_processing_error(current_user.id, f"Karar verme hatası: {str(e)}")
                    logger.error(f"Decision kaydetme hatası: {e}")
                
                logger.info(f"NLP analizi başarılı: {nlp_result.entities.document_analysis.document_type}")
            else:
                db_document.status = "failed"
                await sse_manager.send_processing_error(current_user.id, nlp_result.message)
                logger.error(f"NLP analizi başarısız: {nlp_result.message}")
            
            db_document.updated_at = datetime.utcnow()
            db.commit()
            
            # Son delay
            await asyncio.sleep(0.3)
            
            # İşleme bitişini logla
            processing_time = time.time() - start_time
            final_decision = decision_record.decision if decision_record else "FAILED"
            log_document_processing_end(current_user.id, final_decision, processing_time)
            
            # Response hazırla
            response_data = {
                "document_id": db_document.id,
                "status": db_document.status,
                "message": "Metin başarıyla analiz edildi",
                "raw_text_length": len(text),
                "nlp_analysis": nlp_result.dict() if nlp_result.success else None,
                "processing_time": nlp_result.processing_time,
                "decision_id": decision_record.id if decision_record else None,
                "decision": decision_record.decision if decision_record else None,
                "decision_confidence": decision_record.confidence if decision_record else None
            }
            
            # SSE: İşlem tamamlandı
            await sse_manager.send_processing_complete(current_user.id, response_data)
            
            return response_data
            
        except Exception as e:
            await sse_manager.send_processing_error(current_user.id, f"NLP hatası: {str(e)}")
            logger.error(f"NLP analizi hatası: {e}")
            # Hata durumunda status'ü güncelle
            db_document.status = "failed"
            db_document.updated_at = datetime.utcnow()
            db.commit()
            
            # Hata durumunda da süreyi logla
            processing_time = time.time() - start_time
            log_document_processing_end(current_user.id, "ERROR", processing_time)
            
            raise HTTPException(status_code=500, detail=f"Metin analizi hatası: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        await sse_manager.send_processing_error(current_user.id, f"Sistem hatası: {str(e)}")
        logger.error(f"Genel hata: {e}")
        
        # Beklenmeyen hata durumunda da süreyi logla
        processing_time = time.time() - start_time
        log_document_processing_end(current_user.id, "SYSTEM_ERROR", processing_time)
        
        raise HTTPException(status_code=500, detail=f"İşlem hatası: {e}")

@router.get("/decisions/")
async def get_user_decisions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """Kullanıcının kararlarını getir"""
    decisions = decision_service.get_user_decisions(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    return {
        "decisions": [
            {
                "id": d.id,
                "document_id": d.document_id,
                "decision": d.decision,
                "confidence": d.confidence,
                "document_type": d.document_type,
                "intent": d.intent,
                "risk_level": d.risk_level,
                "risk_factors": d.risk_factors,
                "transaction_amount": d.transaction_amount,
                "transaction_currency": d.transaction_currency,
                "customer_name": d.customer_name,
                "customer_tckn": d.customer_tckn,
                "decision_reasons": d.decision_reasons,
                "created_at": d.created_at,
                "processing_time": d.processing_time
            }
            for d in decisions
        ],
        "total": len(decisions)
    }

@router.get("/document/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Belgeyi veritabanından al
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Belge bulunamadı veya erişim izniniz yok")
    
    # Extracted data'yı parse et
    extracted_data = None
    if document.extracted_data:
        try:
            extracted_data = json.loads(document.extracted_data)
        except json.JSONDecodeError:
            logger.warning(f"Document {document_id} extracted_data parse edilemedi")
    
    return {
        "id": document.id,
        "file_name": document.file_name,
        "file_type": document.file_type,
        "content_type": document.content_type,
        "file_size": document.file_size,
        "raw_text": document.raw_text,
        "extracted_data": extracted_data,
        "status": document.status,
        "created_at": document.created_at,
        "updated_at": document.updated_at
    }

@router.get("/document/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Belgeyi veritabanından al
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Belge bulunamadı veya erişim izniniz yok")
    
    if not document.file_content:
        raise HTTPException(status_code=404, detail="Dosya içeriği bulunamadı")
    
    # Dosyayı stream olarak döndür
    def generate():
        yield document.file_content
    
    return StreamingResponse(
        generate(),
        media_type=document.content_type,
        headers={"Content-Disposition": f"attachment; filename={document.file_name}"}
    ) 
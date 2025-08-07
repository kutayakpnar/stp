import asyncio
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import Request

logger = logging.getLogger(__name__)

class SSEManager:
    def __init__(self):
        # Aktif bağlantıları store et: {user_id: [connection1, connection2, ...]}
        self.connections: Dict[int, List[asyncio.Queue]] = {}
        self.lock = asyncio.Lock()
    
    async def connect(self, user_id: int) -> asyncio.Queue:
        """Yeni SSE bağlantısı oluştur"""
        async with self.lock:
            queue = asyncio.Queue()
            
            if user_id not in self.connections:
                self.connections[user_id] = []
            
            self.connections[user_id].append(queue)
            logger.info(f"SSE bağlantısı açıldı: User {user_id}, Total: {len(self.connections[user_id])}")
            
            return queue
    
    async def disconnect(self, user_id: int, queue: asyncio.Queue):
        """SSE bağlantısını kapat"""
        async with self.lock:
            if user_id in self.connections:
                try:
                    self.connections[user_id].remove(queue)
                    if not self.connections[user_id]:
                        del self.connections[user_id]
                    logger.info(f"SSE bağlantısı kapatıldı: User {user_id}")
                except ValueError:
                    pass
    
    async def send_update(self, user_id: int, event_type: str, data: dict):
        """Kullanıcıya real-time update gönder"""
        if user_id not in self.connections:
            logger.debug(f"User {user_id} için aktif SSE bağlantısı yok")
            return
        
        # Event formatı
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # JSON serialize et
        message = json.dumps(event, ensure_ascii=False)
        
        # Aktif bağlantılara gönder
        async with self.lock:
            connections = self.connections.get(user_id, []).copy()
        
        for queue in connections:
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"SSE message gönderme hatası: {e}")
                # Hatalı bağlantıyı temizle
                await self.disconnect(user_id, queue)
        
        logger.debug(f"SSE update gönderildi: User {user_id}, Event: {event_type}")
    
    async def send_processing_step(self, user_id: int, step: str, details: dict = None):
        """İşlem adımı update'i gönder"""
        await self.send_update(user_id, "processing_step", {
            "step": step,
            "details": details or {}
        })
    
    async def send_processing_complete(self, user_id: int, result: dict):
        """İşlem tamamlanma update'i gönder"""
        await self.send_update(user_id, "processing_complete", result)
    
    async def send_processing_error(self, user_id: int, error: str):
        """İşlem hata update'i gönder"""
        await self.send_update(user_id, "processing_error", {
            "error": error
        })
    
    async def send_document_uploaded(self, user_id: int, document_id: int, filename: str):
        """Belge yükleme update'i gönder"""
        await self.send_update(user_id, "document_uploaded", {
            "document_id": document_id,
            "filename": filename
        })
    
    def get_connection_count(self, user_id: int) -> int:
        """Kullanıcının aktif bağlantı sayısını döndür"""
        return len(self.connections.get(user_id, []))
    
    def get_total_connections(self) -> int:
        """Toplam aktif bağlantı sayısını döndür"""
        return sum(len(queues) for queues in self.connections.values())

# Global SSE manager instance
sse_manager = SSEManager() 
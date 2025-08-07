from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.dependencies import get_current_user
from app.models.user import User
from app.core.sse_manager import sse_manager
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stream")
async def stream_updates(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Server-Sent Events endpoint for real-time updates
    """
    async def event_stream():
        # SSE bağlantısı oluştur
        queue = await sse_manager.connect(current_user.id)
        
        try:
            logger.info(f"SSE stream başlatıldı: User {current_user.id}")
            
            # İlk bağlantı mesajı gönder
            initial_message = {
                "type": "connected",
                "timestamp": "2024-01-01T00:00:00",
                "data": {
                    "message": "Real-time bağlantı kuruldu",
                    "user_id": current_user.id
                }
            }
            
            yield f"data: {str(initial_message).replace('{', '{{').replace('}', '}}')}\n\n"
            
            while True:
                # Client bağlantısı koptu mu kontrol et
                if await request.is_disconnected():
                    logger.info(f"Client bağlantısı koptu: User {current_user.id}")
                    break
                
                try:
                    # Queue'dan mesaj bekle (timeout ile)
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {message}\n\n"
                    
                except asyncio.TimeoutError:
                    # Keepalive mesajı gönder
                    yield f"data: {{'type': 'keepalive', 'timestamp': '2024-01-01T00:00:00'}}\n\n"
                    
        except Exception as e:
            logger.error(f"SSE stream hatası: {e}")
            
        finally:
            # Bağlantıyı temizle
            await sse_manager.disconnect(current_user.id, queue)
            logger.info(f"SSE stream kapatıldı: User {current_user.id}")
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    ) 
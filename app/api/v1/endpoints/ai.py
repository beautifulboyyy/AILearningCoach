from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.services.ai_service import ai_service
from app.schemas.ai import ChatRequest

router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        ai_service.get_chat_response(
            query=request.message,
            history=request.history,
            user_context=request.user_context
        ),
        media_type="text/event-stream"
    )

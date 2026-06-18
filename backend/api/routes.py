from fastapi import APIRouter

from backend.models import ChatRequest, ChatResponse
from backend.core.chatbot import CustomerSupportBot
from backend.core.config import settings

router = APIRouter()

bot = CustomerSupportBot(settings.LOG_FILE)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    return bot.process(request.user_id, request.message)

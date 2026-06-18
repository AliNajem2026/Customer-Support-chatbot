from fastapi import FastAPI
from backend.api.routes import router

app = FastAPI(
    title="Customer Support Chatbot",
    description="Multilingual AI customer support API — English & Arabic",
    version="1.0.0"
)

app.include_router(router)

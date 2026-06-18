import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "vectorstore/faiss_index")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/interactions.csv")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")


settings = Settings()

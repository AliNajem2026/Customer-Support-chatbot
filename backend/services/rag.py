from backend.vectorstore.faiss_store import FaissStore
from backend.core.config import settings


class RAGService:

    def __init__(self):
        self.store = FaissStore(settings.FAISS_INDEX_PATH)

    def retrieve(self, query: str) -> str:
        docs = self.store.search(query)
        return "\n\n".join([doc.page_content for doc in docs])

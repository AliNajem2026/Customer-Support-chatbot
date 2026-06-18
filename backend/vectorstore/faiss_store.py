from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


class FaissStore:

    def __init__(self, path: str):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.db = FAISS.load_local(
            path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )

    def search(self, query: str, k: int = 3):
        return self.db.similarity_search(query, k=k)

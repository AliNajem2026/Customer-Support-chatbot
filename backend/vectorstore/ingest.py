from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings


def ingest(
    knowledge_base_dir: str = "knowledge_base",
    index_path: str = "vectorstore/faiss_index"
):
    docs = []
    root = Path(knowledge_base_dir)

    for file in root.rglob("*.txt"):
        loader = TextLoader(str(file), encoding="utf-8")
        docs.extend(loader.load())

    if not docs:
        raise ValueError(f"No .txt files found in '{knowledge_base_dir}/'")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(index_path)

    print(f"Ingested {len(docs)} documents -> {len(chunks)} chunks -> saved to '{index_path}'")


if __name__ == "__main__":
    ingest()

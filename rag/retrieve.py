"""
RAG RETRIEVAL
=============
Given a user's question, finds the most relevant pieces of "knowledge"
(built in ingest.py) from the Chroma vector database. This context is
handed to the LLM so it writes more accurate pandas code — e.g. it knows
the exact column name to use instead of guessing.
"""

import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "dataset_knowledge"


def retrieve_context(question: str, top_k: int = 3) -> str:
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=embed_fn)
    except Exception:
        return "No knowledge base found yet. Upload a CSV first."

    results = collection.query(query_texts=[question], n_results=top_k)
    matched_docs = results["documents"][0]
    return "\n".join(matched_docs)
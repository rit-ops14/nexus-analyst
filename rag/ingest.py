"""
RAG INGESTION
=============
Turns useful "knowledge" about the dataset — column names, types, sample
values, and any human-written notes — into a searchable vector database
(ChromaDB).

Why bother if the MCP tool `describe_dataframe` already gives the schema?
Because RAG lets the agent search for only the RELEVANT bits of knowledge
for a given question, instead of stuffing the entire schema (and, later,
things like a data dictionary or past Q&A history) into every prompt.
That's the core idea of Retrieval-Augmented Generation: retrieve first,
then generate.
"""

import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "dataset_knowledge"


def build_knowledge_base(csv_path: str, data_dictionary: dict[str, str] | None = None):
    """
    Reads the CSV, turns each column into a short text "document"
    (name + type + sample values + optional human description), and
    stores it in Chroma so the agent can later ask:
    "which columns are relevant to this question?"
    """
    df = pd.read_csv(csv_path)

    # Free, local embedding model — no API key required, great for students.
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Start fresh every time a new file is uploaded, so old columns
    # from a previous dataset don't leak into the new one.
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=embed_fn)

    documents, ids = [], []
    for i, col in enumerate(df.columns):
        description = (data_dictionary or {}).get(col, "No description provided.")
        sample_values = df[col].dropna().unique()[:3].tolist()

        doc = (
            f"Column name: {col}. "
            f"Data type: {df[col].dtype}. "
            f"Example values: {sample_values}. "
            f"Description: {description}"
        )
        documents.append(doc)
        ids.append(f"col_{i}")

    collection.add(documents=documents, ids=ids)
    return collection
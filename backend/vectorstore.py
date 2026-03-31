"""
vectorstore.py
--------------
Chunks parsed PDF pages and stores them.
Each upload gets its own collection keyed by job_id.
"""

import os
from typing import List, Dict, Any
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_store")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBED_MODEL = "nomic-embed-text"


def _get_embeddings():
    return OllamaEmbeddings(model=EMBED_MODEL)


def build_vectorstore(job_id: str, pages: List[Dict[str, Any]]) -> Chroma:
    """
    Takes parsed page data, chunks all text, embeds, and stores in Chroma.

    Args:
        job_id: Unique identifier for this upload session.
        pages: Output of parser.parse_pdf()

    Returns:
        Chroma vectorstore instance.
    """
    # Create client fresh in this process — avoids SQLite issues with forked workers
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks = []
    all_metadatas = []

    for page in pages:
        page_num = page["page_num"]

        if page["text"].strip():
            chunks = splitter.split_text(page["text"])
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadatas.append({"page": page_num, "type": "text"})

        for t_idx, table in enumerate(page.get("tables", [])):
            table_text = _table_to_text(table)
            if table_text.strip():
                all_chunks.append(table_text)
                all_metadatas.append({
                    "page": page_num,
                    "type": "table",
                    "table_index": t_idx,
                })

    if not all_chunks:
        raise ValueError("No extractable text found in the PDF.")

    embeddings = _get_embeddings()

    # Batch to avoid memory spikes on large contracts
    BATCH_SIZE = 25
    vs = None
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch_texts = all_chunks[i:i + BATCH_SIZE]
        batch_metas = all_metadatas[i:i + BATCH_SIZE]

        if vs is None:
            vs = Chroma.from_texts(
                texts=batch_texts,
                embedding=embeddings,
                metadatas=batch_metas,
                collection_name=job_id,
                client=chroma_client,
            )
        else:
            vs.add_texts(texts=batch_texts, metadatas=batch_metas)

    return vs


def get_vectorstore(job_id: str) -> Chroma:
    """
    Retrieve the vectorstore for a given job_id from disk.
    """
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    return Chroma(
        collection_name=job_id,
        embedding_function=_get_embeddings(),
        client=chroma_client,
    )


def _table_to_text(table: List[List[str]]) -> str:
    """
    Convert a table (list of rows) into a readable text representation.
    First row is treated as header if it looks like one.
    """
    if not table:
        return ""
    lines = []
    for row in table:
        lines.append(" | ".join(cell.strip() for cell in row if cell))
    return "\n".join(lines)
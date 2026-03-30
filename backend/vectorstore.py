"""
vectorstore.py
--------------
Chunks parsed PDF pages and stores them.
Each upload gets its own collection keyed by job_id.

"""

from typing import List, Dict, Any
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

_chroma_client = chromadb.Client()

_vectorstores: Dict[str, Chroma] = {}

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBED_MODEL = "nomic-embed-text" 


def _get_embeddings():
    """
    Returns OllamaEmbeddings using nomic-embed-text.
    Raises a clear error if Ollama isn't running or model isn't pulled.
    """
    return OllamaEmbeddings(model=EMBED_MODEL)


def build_vectorstore(job_id: str, pages: List[Dict[str, Any]]) -> Chroma:
    """
    Takes parsed page data, chunks all text, embeds, and stores in Chroma.

    Args:
        job_id: Unique identifier for this upload session.
        pages: Output of parser.parse_pdf()

    Returns:
        Chroma vectorstore instance (also stored in _vectorstores registry).
    """
    # Build flat list of text chunks with metadata
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks = []
    all_metadatas = []

    for page in pages:
        page_num = page["page_num"]

        # Chunk the main text
        if page["text"].strip():
            chunks = splitter.split_text(page["text"])
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadatas.append({"page": page_num, "type": "text"})

        # Add table content as concatenated text chunks
        for t_idx, table in enumerate(page.get("tables", [])):
            table_text = _table_to_text(table)
            if table_text.strip():
                # assume tables are short enough !!!
                all_chunks.append(table_text)
                all_metadatas.append({
                    "page": page_num,
                    "type": "table",
                    "table_index": t_idx,
                })

    if not all_chunks:
        raise ValueError("No extractable text found in the PDF.")

    embeddings = _get_embeddings()

    # Use job_id as the Chroma collection name (must be unique per upload)
    vs = Chroma.from_texts(
        texts=all_chunks,
        embedding=embeddings,
        metadatas=all_metadatas,
        collection_name=job_id,
        client=_chroma_client,
    )

    _vectorstores[job_id] = vs
    return vs


def get_vectorstore(job_id: str) -> Chroma:
    """
    Retrieve the vectorstore for a given job_id.
    Raises KeyError if the job hasn't been indexed yet.
    """
    if job_id not in _vectorstores:
        raise KeyError(f"No vectorstore found for job_id: {job_id}")
    return _vectorstores[job_id]


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

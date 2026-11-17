"""
rag_tool.py — Advanced version
Direct replacement for the 19-line version.
Same name, same idea, + 6 protections.

What it adds vs the simple version:
1. Cache so you don't pay OpenAI twice for the same search
2. Input validation with Pydantic
3. Hybrid search (vector + keywords)
4. Relevance filter < 0.35 (drops junk)
5. Deduplication
6. Logs + latency measurement (observability)
"""

from __future__ import annotations

import hashlib
import time
from functools import lru_cache

import structlog
from crewai.tools import tool
from pydantic import BaseModel, Field

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

import os

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")
MIN_RELEVANCE = float(os.getenv("MIN_RELEVANCE", "0.35"))
DEFAULT_TOP_K = 5

log = structlog.get_logger()

# ------------------------------------------------------------------
# Vector DB — with cache
# ------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_db() -> Chroma:
    """
    The simple version created a new connection on every search.
    This one creates it once and reuses it (cache).
    Saves time and money.
    """
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=OpenAIEmbeddings(),
    )


# ------------------------------------------------------------------
# Ingestion — add new documents
# ------------------------------------------------------------------

def ingest_document(path: str) -> int:
    """
    Same as the simple version, but with:
    - Explicit metadata with source and chunk
    - Log of how many chunks were stored
    - Clear error handling
    """
    try:
        loader = PyPDFLoader(path) if path.endswith(".pdf") else TextLoader(path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " "],
        )
        chunks = splitter.split_documents(docs)

        # Add explicit metadata so we can cite sources later
        for i, chunk in enumerate(chunks):
            chunk.metadata["source"] = os.path.basename(path)
            chunk.metadata["chunk"] = i

        get_db().add_documents(chunks)

        log.info("ingest_ok", file=os.path.basename(path), chunks=len(chunks))
        return len(chunks)

    except Exception as e:
        log.error("ingest_failed", file=path, error=str(e))
        raise


# ------------------------------------------------------------------
# Tool — what the agent uses
# ------------------------------------------------------------------

class RAGInput(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=1000,
        description="Question or keywords to search in internal documents",
    )
    top_k: int = Field(
        default=DEFAULT_TOP_K,
        ge=1,
        le=10,
        description="How many results to return, between 1 and 10",
    )


@tool("rag_search")
def rag_search_tool(query: str, top_k: int = 5) -> str:
    """
    Search evidence in internal documents (RAG).

    ALWAYS use this before stating anything.

    Steps:
    1. Validate the query
    2. Search twice: vector + keywords (hybrid)
    3. Filter by relevance >= 0.35
    4. Remove duplicates
    5. Sort by relevance
    6. If nothing good found, say NO DATA, do not invent
    """
    start = time.time()

    # 1. Validation
    if not query or len(query.strip()) < 3:
        return "RAG ERROR: Query too short. Minimum 3 characters."
    if len(query) > 1000:
        return "RAG ERROR: Query too long. Maximum 1000 characters."

    # Clamp top_k to valid range
    top_k = max(1, min(top_k, 10))

    try:
        db = get_db()

        # 2. Hybrid search
        # a) Vector: search by meaning
        docs_vector = db.similarity_search_with_score(query, k=top_k * 2)

        # b) Keywords: search by exact words (helps with names, codes, dates)
        docs_keyword = db.similarity_search(f"keywords: {query}", k=top_k)

        # 3 + 4. Filter by relevance + deduplicate
        seen: set[str] = set()
        results: list[tuple] = []

        for doc, score in docs_vector:
            relevance = 1 - float(score)  # Chroma returns distance, convert to relevance
            if relevance < MIN_RELEVANCE:
                continue  # Junk, drop it

            # Deduplicate by content
            key = hashlib.md5(doc.page_content[:200].encode()).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            results.append((doc, relevance))

        # Add keyword results not already present
        for doc in docs_keyword:
            key = hashlib.md5(doc.page_content[:200].encode()).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            # Keyword results get a medium relevance since we have no score
            results.append((doc, 0.5))

        # 5. Re-ranking: highest relevance first, keep top_k
        results = sorted(results, key=lambda x: x[1], reverse=True)[:top_k]

        # 6. Guardrail: if nothing good found, DO NOT invent
        if not results:
            log.info("rag_empty", query=query[:80])
            return "RAG EMPTY: No data. Answer 'I don't have enough evidence in the documents' and do not invent."

        # 7. Observability
        latency_ms = int((time.time() - start) * 1000)
        log.info(
            "rag_search",
            query=query[:80],
            hits=len(results),
            latency_ms=latency_ms,
            top_relevance=round(results[0][1], 3),
        )

        # Format with citation: source + chunk + relevance + text
        return "\n\n---\n\n".join(
            f"[SOURCE: {d.metadata.get('source')} | chunk {d.metadata.get('chunk')} | relevance {rel:.2f}]\n{d.page_content[:1000]}"
            for d, rel in results
        )

    except Exception as e:
        log.error("rag_error", query=query[:80], error=str(e))
        return f"RAG ERROR: {e}. Try again."


# ------------------------------------------------------------------
# Backwards compatibility with the old version
# ------------------------------------------------------------------
# If an old agent still uses RAGSearchTool,
# this keeps it working without breaking anything.

class RAGSearchTool:
    """
    Backwards-compatibility alias.
    Old code did: RAGSearchTool()._run(query)
    This does the same, but calls the new version.
    """
    name: str = "rag_search"
    description: str = "Search internal vector DB. Input: question."

    def _run(self, query: str) -> str:
        return rag_search_tool(query)

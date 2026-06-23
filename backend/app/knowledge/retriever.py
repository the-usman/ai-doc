"""A LangChain retriever backed by pgvector.

Wrapping our ``document_chunks`` similarity search as a ``BaseRetriever`` lets it
drop straight into LCEL chains (``retriever | prompt | model | parser``) exactly
as LangChain's own ``PGVector`` retriever would — but it reads from our schema's
table, so the documents↔chunks relationship and the ivfflat index defined in
``schema/schema.sql`` remain the source of truth. See ADR-008.
"""

from typing import Any

from app.config import get_settings
from app.knowledge import embeddings, persistence


def search_chunks(query: str, k: int | None = None, user_id: Any = None) -> list[dict]:
    """
    Embed a query and return the most similar chunks as plain dicts.

    Args:
        query: The natural-language query.
        k: Number of chunks to return; defaults to the configured ``rag_top_k``.
        user_id: Optional owner filter.

    Returns:
        Chunk dicts with ``chunk_text``, ``document_title``, ``chunk_index`` and
        ``similarity``, most similar first.
    """
    top_k = k if k is not None else get_settings().rag_top_k
    vector = embeddings.embed_query(query)
    return persistence.similarity_search(vector, k=top_k, user_id=user_id)


def get_retriever(k: int | None = None, user_id: Any = None) -> Any:
    """
    Build a LangChain ``BaseRetriever`` over the pgvector store.

    Args:
        k: Number of chunks to return per query.
        user_id: Optional owner filter applied to every query.

    Returns:
        A retriever whose ``invoke(query)`` returns LangChain ``Document`` objects
        carrying the chunk text and its source metadata.
    """
    from langchain_core.documents import Document
    from langchain_core.retrievers import BaseRetriever

    top_k = k if k is not None else get_settings().rag_top_k
    owner = user_id

    class PgVectorRetriever(BaseRetriever):
        """Retriever that runs a cosine search over ``document_chunks``."""

        def _get_relevant_documents(self, query: str, *, run_manager: Any = None) -> list:
            rows = search_chunks(query, k=top_k, user_id=owner)
            return [
                Document(
                    page_content=row["chunk_text"],
                    metadata={
                        "document_id": str(row["document_id"]),
                        "document_title": row["document_title"],
                        "chunk_index": row["chunk_index"],
                        "similarity": float(row["similarity"]),
                    },
                )
                for row in rows
            ]

    return PgVectorRetriever()

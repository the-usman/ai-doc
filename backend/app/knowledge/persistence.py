"""Persistence for documents and their embedded chunks.

Plain psycopg against the ``documents`` and ``document_chunks`` tables from
``schema/schema.sql`` — no LangChain dependency, so it is unit-tested directly
against PostgreSQL. We store embeddings in our own ``document_chunks`` table
(rather than letting a vector-store wrapper manage its own tables) so the schema
stays the single source of truth and the documents↔chunks foreign key is
preserved. See ADR-008.

pgvector accepts a bracketed string literal for ``vector`` values, so embeddings
are formatted with :func:`_vector_literal` and cast with ``%s::vector`` — no
extra adapter registration required.
"""

from typing import Any
from uuid import UUID

from app.db import get_connection


def _vector_literal(embedding: list[float]) -> str:
    """Format an embedding as the ``[1,2,3]`` literal pgvector expects."""
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


def create_document(
    user_id: UUID | str, title: str, source_name: str, raw_text: str
) -> dict[str, Any]:
    """
    Insert a document row and return it.

    Args:
        user_id: The owner of the document.
        title: Human-readable title supplied at upload.
        source_name: Original filename.
        raw_text: Full extracted text.

    Returns:
        The inserted document row (without chunk data).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (user_id, title, source_name, raw_text)
                VALUES (%s, %s, %s, %s)
                RETURNING id, user_id, title, source_name, created_at
                """,
                (str(user_id), title, source_name, raw_text),
            )
            row = cur.fetchone()
    if row is None:
        raise RuntimeError("create_document did not return a row")
    return dict(row)


def insert_chunks(document_id: UUID | str, chunks: list[dict[str, Any]]) -> int:
    """
    Bulk-insert embedded chunks for a document.

    Args:
        document_id: The parent document.
        chunks: Items with ``chunk_index``, ``chunk_text`` and ``embedding``
            (a list of floats).

    Returns:
        The number of chunks inserted.
    """
    if not chunks:
        return 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO document_chunks
                    (document_id, chunk_index, chunk_text, embedding)
                VALUES (%s, %s, %s, %s::vector)
                """,
                [
                    (
                        str(document_id),
                        chunk["chunk_index"],
                        chunk["chunk_text"],
                        _vector_literal(chunk["embedding"]),
                    )
                    for chunk in chunks
                ],
            )
    return len(chunks)


def list_documents(user_id: UUID | str | None = None) -> list[dict[str, Any]]:
    """
    List documents with their chunk counts, newest first.

    Args:
        user_id: When given, restrict to that user's documents.

    Returns:
        Document rows, each with a ``chunk_count``.
    """
    clause = "WHERE d.user_id = %s" if user_id is not None else ""
    params: tuple[Any, ...] = (str(user_id),) if user_id is not None else ()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT d.id, d.user_id, d.title, d.source_name, d.created_at,
                       COUNT(c.id) AS chunk_count
                FROM documents d
                LEFT JOIN document_chunks c ON c.document_id = d.id
                {clause}
                GROUP BY d.id
                ORDER BY d.created_at DESC
                """,
                params,
            )
            rows = cur.fetchall()
    return [dict(r) for r in rows]


def delete_document(document_id: UUID | str, user_id: UUID | str | None = None) -> bool:
    """
    Delete a document (its chunks cascade via the foreign key).

    Args:
        document_id: The document to delete.
        user_id: When given, only delete if the document belongs to this user.

    Returns:
        True if a row was deleted.
    """
    clause = "AND user_id = %s" if user_id is not None else ""
    params: tuple[Any, ...] = (
        (str(document_id), str(user_id)) if user_id is not None else (str(document_id),)
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM documents WHERE id = %s {clause}",
                params,
            )
            deleted = cur.rowcount
    return deleted > 0


def similarity_search(
    query_embedding: list[float], k: int = 5, user_id: UUID | str | None = None
) -> list[dict[str, Any]]:
    """
    Return the ``k`` chunks closest to a query embedding by cosine distance.

    Args:
        query_embedding: The embedded query vector.
        k: Number of chunks to return (clamped to 1–20).
        user_id: When given, restrict the search to that user's documents.

    Returns:
        Chunk rows with their parent document title and a ``similarity`` score
        in ``[0, 1]`` (1 = identical direction), most similar first.

    Side effects:
        Executes a pgvector cosine-distance search (``<=>``) over
        ``document_chunks``.
    """
    safe_k = max(1, min(int(k), 20))
    literal = _vector_literal(query_embedding)
    clause = "WHERE d.user_id = %s" if user_id is not None else ""
    params: list[Any] = [literal]
    if user_id is not None:
        params.append(str(user_id))
    params.extend([literal, safe_k])
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT c.id, c.document_id, c.chunk_index, c.chunk_text,
                       d.title AS document_title,
                       1 - (c.embedding <=> %s::vector) AS similarity
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                {clause}
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                params,
            )
            rows = cur.fetchall()
    return [dict(r) for r in rows]

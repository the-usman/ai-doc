"""Embedding model factory for the Knowledge application.

Embeddings are generated with OpenAI ``text-embedding-3-small`` (1536 dimensions),
which is what the ``document_chunks.embedding VECTOR(1536)`` column in
``schema/schema.sql`` is sized for. The *same* model must be used at index time
and at query time — a mismatch produces vectors in a different space and makes
retrieval meaningless. See ADR-008.

The model is constructed lazily so the module imports cleanly without an API key;
tests patch this factory and never hit the network.
"""

from typing import Any

from app.config import get_settings


def get_embeddings() -> Any:
    """
    Build the OpenAI embeddings client used for indexing and querying.

    Returns:
        An ``OpenAIEmbeddings`` instance configured from settings.

    Raises:
        RuntimeError: If no OpenAI API key is configured.
    """
    from langchain_openai import OpenAIEmbeddings

    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured; the knowledge base is unavailable."
        )
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
        dimensions=settings.embedding_dimension,
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a batch of document chunks for indexing.

    Args:
        texts: The chunk texts to embed.

    Returns:
        One embedding vector per input text, in the same order.
    """
    if not texts:
        return []
    return get_embeddings().embed_documents(texts)


def embed_query(text: str) -> list[float]:
    """
    Embed a single query string for retrieval.

    Args:
        text: The user's question.

    Returns:
        The query embedding vector.
    """
    return get_embeddings().embed_query(text)

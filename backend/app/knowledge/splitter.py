"""Document chunking with LangChain's ``RecursiveCharacterTextSplitter``.

The recursive splitter tries to break on natural boundaries — paragraphs, then
lines, then sentences, then words — so a chunk is far less likely to cut a
sentence in half than a fixed-width splitter would. We size chunks by *tokens*
(via the tiktoken encoder) rather than characters so the budget lines up with
the embedding model's tokenizer. 512 tokens with 64 tokens of overlap is the
Phase 4 starting point; see ADR-009 for the reasoning and tuning notes.
"""

from typing import Any

from app.config import get_settings

_splitter: Any | None = None


def get_splitter() -> Any:
    """
    Return a cached token-aware ``RecursiveCharacterTextSplitter``.

    Returns:
        A splitter configured with the settings chunk size and overlap.
    """
    global _splitter
    if _splitter is None:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        settings = get_settings()
        _splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
    return _splitter


def split_text(text: str) -> list[str]:
    """
    Split extracted document text into overlapping chunks.

    Args:
        text: The full extracted document text.

    Returns:
        Non-empty chunk strings in document order.
    """
    chunks = get_splitter().split_text(text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]

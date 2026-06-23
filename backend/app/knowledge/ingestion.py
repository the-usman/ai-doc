"""Document ingestion pipeline.

Ties the pieces together for an upload: persist the document, split its text into
chunks, embed each chunk, and store the chunks with their embeddings. This is the
one code path the upload route calls; it is deliberately thin so each stage
(extraction, splitting, embedding, persistence) stays independently testable.
"""

from typing import Any
from uuid import UUID

from app.knowledge import embeddings, persistence, splitter


def ingest_document(
    user_id: UUID | str, title: str, source_name: str, raw_text: str
) -> dict[str, Any]:
    """
    Persist a document and index its chunks into the vector store.

    Args:
        user_id: The owner of the document.
        title: Human-readable title supplied at upload.
        source_name: Original filename.
        raw_text: Full extracted text.

    Returns:
        The created document row plus the ``chunk_count`` that was indexed.

    Side effects:
        Inserts one ``documents`` row and N ``document_chunks`` rows, and calls
        the embedding model once for the whole batch of chunks.
    """
    document = persistence.create_document(user_id, title, source_name, raw_text)

    chunk_texts = splitter.split_text(raw_text)
    vectors = embeddings.embed_texts(chunk_texts)
    chunks = [
        {"chunk_index": index, "chunk_text": text, "embedding": vector}
        for index, (text, vector) in enumerate(zip(chunk_texts, vectors, strict=True))
    ]
    count = persistence.insert_chunks(document["id"], chunks)

    return {**document, "chunk_count": count}

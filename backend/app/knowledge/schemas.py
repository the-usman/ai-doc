"""Structured shapes for the Knowledge application's API and RAG chain."""

from pydantic import BaseModel, Field


class KnowledgeAnswer(BaseModel):
    """The LLM's structured answer over retrieved context."""

    answer: str = Field(description="The answer for the user, citing document titles.")
    answer_found: bool = Field(
        default=True,
        description="False when the answer was not present in the provided context.",
    )


class SourceChunk(BaseModel):
    """A retrieved chunk shown to the user as a citation."""

    document_id: str
    document_title: str
    chunk_index: int
    similarity: float
    snippet: str = Field(description="A short excerpt of the chunk text.")


class KnowledgeResponse(BaseModel):
    """Full response returned by the Knowledge Chat endpoint."""

    answer: str
    answer_found: bool = True
    sources: list[SourceChunk] = Field(default_factory=list)


class DocumentSummary(BaseModel):
    """A document as listed on the Documents page."""

    id: str
    title: str
    source_name: str
    chunk_count: int
    created_at: str

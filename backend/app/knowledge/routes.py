"""HTTP surface for the Knowledge application.

* ``GET    /api/knowledge/documents``        — list the caller's documents.
* ``POST   /api/knowledge/documents``         — upload a file (multipart): extract,
  chunk, embed and index it.
* ``DELETE /api/knowledge/documents/{id}``    — remove a document and its chunks.
* ``POST   /api/knowledge/chat``              — ask a question; returns a grounded
  answer plus the source chunks it used.
* ``POST   /api/knowledge/search``            — raw retrieval for the Explore page.

All routes require the Phase 1 session cookie. Documents are scoped per user.
"""

import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from app.auth_routes import SESSION_COOKIE
from app.knowledge import extraction, ingestion, persistence, retriever
from app.knowledge.chain import answer_question
from app.sessions import get_active_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

# Reject uploads larger than this to bound memory and embedding cost.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


class QuestionRequest(BaseModel):
    """Body for a Knowledge Chat question."""

    question: str = Field(min_length=1, description="The user's question.")


class SearchRequest(BaseModel):
    """Body for a raw knowledge-base search (Explore page)."""

    query: str = Field(min_length=1, description="The search query.")


def _require_session(request: Request) -> dict:
    """
    Resolve the active session from the cookie.

    Args:
        request: Incoming HTTP request.

    Returns:
        Joined session and user fields.

    Raises:
        HTTPException: 401 when unauthenticated or expired.
    """
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_active_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    return session


def _serialize_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Convert a document row into a JSON-friendly dict."""
    return {
        "id": str(doc["id"]),
        "title": doc["title"],
        "source_name": doc["source_name"],
        "chunk_count": int(doc.get("chunk_count", 0)),
        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
    }


@router.get("/documents")
def list_documents(request: Request) -> dict[str, list[dict[str, Any]]]:
    """
    List the signed-in user's uploaded documents, newest first.

    Args:
        request: Incoming request (provides the session cookie).

    Returns:
        A JSON object with a ``documents`` list.
    """
    session = _require_session(request)
    docs = persistence.list_documents(session["user_id"])
    return {"documents": [_serialize_document(d) for d in docs]}


@router.post("/documents")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
) -> dict[str, Any]:
    """
    Upload a document: extract text, chunk, embed, and index it.

    Args:
        request: Incoming request (provides the session cookie).
        file: The uploaded file (``.txt``/``.md`` or ``.pdf``).
        title: Human-readable title for the document.

    Returns:
        The created document summary, including the indexed chunk count.

    Raises:
        HTTPException: 401 unauthenticated; 400 for an empty/oversized/unsupported
            file or one with no extractable text; 503 if embeddings are not
            configured.
    """
    session = _require_session(request)

    filename = file.filename or "upload"
    if not extraction.is_supported(filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a .txt, .md or .pdf file.",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds the 10 MB limit.")

    try:
        text = extraction.extract_text(filename, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    clean_title = title.strip() or filename
    try:
        document = ingestion.ingest_document(
            session["user_id"], clean_title, filename, text
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return _serialize_document(document)


@router.delete("/documents/{document_id}")
def delete_document(request: Request, document_id: str) -> dict[str, bool]:
    """
    Delete one of the caller's documents and its chunks.

    Args:
        request: Incoming request (provides the session cookie).
        document_id: The document to delete.

    Returns:
        ``{"deleted": true}`` when a row was removed.

    Raises:
        HTTPException: 401 unauthenticated; 404 if the document does not exist
            or does not belong to the caller.
    """
    session = _require_session(request)
    deleted = persistence.delete_document(document_id, session["user_id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True}


@router.post("/chat")
def knowledge_chat(request: Request, payload: QuestionRequest) -> dict[str, Any]:
    """
    Answer a question over the caller's documents, with source citations.

    Args:
        request: Incoming request (provides the session cookie).
        payload: The user's question.

    Returns:
        The grounded answer and the source chunks used.

    Raises:
        HTTPException: 401 unauthenticated; 503 if the model/embeddings are not
            configured; 502 on a backend failure.
    """
    session = _require_session(request)
    session_id = str(session["session_id"])
    try:
        response = answer_question(session_id, payload.question, session["user_id"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # surface the exact error to aid debugging
        logger.exception("Knowledge backend error")
        raise HTTPException(
            status_code=502,
            detail=f"Knowledge backend error: {type(exc).__name__}: {exc}",
        ) from exc
    return response.model_dump()


@router.post("/search")
def knowledge_search(request: Request, payload: SearchRequest) -> dict[str, Any]:
    """
    Run a raw retrieval against the knowledge base (Explore page).

    Args:
        request: Incoming request (provides the session cookie).
        payload: The search query.

    Returns:
        The matching chunks with their similarity scores.

    Raises:
        HTTPException: 401 unauthenticated; 503 if embeddings are not configured.
    """
    session = _require_session(request)
    try:
        rows = retriever.search_chunks(payload.query, user_id=session["user_id"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # surface the exact error to aid debugging
        logger.exception("Knowledge search error")
        raise HTTPException(
            status_code=502,
            detail=f"Knowledge search error: {type(exc).__name__}: {exc}",
        ) from exc
    results = [
        {
            "document_id": str(row["document_id"]),
            "document_title": row["document_title"],
            "chunk_index": row["chunk_index"],
            "similarity": round(float(row["similarity"]), 4),
            "text": row["chunk_text"],
        }
        for row in rows
    ]
    return {"results": results}

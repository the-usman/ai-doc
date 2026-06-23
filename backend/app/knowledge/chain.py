"""The retrieval-augmented generation (RAG) chain.

Structure (ADR-010): a pgvector retriever fetches the top-k chunks, a
``ChatPromptTemplate`` formats them as labelled context alongside the question
and the conversation history, the Anthropic model answers, and the output is
parsed into the structured :class:`KnowledgeAnswer`. The system prompt forbids
answering from outside the context and requires citing document titles.

Embeddings come from OpenAI (see :mod:`app.knowledge.embeddings`); the answer
model stays Anthropic, reusing the chat application's model factory.
"""

from typing import Any
from uuid import UUID

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.chat.chain import get_chat_model
from app.config import get_settings
from app.knowledge import retriever
from app.knowledge.schemas import KnowledgeAnswer, KnowledgeResponse, SourceChunk
from app.memory import append_turn, get_history

SCOPE = "knowledge"

# How much of each chunk to surface to the user as a citation snippet.
_SNIPPET_CHARS = 240


def _is_overloaded_error(exc: Exception) -> bool:
    """
    Report whether an exception is a transient Anthropic "overloaded" error.

    Covers HTTP 529 (and the SDK's overloaded error type) so the chain can map a
    sustained overload to a friendly, retryable response.

    Args:
        exc: The exception raised by the model call.

    Returns:
        True if the error looks like an Anthropic overload/529.
    """
    status = getattr(exc, "status_code", None)
    if status == 529:
        return True
    text = f"{type(exc).__name__} {exc}".lower()
    return "overloaded" in text or "529" in text


def _format_context(docs: list) -> str:
    """
    Render retrieved documents as labelled context for the prompt.

    Args:
        docs: LangChain ``Document`` objects from the retriever.

    Returns:
        A string with one titled passage per retrieved chunk, or a marker when
        nothing was retrieved.
    """
    if not docs:
        return "(no relevant passages were found in the uploaded documents)"
    blocks = []
    for index, doc in enumerate(docs, start=1):
        title = doc.metadata.get("document_title", "Untitled")
        blocks.append(f"[{index}] From \"{title}\":\n{doc.page_content}")
    return "\n\n".join(blocks)


def build_rag_chain(user_id: UUID | str | None = None) -> Any:
    """
    Build the pure LCEL RAG chain: retriever → prompt → model → structured output.

    The chain takes a question string and returns a :class:`KnowledgeAnswer`. It
    carries no conversation memory; :func:`answer_question` wraps it with memory
    and source reporting for the API.

    Args:
        user_id: Optional owner filter applied to retrieval.

    Returns:
        A runnable mapping a question string to a ``KnowledgeAnswer``.
    """
    from langchain_core.runnables import RunnablePassthrough

    pg_retriever = retriever.get_retriever(user_id=user_id)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", get_settings().rag_system_prompt),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    model = get_chat_model().with_structured_output(KnowledgeAnswer)
    return (
        {
            "context": pg_retriever | _format_context,
            "question": RunnablePassthrough(),
        }
        | prompt
        | model
    )


def answer_question(
    session_id: str, question: str, user_id: UUID | str | None = None
) -> KnowledgeResponse:
    """
    Answer a question over the knowledge base, with memory and source citations.

    Retrieval is run once so the retrieved chunks can be both fed to the model
    and returned to the caller as citations — the transparency the Knowledge Chat
    page shows beneath each answer.

    Args:
        session_id: Conversation key (the auth session id).
        question: The user's question.
        user_id: Optional owner filter applied to retrieval.

    Returns:
        A :class:`KnowledgeResponse` with the answer and the source chunks used.

    Side effects:
        Embeds the question, runs a pgvector search, calls the model, and appends
        the turn to the knowledge-scoped conversation memory.
    """
    settings = get_settings()
    pg_retriever = retriever.get_retriever(user_id=user_id)
    docs = pg_retriever.invoke(question)
    context = _format_context(docs)

    # History goes in as a MessagesPlaceholder (real message objects), NOT baked
    # into the template — otherwise any '{'/'}' in a past message or in the
    # retrieved context would be parsed as a template variable and blow up.
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", settings.rag_system_prompt),
            MessagesPlaceholder("history"),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    model = get_chat_model().with_structured_output(KnowledgeAnswer)
    try:
        result: KnowledgeAnswer | None = (prompt | model).invoke(
            {
                "history": get_history(SCOPE, session_id),
                "context": context,
                "question": question,
            }
        )
    except Exception as exc:  # noqa: BLE001 - narrowed below
        # If the answer model is still overloaded after the SDK's retries, give a
        # clear, retryable message (503) rather than a generic backend error.
        if _is_overloaded_error(exc):
            raise RuntimeError(
                "The answer model is busy right now (overloaded). "
                "Please try again in a few seconds."
            ) from exc
        raise

    # with_structured_output can return None if the model emits no structured
    # call; treat that as "not found" rather than crashing on result.answer.
    if result is None:
        result = KnowledgeAnswer(
            answer="I could not produce an answer from the uploaded documents.",
            answer_found=False,
        )

    sources = [
        SourceChunk(
            document_id=doc.metadata.get("document_id", ""),
            document_title=doc.metadata.get("document_title", "Untitled"),
            chunk_index=int(doc.metadata.get("chunk_index", 0)),
            similarity=float(doc.metadata.get("similarity", 0.0)),
            snippet=doc.page_content[:_SNIPPET_CHARS].strip(),
        )
        for doc in docs
    ]

    append_turn(SCOPE, session_id, question, result.answer)
    return KnowledgeResponse(
        answer=result.answer,
        answer_found=result.answer_found,
        sources=sources if result.answer_found else [],
    )

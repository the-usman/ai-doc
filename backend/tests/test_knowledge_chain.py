"""Tests for the RAG chain.

The retriever, the answer model, and conversation memory are all patched, so the
test covers the chain's orchestration — retrieve once, ground the prompt, return
the answer with its source chunks — without OpenAI, Anthropic, a DB, or Redis.
"""

from uuid import uuid4

import pytest

pytest.importorskip("langchain_core")

from langchain_core.documents import Document  # noqa: E402
from langchain_core.runnables import RunnableLambda  # noqa: E402

from app.knowledge import chain  # noqa: E402
from app.knowledge.schemas import KnowledgeAnswer, KnowledgeResponse  # noqa: E402


def _doc(title="Guide", index=0, similarity=0.9, text="onboarding takes one day") -> Document:
    return Document(
        page_content=text,
        metadata={
            "document_id": "d-1",
            "document_title": title,
            "chunk_index": index,
            "similarity": similarity,
        },
    )


def test_format_context_labels_each_passage() -> None:
    """Retrieved passages are rendered with their document title."""
    rendered = chain._format_context([_doc(title="Onboarding", text="step one")])
    assert "Onboarding" in rendered
    assert "step one" in rendered


def test_format_context_handles_no_documents() -> None:
    """With nothing retrieved, a clear no-context marker is returned."""
    assert "no relevant passages" in chain._format_context([])


class _FakeRetriever:
    def __init__(self, docs) -> None:
        self._docs = docs

    def invoke(self, _query):
        return self._docs


class _ModelHolder:
    """Stands in for the chat model; structured output returns a fixed answer."""

    def __init__(self, answer: KnowledgeAnswer) -> None:
        self._answer = answer

    def with_structured_output(self, _schema):
        return RunnableLambda(lambda _prompt_value: self._answer)


@pytest.fixture
def patched_chain(monkeypatch):
    """Patch retrieval, the model, and memory; capture appended turns."""
    docs = [_doc(title="Onboarding", similarity=0.88)]
    monkeypatch.setattr(
        chain.retriever, "get_retriever", lambda user_id=None: _FakeRetriever(docs)
    )
    monkeypatch.setattr(chain, "get_history", lambda scope, sid: [])
    recorded = {}
    monkeypatch.setattr(
        chain,
        "append_turn",
        lambda scope, sid, human, ai: recorded.update(
            scope=scope, human=human, ai=ai
        ),
    )
    return recorded


def test_answer_question_returns_answer_and_sources(patched_chain, monkeypatch) -> None:
    """A found answer is returned with the source chunks that grounded it."""
    answer = KnowledgeAnswer(answer="Onboarding takes one day (Onboarding).", answer_found=True)
    monkeypatch.setattr(chain, "get_chat_model", lambda: _ModelHolder(answer))

    response = chain.answer_question(str(uuid4()), "how long is onboarding?")

    assert isinstance(response, KnowledgeResponse)
    assert response.answer_found
    assert response.answer.startswith("Onboarding takes one day")
    assert len(response.sources) == 1
    source = response.sources[0]
    assert source.document_title == "Onboarding"
    assert source.similarity == pytest.approx(0.88)
    assert source.snippet  # snippet populated from chunk text


def test_answer_question_records_turn_under_knowledge_scope(patched_chain, monkeypatch) -> None:
    """The completed turn is appended to the knowledge-scoped memory."""
    answer = KnowledgeAnswer(answer="An answer.", answer_found=True)
    monkeypatch.setattr(chain, "get_chat_model", lambda: _ModelHolder(answer))

    chain.answer_question("session-xyz", "a question")

    assert patched_chain["scope"] == "knowledge"
    assert patched_chain["human"] == "a question"
    assert patched_chain["ai"] == "An answer."


def test_answer_question_tolerates_braces_in_history_and_context(monkeypatch) -> None:
    """Prior messages or context containing '{'/'}' must not break the template.

    Regression test: history used to be baked into the prompt as template text, so
    a past answer containing JSON-like braces raised a template error (the 502
    "Knowledge backend error"). History now flows in as message objects.
    """
    from langchain_core.messages import AIMessage, HumanMessage

    docs = [_doc(text='see config {"chunk_size": 512}')]
    monkeypatch.setattr(
        chain.retriever, "get_retriever", lambda user_id=None: _FakeRetriever(docs)
    )
    monkeypatch.setattr(
        chain,
        "get_history",
        lambda scope, sid: [
            HumanMessage(content="what is the {setting}?"),
            AIMessage(content='it is {"value": 1}'),
        ],
    )
    monkeypatch.setattr(chain, "append_turn", lambda *a, **k: None)
    answer = KnowledgeAnswer(answer="The chunk size is 512.", answer_found=True)
    monkeypatch.setattr(chain, "get_chat_model", lambda: _ModelHolder(answer))

    response = chain.answer_question(str(uuid4()), "what is the chunk size?")
    assert response.answer == "The chunk size is 512."


def test_is_overloaded_error_detects_529() -> None:
    """Overload is recognised by status code or message text."""

    class _Overloaded(Exception):
        status_code = 529

    assert chain._is_overloaded_error(_Overloaded())
    assert chain._is_overloaded_error(Exception("Error code: 529 - Overloaded"))
    assert not chain._is_overloaded_error(ValueError("bad request"))


def test_answer_question_maps_overload_to_runtimeerror(patched_chain, monkeypatch) -> None:
    """A sustained overload becomes a RuntimeError (→ 503) with a clear message."""

    class _OverloadedModel:
        def with_structured_output(self, _schema):
            from langchain_core.runnables import RunnableLambda

            def _raise(_payload):
                raise RuntimeError("Error code: 529 - Overloaded")

            return RunnableLambda(_raise)

    monkeypatch.setattr(chain, "get_chat_model", lambda: _OverloadedModel())

    with pytest.raises(RuntimeError, match="overloaded"):
        chain.answer_question(str(uuid4()), "any question")


def test_answer_question_drops_sources_when_not_found(patched_chain, monkeypatch) -> None:
    """When the answer is not in the context, no sources are returned."""
    answer = KnowledgeAnswer(
        answer="I could not find that in the uploaded documents.", answer_found=False
    )
    monkeypatch.setattr(chain, "get_chat_model", lambda: _ModelHolder(answer))

    response = chain.answer_question(str(uuid4()), "unanswerable question")

    assert response.answer_found is False
    assert response.sources == []

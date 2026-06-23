"""Tests for the agent-facing knowledge search tool."""

import pytest

pytest.importorskip("langchain_core")

from app.knowledge import tools  # noqa: E402


def test_search_knowledge_base_shapes_rows(monkeypatch) -> None:
    """The tool maps chunk rows to compact dicts with rounded similarity."""
    monkeypatch.setattr(
        tools.retriever,
        "search_chunks",
        lambda query: [
            {
                "document_id": "d1",
                "document_title": "Spec",
                "chunk_index": 4,
                "chunk_text": "the answer text",
                "similarity": 0.876543,
            }
        ],
    )
    result = tools.search_knowledge_base.invoke({"query": "what does the spec say?"})
    assert result == [
        {
            "document_title": "Spec",
            "chunk_index": 4,
            "similarity": 0.8765,
            "text": "the answer text",
        }
    ]


def test_knowledge_tools_exports_the_tool() -> None:
    """The tool is exported for binding to the DataAgent."""
    assert tools.search_knowledge_base in tools.KNOWLEDGE_TOOLS

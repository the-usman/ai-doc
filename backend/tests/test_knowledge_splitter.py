"""Tests for token-aware document chunking."""

import pytest

pytest.importorskip("langchain_text_splitters")
pytest.importorskip("tiktoken")

from app.knowledge import splitter  # noqa: E402


def test_split_text_returns_non_empty_chunks() -> None:
    """Splitting real prose yields stripped, non-empty chunks."""
    text = "Onboarding guide.\n\n" + ("All new hires complete training. " * 200)
    chunks = splitter.split_text(text)
    assert chunks
    assert all(chunk == chunk.strip() and chunk for chunk in chunks)


def test_split_text_long_input_produces_multiple_chunks() -> None:
    """Input well beyond one chunk's token budget splits into several pieces."""
    text = " ".join(f"sentence number {i} about the platform." for i in range(2000))
    chunks = splitter.split_text(text)
    assert len(chunks) > 1


def test_split_text_short_input_is_single_chunk() -> None:
    """A short document fits in one chunk."""
    chunks = splitter.split_text("A single short sentence.")
    assert chunks == ["A single short sentence."]


def test_get_splitter_is_cached() -> None:
    """The splitter is built once and reused."""
    assert splitter.get_splitter() is splitter.get_splitter()

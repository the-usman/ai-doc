"""Tests for upload text extraction.

Plain-text decoding is exercised directly; the PDF path is exercised by patching
``pypdf.PdfReader`` with a fake so the test needs no real PDF bytes or network.
"""

import pytest

from app.knowledge import extraction


def test_is_supported_accepts_text_and_pdf() -> None:
    """Supported extensions are recognised, case-insensitively."""
    assert extraction.is_supported("notes.txt")
    assert extraction.is_supported("README.MD")
    assert extraction.is_supported("spec.pdf")
    assert extraction.is_supported("transcript.text")


def test_is_supported_rejects_other_types() -> None:
    """Unsupported or extension-less filenames are rejected."""
    assert not extraction.is_supported("photo.png")
    assert not extraction.is_supported("archive.zip")
    assert not extraction.is_supported("noextension")


def test_extract_text_decodes_plain_text() -> None:
    """A UTF-8 text file is decoded and stripped."""
    data = "  hello world  ".encode("utf-8")
    assert extraction.extract_text("note.txt", data) == "hello world"


def test_extract_text_replaces_invalid_bytes() -> None:
    """Invalid UTF-8 is decoded with replacement rather than raising."""
    text = extraction.extract_text("note.txt", b"caf\xff")
    assert text.startswith("caf")


def test_extract_text_rejects_unsupported_extension() -> None:
    """An unsupported extension raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        extraction.extract_text("image.png", b"\x89PNG")


def test_extract_text_rejects_empty_result() -> None:
    """Whitespace-only content yields no text and is rejected."""
    with pytest.raises(ValueError, match="No extractable text"):
        extraction.extract_text("blank.txt", b"   \n\t  ")


def test_extract_text_reads_pdf_pages(monkeypatch) -> None:
    """The PDF path concatenates every page's extracted text."""

    class _FakePage:
        def __init__(self, text: str) -> None:
            self._text = text

        def extract_text(self) -> str:
            return self._text

    class _FakeReader:
        def __init__(self, _stream) -> None:
            self.pages = [_FakePage("page one"), _FakePage("page two")]

    import pypdf

    monkeypatch.setattr(pypdf, "PdfReader", _FakeReader)
    text = extraction.extract_text("doc.pdf", b"%PDF-1.4 fake bytes")
    assert "page one" in text
    assert "page two" in text

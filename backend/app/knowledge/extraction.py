"""Text extraction from uploaded files.

Plain-text files are decoded directly. PDFs are parsed with ``pypdf`` — chosen
for being pure-Python (no system libraries to install in the Docker image) and
adequate for the born-digital PDFs this platform handles. Extraction quality
feeds directly into retrieval quality, so the choice is recorded in ADR-009.
"""

from io import BytesIO

# Extensions we accept for upload.
TEXT_EXTENSIONS = {".txt", ".md", ".text"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | PDF_EXTENSIONS


def _extension(filename: str) -> str:
    """Return the lower-cased file extension including the dot, or ''."""
    name = filename.lower().strip()
    dot = name.rfind(".")
    return name[dot:] if dot != -1 else ""


def is_supported(filename: str) -> bool:
    """
    Report whether a filename has a supported extension.

    Args:
        filename: The original upload filename.

    Returns:
        True for ``.txt``/``.md``/``.text`` and ``.pdf`` files.
    """
    return _extension(filename) in SUPPORTED_EXTENSIONS


def extract_text(filename: str, data: bytes) -> str:
    """
    Extract plain text from an uploaded file's bytes.

    Args:
        filename: The original filename (used to pick an extractor).
        data: The raw file bytes.

    Returns:
        The extracted text, with surrounding whitespace stripped.

    Raises:
        ValueError: If the file type is unsupported or yields no text.
    """
    ext = _extension(filename)
    if ext in TEXT_EXTENSIONS:
        text = data.decode("utf-8", errors="replace")
    elif ext in PDF_EXTENSIONS:
        text = _extract_pdf(data)
    else:
        raise ValueError(f"Unsupported file type: {ext or '(none)'}")

    text = text.strip()
    if not text:
        raise ValueError("No extractable text was found in the document.")
    return text


def _extract_pdf(data: bytes) -> str:
    """
    Extract text from a PDF's bytes using pypdf.

    Args:
        data: The raw PDF bytes.

    Returns:
        The concatenated text of every page, separated by blank lines.
    """
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)

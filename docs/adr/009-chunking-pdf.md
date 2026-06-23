# ADR-009 — Document extraction and chunking strategy

**Date:** 2026-06-23
**Status:** Accepted
**Phase:** 4 — Knowledge (RAG)

### Context

Before text can be embedded it has to be extracted from an uploaded file and split
into pieces small enough to embed and retrieve usefully. Two sub-decisions follow:
how to get plain text out of the supported formats (notably PDF, which is not
plain text), and how to cut that text into chunks. Chunk size is a genuine
tradeoff — chunks that are too large dilute the embedding and return irrelevant
surrounding text as a "match"; chunks that are too small lose the context needed
to answer a question and multiply the row count and index size.

### Options considered

**Extraction.**
- **`pypdf`** — pure-Python, no system dependencies, MIT-licensed, extracts text
  from the common PDF types we expect (exported docs, reports, specs).
- **`pdfplumber` / `PyMuPDF`** — richer layout and table extraction, but heavier
  dependencies (PyMuPDF ships native binaries) for capabilities this phase does
  not need.
- **An OCR pipeline (Tesseract)** — handles scanned/image PDFs, but a large
  dependency and slow; out of scope for text-bearing documents.

**Chunking.**
- **Fixed character windows** — trivial, but cut mid-word and mid-sentence,
  fragmenting meaning at boundaries.
- **`RecursiveCharacterTextSplitter` with token-based sizing** — splits on a
  descending list of natural boundaries (paragraph, line, sentence, word) and
  measures length in tokens via the model's tiktoken encoder, so chunk size is
  expressed in the same units the embedding model actually consumes.
- **Semantic / model-driven chunking** — split on embedding-similarity shifts;
  higher quality in principle but adds an extra model pass per document and more
  moving parts than this phase warrants.

### Decision

Extract text with **`pypdf`** for PDFs and direct UTF-8 decoding for `.txt`/`.md`,
and chunk with **`RecursiveCharacterTextSplitter.from_tiktoken_encoder` at 512
tokens with 64 tokens of overlap** (`chunk_size`/`chunk_overlap` in config).

`pypdf` is chosen for being dependency-light and sufficient: the platform accepts
text-bearing documents, not scans, so OCR and rich layout parsing are unnecessary
weight. Extraction is centralised in `knowledge/extraction.py`, which validates
the extension, decodes text with `errors="replace"`, and rejects unsupported or
empty files with a clear `ValueError`.

The recursive splitter sized by tiktoken is chosen because it respects natural
language boundaries while measuring length in the embedding model's own token
units. **512 tokens** is large enough to hold a coherent idea (a paragraph or
two) yet small enough that a retrieved chunk is mostly relevant to the query.
**64 tokens of overlap** (one-eighth) carries a sentence or two across each cut so
a fact straddling a boundary still appears whole in at least one chunk, at a modest
cost in duplicated storage. Both numbers are config values, not literals, so they
can be tuned without code changes.

### Consequences

- The platform reliably ingests `.txt`, `.md`, and text-bearing `.pdf`. Scanned or
  image-only PDFs extract little or no text and are out of scope until an OCR path
  is added; an empty extraction is rejected rather than producing zero chunks.
- Token-based sizing keeps every chunk within the embedding model's comfortable
  input range and makes chunk size mean the same thing as the model's own limit.
- 512/64 is a deliberate middle ground; very long tables or code blocks may still
  span chunks, and the overlap duplicates a small amount of text in the store.
  Re-tuning is a config change followed by re-ingestion.
- Centralising extraction behind one validated entry point keeps the upload route
  thin and gives one place to add new formats later.

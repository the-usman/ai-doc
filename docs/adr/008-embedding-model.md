# ADR-008 — Embedding model, dimension, and vector storage

**Date:** 2026-06-23
**Status:** Accepted
**Phase:** 4 — Knowledge (RAG)

### Context

Phase 4 adds retrieval-augmented generation over user-uploaded documents. Every
retrieval system rests on two coupled choices: which model turns text into
vectors, and where those vectors live. The two are coupled because a vector's
dimension is fixed by the model that produced it, and the database column that
stores it must declare that exact dimension. The schema (`schema/schema.sql`) was
locked in an earlier phase with `document_chunks.embedding VECTOR(1536)` and an
ivfflat cosine index, so the embedding choice is constrained: whatever model we
pick must emit 1536-dimensional vectors, and the same model must be used at index
time and query time or cosine distances become meaningless.

### Options considered

- **OpenAI `text-embedding-3-small` (1536-dim).** Hosted API, no local model
  weights, 1536 dimensions natively — a direct match for the existing column.
  Costs a fraction of a cent per thousand chunks. Requires `OPENAI_API_KEY`.
- **OpenAI `text-embedding-3-large` (3072-dim).** Higher quality but double the
  dimension; would force a schema change and a larger index.
- **Local sentence-transformers (e.g. `all-MiniLM-L6-v2`, 384-dim).** No API key
  and no per-call cost, but the dimension does not match the column, the model
  weights bloat the image, and CPU inference is slow on the deployment target.
- **Dedicated vector database (Pinecone, Weaviate, Qdrant).** Purpose-built ANN
  search, but a second datastore to run, secure, and back up when we already have
  Postgres with pgvector.

### Decision

Use **OpenAI `text-embedding-3-small` at 1536 dimensions**, stored **directly in
the existing `document_chunks` table** via pgvector — no separate vector store.

The dimension is the deciding factor: `text-embedding-3-small` matches the locked
`VECTOR(1536)` column exactly, so no migration is needed and the ivfflat index
keeps working unchanged. The model and dimension are not hard-coded — they live in
config (`embedding_model`, `embedding_dimension`) and the dimension is passed to
`OpenAIEmbeddings(dimensions=...)`, so the same column could later hold a
reduced-dimension projection of a larger model without touching call sites.

Storage stays in Postgres. The schema's `document_chunks` table — with its foreign
key to `documents`, its `chunk_index`, and its ivfflat cosine index — remains the
single source of truth. Rather than adopt LangChain's `PGVector` store (which
manages its own tables), we keep our schema and wrap retrieval in a thin
`BaseRetriever` subclass (`knowledge/retriever.py`) so the rest of the pipeline
still composes as standard LCEL. This preserves referential integrity (deleting a
document cascades to its chunks) and one operational surface to run and back up.

### Consequences

- The column dimension and the embedding model are now an invariant pair; changing
  the model to one with a different native dimension requires either projecting to
  1536 or migrating the column and rebuilding the index.
- Embedding requires network access and a valid `OPENAI_API_KEY`; the ingestion
  and chat paths surface a clear 503 when the key is absent rather than failing
  obscurely, and the embeddings factory raises `RuntimeError` early.
- Keeping vectors in Postgres means no second datastore to operate, and document
  deletion stays transactional and consistent via the existing foreign key.
- ivfflat is an approximate index: recall depends on `lists` and the number of
  probes. For the expected corpus size this is well within tolerance, and the
  index can be rebuilt with different parameters without changing application code.

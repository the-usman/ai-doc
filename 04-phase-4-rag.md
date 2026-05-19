# Phase 4 — Knowledge

**Duration:** Weeks 7 to 9
**Branch:** `phase-4/rag`
**Deliverable:** A LangChain-powered RAG pipeline registered as the Knowledge application in the platform shell, backed by pgvector for vector search and Redis for persistent agent memory. A document upload interface, a retrieval-augmented chat interface, and a document-aware agent that answers questions about uploaded content.

---

## What you are building

The three applications you have built so far — the platform home, the LangChain chatbot, and the LangGraph agents panel — all work with data that lives in structured tables. They can count rows, list records, and summarise what is in the database. What they cannot do is answer questions about documents — PDFs, notes, specifications, reports — where the information is unstructured and context-dependent.

Phase 4 teaches the pattern that makes that possible: Retrieval-Augmented Generation, or RAG. A user uploads a document. The system chunks the document into pieces, converts each piece into a vector embedding, and stores the embeddings in pgvector. When the user asks a question, the system converts the question into an embedding, finds the document chunks whose embeddings are most similar to the question's embedding, and injects those chunks into the LLM's context. The LLM now has the relevant information in front of it and produces a grounded, accurate answer.

This phase also adds persistent memory to the agent using Redis. Until now, conversation memory has been stored in RAM — it disappears when the server restarts. Redis-backed memory persists across restarts, which is the minimum requirement for a production system where users expect their history to be there when they return.

---

## Understanding RAG before building it

RAG is not magic. It is a specific engineering pipeline with specific components, and understanding each component before you use it is what allows you to diagnose problems and improve quality.

The first component is the text splitter. A document cannot be embedded as a single unit — most embedding models have a token limit, and a large document as a single chunk would have such a broad representation that it would match almost any query, making retrieval meaningless. The splitter breaks the document into chunks of manageable size, with some overlap between adjacent chunks so that sentences that fall near the boundary of a chunk are not split in a way that destroys their meaning.

The second component is the embedding model. An embedding model converts text into a high-dimensional vector — a list of floating-point numbers — that represents the semantic meaning of the text. The key property is that texts with similar meanings have vectors that are close to each other in this high-dimensional space, even if the words are different. This is what makes semantic search possible: the question "how many users signed up last week?" and the document chunk "new registrations increased by 42% in the seven days ending Friday" have similar vectors because they mean similar things, even though they share almost no words.

The third component is the vector store. This is where the embeddings are stored and searched. AI-Doc uses pgvector, which means the vector store is your existing PostgreSQL database with the vector extension enabled. When you search, you provide a query embedding and pgvector finds the k database rows whose stored embeddings are most similar, measured by cosine distance.

The fourth component is the retriever. In LangChain's abstraction, a retriever takes a query string, converts it to an embedding internally, and returns the top-k most relevant documents. LangChain's `PGVector` integration wraps pgvector as a retriever, which means it plugs directly into LCEL chains.

The fifth component is the RAG chain itself. In LangChain, a RAG chain takes a question, calls the retriever to get relevant context, formats a prompt that includes both the question and the context, and passes that prompt to the LLM. The LLM answers the question based on the provided context — it is not relying on its training data, it is reading the documents you gave it.

Use Claude to walk through each of these components in detail before you implement any of them. Ask it what happens when chunk size is too large. Ask it what happens when the embedding model is different during retrieval than it was during indexing. Ask it what hybrid search is and why it sometimes outperforms pure vector search. These are the questions you will need to answer confidently in the live demonstration.

---

## Step 1 — Knowledge application registration

Register the Knowledge application in the platform shell at the path `/knowledge`. Its sub-navigation has three pages: Documents (a list of uploaded documents with upload controls), Chat (a retrieval-augmented chat interface specific to the knowledge base), and Explore (a search interface for querying the knowledge base directly without conversational framing). The Documents and Chat pages need to be functional in Phase 4. Explore can be a placeholder.

---

## Step 2 — pgvector schema

The `schema/schema.sql` file already contains the `documents` and `document_chunks` tables defined in Phase 1 with `IF NOT EXISTS` guards. Confirm they are present and match your requirements, and make any needed adjustments. Confirm the ivfflat index on the `embedding` column is present. Confirm the pgvector extension is activated at the top of the schema.

The dimension of the embedding column is 1536, which matches the OpenAI `text-embedding-3-small` model. If you are using a different embedding model, the dimension must match exactly — document this in an ADR. This is a constraint that cannot be changed after data has been inserted without dropping and recreating the table, which is why it is documented as a deliberate architectural decision rather than a configuration detail.

---

## Step 3 — Document upload and text extraction

Build the document upload interface in the Documents page. A user selects a file — accept PDF and plain text formats — gives it a title, and uploads it. The backend receives the file, extracts the text, and passes it to the ingestion pipeline.

For text files, extraction is trivial. For PDFs, use a library to extract the text content. Document your choice of PDF extraction library in an ADR, because PDF extraction quality varies significantly across tools and the choice has a direct impact on retrieval quality downstream.

Store the original file, the extracted text, the document title, and metadata in the `documents` table. Then pass the extracted text to the chunking and embedding pipeline.

---

## Step 4 — LangChain text splitter and embeddings

Use LangChain's `RecursiveCharacterTextSplitter` to chunk the extracted text. This splitter is the standard starting point for most RAG systems because it tries to split at natural boundaries — paragraphs, sentences, then words — rather than at arbitrary character positions. Configure it with a chunk size of 512 tokens and an overlap of 64 tokens as a starting point.

Use LangChain's embeddings integration to generate an embedding for each chunk. `OpenAIEmbeddings` with `text-embedding-3-small` or `BedrockEmbeddings` with an equivalent model are the right choices depending on your API access. The embedding model you choose here must be the same model you use at query time — mismatched models produce nonsensical retrieval results.

Use LangChain's `PGVector` integration to store the embeddings in your PostgreSQL database. `PGVector.from_documents` handles the insert in batch. After indexing a document, run a test query directly against the vector store and inspect the results to confirm retrieval is working before wiring it into the chat interface.

Document the chunking strategy and embedding model in an ADR. Note that chunk size is a tunable parameter — 512 tokens is a starting point, not a fixed truth, and in a real system you would run retrieval quality experiments to find the optimal size for your document types.

---

## Step 5 — LangChain retrieval chain

Build a RAG chain using LangChain's retrieval components. The chain structure is: a `PGVector` retriever that accepts a query string and returns the top-5 most similar chunks, a `ChatPromptTemplate` that formats the retrieved chunks as context alongside the user's question, the LLM, and a structured output parser.

The system prompt for the RAG chain must instruct the LLM to answer based only on the provided context, to cite the document title when it uses information from a chunk, and to say clearly when the answer is not present in the provided context rather than inventing an answer. A RAG system that produces plausible-sounding hallucinations is worse than a system that honestly says "I don't know" — document this constraint in your system prompt ADR.

Wire this chain into the Chat page of the Knowledge application. The interface looks similar to the Phase 2 chat interface but has an additional feature: after each response, show the source chunks that were retrieved and used to generate the answer. This transparency — showing the retrieval step — is a key trust signal for users of any document-grounded system.

---

## Step 6 — Redis-backed persistent memory

Add Redis-backed memory to the RAG chain so that conversation history persists across server restarts. LangChain provides `RedisChatMessageHistory`, which stores message history in Redis keyed by session ID. Replace the in-memory buffer from Phase 2 with `RedisChatMessageHistory` across both the Chat application and the Knowledge Chat page.

The key design question is the memory scope: does the user have one conversation history shared across both the Chat and Knowledge Chat interfaces, or separate histories per application? Document your decision in an ADR. Separate histories per application is usually the right default — a user asking questions about uploaded documents has a different context than a user asking questions about platform data, and mixing them creates noise.

---

## Step 7 — Document-aware agents

Extend the DataAgent from Phase 3 to include a document retrieval tool. Define a `search_knowledge_base` tool using LangChain's tool interface that takes a query string and returns the top-k retrieved chunks from the vector store. Add this tool to the DataAgent's tool list in the LangGraph graph.

This means the Phase 3 agent pipeline can now answer questions that require both structured data (from the database) and unstructured knowledge (from uploaded documents), routing between these sources as needed. Update the supervisor's routing logic if necessary to handle tasks that clearly require document retrieval.

---

## Phase 4 checklist

- [ ] ADR written: embedding model choice and dimension, with consequences of changing it
- [ ] ADR written: chunking strategy — splitter type, chunk size, overlap, and reasoning
- [ ] ADR written: RAG chain system prompt and the no-hallucination constraint
- [ ] ADR written: Redis memory scope — shared or per-application history
- [ ] Knowledge application registered in the platform shell at `/knowledge`
- [ ] Knowledge sub-navigation: Documents (functional), Chat (functional), Explore (placeholder)
- [ ] pgvector extension confirmed active in schema.sql
- [ ] `documents` and `document_chunks` tables confirmed present with embedding column and ivfflat index
- [ ] Document upload interface working end-to-end: upload, extract, chunk, embed, store
- [ ] PDF extraction implemented and library choice documented in ADR
- [ ] `RecursiveCharacterTextSplitter` configured with documented chunk size and overlap
- [ ] LangChain `PGVector` integration storing and retrieving embeddings
- [ ] Retrieval tested directly against the vector store before wiring into the chain
- [ ] RAG chain built: retriever → prompt with context → LLM → structured output
- [ ] System prompt instructs LLM to cite sources and decline to hallucinate
- [ ] Knowledge Chat page shows retrieved source chunks alongside each answer
- [ ] Redis-backed `RedisChatMessageHistory` replacing in-memory buffer in all chat interfaces
- [ ] Memory scope decision documented in ADR
- [ ] Phase 3 DataAgent extended with `search_knowledge_base` tool
- [ ] LangGraph supervisor updated to route document-retrieval tasks appropriately
- [ ] All new functions documented with docstring or JSDoc
- [ ] All new functions have at least one test
- [ ] Retrieval quality evaluated with a manual test set of five question-chunk pairs
- [ ] AI-Driven Development validation review completed before PR opened
- [ ] CI pipeline passes
- [ ] Deployed to Dokploy live URL

---

*Phase 4 complete → PR opened and merged → open `05-phase-5-production.md`.*

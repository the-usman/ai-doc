# ADR-010 — RAG chain and the no-hallucination contract

**Date:** 2026-06-23
**Status:** Accepted
**Phase:** 4 — Knowledge (RAG)

### Context

The point of retrieval-augmented generation is to ground answers in the user's own
documents rather than the model's parametric memory. A naive "stuff the chunks into
the prompt and ask" approach still lets the model answer from general knowledge,
blend it with the retrieved text, or confidently invent a citation. For a knowledge
assistant whose value proposition is "answers you can trust, traceable to a source,"
that failure mode is the one that matters most. The chain therefore needs both a
prompt that constrains the model to the supplied context and a UI contract that lets
the user verify the grounding.

### Options considered

- **Plain LCEL with a permissive prompt.** Retrieve, format, ask. Simple, but the
  model is free to answer from outside knowledge and to hallucinate citations.
- **A strict, context-only system prompt plus structured output.** The system
  message forbids outside knowledge, requires inline citation of the document title,
  and mandates an explicit "not found in the documents" response when the context
  does not contain the answer; the model returns a typed object rather than free
  text so the answer and its "found" flag are machine-readable.
- **Post-hoc verification (a second model pass to check the answer against the
  context).** Stronger guarantees, but doubles latency and cost and adds a failure
  mode of its own; disproportionate for this phase.

### Decision

Build the RAG chain as **pure LCEL** —
`{context: retriever | format, question: passthrough} | prompt | model.with_structured_output(KnowledgeAnswer)`
— governed by a **strict, context-only system prompt** held in config
(`rag_system_prompt`).

The prompt instructs the model to answer using **only** the provided passages, to
**cite the document title in parentheses** when it uses a passage, and, when the
answer is not present in the context, to say plainly that it could not find it in
the uploaded documents — explicitly forbidding outside knowledge and invented
answers. Structured output (`KnowledgeAnswer` with `answer` and `answer_found`)
makes the refusal a typed signal rather than a phrase to parse.

Grounding is also made visible, not just asserted. The retrieval step runs once per
question; the chunks it returns are both formatted into the prompt context **and**
returned to the client as `SourceChunk`s (document title, similarity score,
snippet) so the Knowledge Chat page renders the exact passages that grounded each
answer. The user can see — and the developer can debug — precisely what the model
was given. Conversation history is included as prior turns so follow-up questions
have context, but history never substitutes for retrieval: every question
re-retrieves.

We deliberately do **not** add a second verification pass. The prompt-plus-visible-
sources approach gives the user the means to verify grounding themselves at no extra
latency, which is the right tradeoff for this phase.

### Consequences

- Answers are constrained to the corpus and are traceable: every reply ships with
  the passages behind it, and "I couldn't find that in your documents" is a typed,
  testable outcome rather than a hallucinated guess.
- The guarantee is prompt-driven, not enforced by a verifier, so it is strong but
  not absolute; a sufficiently adversarial query could still elicit a slip. The
  visible sources are the backstop that lets a user catch one.
- Returning sources alongside the answer shapes the API contract and the chat UI,
  and keeps the retrieval step observable for evaluation and debugging.
- Because the chain is plain LCEL with config-driven prompt and structured output,
  the system prompt can be tightened or the schema extended without rewriting the
  pipeline.

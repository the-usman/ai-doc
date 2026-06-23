"""Knowledge-base tool exposed to the agent pipeline.

``search_knowledge_base`` lets the Phase 3 DataAgent retrieve from uploaded
documents, so the agent can answer questions that need unstructured knowledge in
addition to the structured database tools. See Phase 4, Step 7 and ADR-007.
"""

from langchain_core.tools import tool

from app.knowledge import retriever


@tool
def search_knowledge_base(query: str) -> list[dict]:
    """Search the uploaded knowledge base for passages relevant to a query.

    Embeds the query and returns the most semantically similar document chunks
    from the vector store, each with its source document title and a similarity
    score. Use this whenever a question is about the *content of uploaded
    documents* — notes, specifications, reports, PDFs — rather than structured
    platform data such as user counts or sign-ins.

    Args:
        query: A natural-language description of what to look for.
    """
    rows = retriever.search_chunks(query)
    return [
        {
            "document_title": row["document_title"],
            "chunk_index": row["chunk_index"],
            "similarity": round(float(row["similarity"]), 4),
            "text": row["chunk_text"],
        }
        for row in rows
    ]


KNOWLEDGE_TOOLS = [search_knowledge_base]

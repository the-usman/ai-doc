# AI-Doc — Full Context and Development Record
### For standardisation, training, and future reference

---

## What this document is

This is the complete record of how AI-Doc was conceived, designed, and built as a developer training programme. It captures the reasoning behind every structural decision, the full scope of the current phases, and all supporting materials. Use it to run the programme with a new resource, to hand it off to another instructor, to add a new phase, or to adapt it for a different technical context. This document together with the repository is the complete handoff package.

---

## What AI-Doc is

AI-Doc is a personal developer platform and AI-engineering portfolio that resources build across a growing series of phases. It is a real multi-application product with a shared authentication layer, a PostgreSQL database, and a suite of AI-powered tools that grows with every new phase. There is no fixed end point. Each phase the resource completes adds a permanent layer to the same codebase, and new phases will be added to the programme as resources advance.

The name is plain English. A forge is where raw material is shaped into something useful and durable through disciplined, repeated work. That is exactly what the programme is. The goal is not to finish a curriculum — it is to develop an engineer. Each phase is a step in that direction, and the platform the resource is building is the accumulating evidence of the work.

The first five phases bring the resource from a blank repository to a production-grade, deployed, four-application platform with LangChain, LangGraph, RAG, observability, and an evaluated, hardened system. The phases beyond that go further — deeper LangChain patterns, more sophisticated agent architectures, evaluation at scale, deployment hardening, and integrations with real external systems. All of it builds on the same codebase.

---

## The multi-application platform architecture

AI-Doc is not a single-purpose application. It is a platform — a container that holds multiple applications under a single sign-on, each with its own navigation, its own sub-menus, and its own URL namespace. Adding a new application means registering it in a central configuration file: a name, an icon, a root path, and a sub-navigation definition. The shell reads that configuration and builds the top-level navigation automatically. The authentication layer, the database, and the navigation chrome are never touched when a new application is added.

This is the architectural pattern underlying every serious SaaS product. Understanding it from the inside — by having built it from scratch in Phase 1 — is one of the most transferable things this programme teaches. A resource who has built the shell can explain why Google Workspace works the way it does, and can design a similar structure in a client engagement without needing to look it up.

The current application map is below. Each new phase that introduces a significant new capability will add a new application to this map.

| Phase | Application | Path | Sub-pages |
|---|---|---|---|
| Phase 1 | Home | `/` | Overview, Settings |
| Phase 1 | Docs | `/docs` | Architecture, Decisions, Runbook, API Reference, Security (Phase 5), Case Study (Phase 5) |
| Phase 2 | Chat | `/chat` | Conversation, History, Settings |
| Phase 3 | Agents | `/agents` | Pipeline, Run History, Configuration |
| Phase 4 | Knowledge | `/knowledge` | Documents, Chat, Explore |
| Phase 6+ | To be defined | TBD | TBD |

---

## Origin and intent

AI-Doc was designed to fill a specific gap in the TSS resource development pipeline. Resources who complete the AI-LMS assignment have strong learning habits and solid foundational knowledge. What they typically lack is a cohesive portfolio piece — a single deployed system they can demonstrate end-to-end and explain under questioning. Most junior-to-mid developers who enter the pipeline have built things, but not with professional discipline. They have committed secrets to repositories. They have not written Architecture Decision Records. They have not separated development and production configurations. They cannot explain their design choices because those choices were made impulsively rather than consciously.

Forge addresses this not by teaching these practices as concepts but by making them unavoidable in practice. The resource does not read about ADRs — they write four of them in Phase 1 alone. They do not read about TDD — they write a failing test before writing the code that makes it pass. They do not read about production Docker configurations — they review both compose files side by side and find the differences themselves. The discipline is embedded in the structure of the programme, not appended as advice.

---

## Design decisions and reasoning

**Why a single growing application rather than separate projects per phase?**

Separate projects produce half-finished things that are hard to present as a coherent body of work and impossible to demonstrate as a system. A single application that grows across every phase produces one deeply understood thing. The database schema used in Phase 4 is the same schema created in Phase 1 — with tables added, but not replaced. The authentication system built in Phase 1 is the same system protecting the Phase 8 pipeline. Choices have consequences and context accumulates. This is how real professional software development works, and it is the most honest way to teach it.

**Why the multi-application platform architecture?**

The platform shell — where each tool registers under a shared authentication layer and its own URL namespace — teaches a pattern that most junior developers have never built from scratch. Understanding the separation between the identity layer, the navigation shell, and the individual applications is what allows an engineer to add new capabilities without rewriting the authentication system. The architecture was designed specifically so that adding a new phase means adding a new application entry, not restructuring the existing code. This constraint keeps the programme extensible indefinitely.

**Why the LangChain stack specifically?**

LangChain is the dominant framework for production AI application development. Its abstractions — the Runnable interface, LCEL, output parsers, tool binding, retrievers — appear in real client codebases more than any competing framework. Teaching LangChain across phases 2, 3, and 4 means resources arrive at client engagements with direct applicable experience rather than general AI knowledge that needs to be translated. The coverage is deliberate in its progression: Phase 2 covers core abstractions and chains before introducing agents, Phase 3 covers LangGraph's stateful multi-agent model, Phase 4 covers the retrieval stack and vector store integrations. Future phases will go deeper into the same stack — advanced retrieval strategies, custom callbacks, fine-tuned evaluation — rather than switching to different tools. Depth in one framework is more valuable at a client engagement than superficial knowledge of many.

**Why LangGraph for multi-agent work?**

LangGraph is the framework LangChain recommends for production multi-agent systems. The supervisor-and-worker pattern it implements is the standard pattern for agent orchestration that resources will encounter in real AI product work. More importantly, LangGraph forces the resource to think about state explicitly — what is in the state object, how each node updates it, what the routing conditions are. This explicit state thinking is the mental model that generalises to every agentic system, regardless of framework.

**Why is the SDLC explicit rather than assumed?**

Most junior developers have heard of the SDLC but have never applied it to their own work. Making it explicit in `00-overview.md` and threading it through every phase document turns it from an abstract principle into a practised habit. The habit is formed through repetition across phases, not through a single instruction.

**Why AI-Driven Development throughout?**

Resources will work with AI tools throughout their careers. The question is not whether they use them but whether they use them in a way that makes them better engineers or in a way that creates dependency without understanding. The AI-Driven Development protocol — using AI as a thinking partner across the SDLC, with the validation rule that every AI output must be read, run, and understood before merging — teaches the productive mode directly. The documentation rule — every function must have a docstring the developer writes themselves — is the specific practice that enforces understanding. You cannot document a function you do not understand.

**Why live presentations at Phase 1 and at the end of every major capability phase?**

Phase 1 establishes early that demonstrating and explaining work is as much part of the deliverable as building it. Phase 5 ends with a session that mirrors the format of a real technical client engagement. Every subsequent phase that introduces a significant new capability — agents, a new integration, a new architecture pattern — will also end with a live session. The ability to explain what you built under questioning is the final test of whether you actually understand it.

---

## The LangChain stack coverage — current phases

This table is a living map. It grows as phases are added. The current entries cover what is introduced in Phases 1 through 5. Future phases will add entries to this table as new components of the LangChain ecosystem are introduced and practised.

| Component | Phase introduced | What it teaches |
|---|---|---|
| Runnable interface | Phase 2 | Core abstraction underlying all LangChain composition |
| LangChain Expression Language (LCEL) | Phase 2 | Chain composition with the pipe operator |
| ChatPromptTemplate | Phase 2 | Structured multi-turn prompt formatting |
| Output parsers — Str, JSON, Pydantic | Phase 2 | Structured and validated LLM output |
| Structured output with `with_structured_output` | Phase 2 | Schema-validated LLM responses |
| Tool definition with `@tool` decorator | Phase 2 | Giving the LLM callable functions |
| Tool binding with `bind_tools` | Phase 2 | Attaching tools to a model in an LCEL chain |
| Conversation memory with BufferWindowMemory | Phase 2 | Multi-turn context within a session |
| LangServe | Phase 2 | Deploying LCEL chains as production REST APIs |
| LangGraph StateGraph | Phase 3 | Stateful directed graph for agent orchestration |
| LangGraph nodes and conditional edges | Phase 3 | Routing logic and unit-of-work pattern |
| Supervisor-and-worker pattern | Phase 3 | Multi-agent delegation and synthesis |
| ReAct agent with `create_react_agent` | Phase 3 | Worker agent implementation |
| RedisChatMessageHistory | Phase 4 | Persistent cross-session agent memory |
| RecursiveCharacterTextSplitter | Phase 4 | Document chunking for RAG |
| Embedding models — OpenAIEmbeddings and equivalents | Phase 4 | Converting text to semantic vectors |
| PGVector integration | Phase 4 | LangChain vector store backed by pgvector |
| LangChain retrievers | Phase 4 | Semantic search abstraction for RAG chains |
| RAG chain with retrieval injection | Phase 4 | Full retrieval-augmented generation pipeline |
| LangSmith tracing | Phase 5 | Full observability across all LangChain operations |
| LangSmith datasets and evaluation | Phase 5 | LLM-as-judge evaluation framework |

---

## Repository structure

```
ai-doc/
  README.md
  00-overview.md
  01-phase-1-foundations.md
  02-phase-2-langchain.md
  03-phase-3-agents.md
  04-phase-4-rag.md
  05-phase-5-production.md
  06-phase-N-[name].md          ← added here as new phases are written
  docs/
    setup.md              — senior developer practices, applied before Phase 1
    decisions.md          — ADR template and running log
    runbook.md            — how to run locally and deploy
  schema/
    schema.sql            — single source of truth, idempotent, grows across phases
  docker/
    docker-compose.yml
    docker-compose.prod.yml
    .env.example
  automations/
    pipeline_trigger.json — exported by resource in Phase 3
  evals/
    eval_set.json         — created in Phase 5
    run_evals.py          — eval harness script
  .github/
    workflows/
      ci.yml
    PULL_REQUEST_TEMPLATE.md
    ISSUE_TEMPLATE/
      phase-checklist.md
```

---

## How to add a new phase

Adding a phase to Forge takes four steps. First, write the phase document following the structure of the existing phase files — a clear statement of what is being built and why, the SDLC-driven steps in order, a documentation and testing requirement in every step, a checklist, and a PR gate. Name it `0N-phase-N-name.md` and add it to the repository root.

Second, update this context file: add the phase to the LangChain stack coverage table if it introduces new framework components, update the platform application map if it adds a new application, and add the phase to the README phase list.

Third, if the new phase adds database tables, add them to `schema/schema.sql` with `IF NOT EXISTS` guards, following the established pattern.

Fourth, open a GitHub Issue for the resource with the phase checklist.

No other files need changing. The platform shell is designed to accept new applications through registration. The CI pipeline works for all phases without modification. The `schema.sql` pattern is forward-compatible by design.

---

## Instructor pre-flight checklist

Complete every item below before sharing the repository link with the resource. Do not send the assignment until this list is fully ticked.

**TSS server setup — one per resource:**

- [ ] Dokploy project created for the resource
- [ ] Dokploy login credentials generated and shared (server URL, username, password)
- [ ] Domain assigned (e.g. `name.tss-domain.com`)
- [ ] Database port opened on the TSS server for this instance
- [ ] Resource can reach their Dokploy panel from a browser

**GitHub setup:**

- [ ] Resource GitHub username collected
- [ ] Resource given access to the AI-Doc template repository
- [ ] Resource has forked the repository to their own account
- [ ] Forked repository link received from resource
- [ ] Instructor added as admin to the resource's fork so PRs can be reviewed

**Resource access confirmation — receive these from the resource before they begin:**

- [ ] GitHub username provided and fork confirmed
- [ ] Claude.ai access confirmed
- [ ] Docker Desktop installed locally and confirmed running
- [ ] Resource has read and acknowledged `00-overview.md`

Only hand over the assignment after all boxes are ticked.

---

## Assignment delivery method

The resource receives the repository link. A GitHub Issue is opened for Phase 1. For each phase, the workflow is: create a branch, work through the phase document, tick the checklist items in the Issue, open a Pull Request using the PR template, receive a review and approval, merge, then open the next Issue.

No status update meetings are needed. The commit history, Issues, and PRs provide full visibility. TSS reviews PRs within two working days — a PR that sits unreviewed longer than that is a blocker and should be flagged.

---

## Phase gates

Phase 1 does not close without the live demonstration being delivered. Phase 5 does not close without the live presentation being delivered. Every subsequent phase that introduces a significant new system capability has its own live session requirement, documented in the phase file.

---

## Items not yet built

The `automations/` folder needs a README explaining the expected n8n workflow export format and import instructions. The `evals/` folder needs a starter `eval_set.json` template showing the expected format. A `Dockerfile.dev` starter template should be added to the repository so resources have a working development image to extend rather than writing one from scratch. The Security page of the Docs application should have a template with the OWASP Top 10 headings pre-populated. Phase 6 and beyond are not yet written — the next phase should deepen LangChain agent patterns (tool calling strategies, custom callbacks, or structured output at scale) before introducing entirely new system capabilities.

---

*AI-Doc — TSS Developer Training Programme — Full Context Document*
*Version 1.0 — May 2026*

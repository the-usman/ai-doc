# Phase 2 — LangChain

**Duration:** Weeks 3 to 5
**Branch:** `phase-2/langchain`
**Deliverable:** A LangChain-powered chatbot registered as the third application in your platform shell, built using LCEL, with structured output parsing, tool use, and an API endpoint served via LangServe. A working MCP server exposing your tools.

---

## What you are building

Phase 2 adds the LangChain application to your platform. A user signs in, navigates to the Chat application in the platform switcher, and has a structured conversation with an LLM that has access to real tools backed by your PostgreSQL database. The conversation history is maintained correctly across turns. Tool calls are transparent — the user can see when the agent queried data. Responses are structured and predictable, not free-form text that happens to contain the information.

This phase teaches the LangChain ecosystem from its core abstractions outward. You will not start with agents or chains. You will start with the fundamental building blocks — prompts, models, output parsers — and compose them using LCEL before adding the higher-level constructs on top. This bottom-up approach matters because it means you understand what LangChain is doing on your behalf rather than treating it as a black box that sometimes produces the answer you wanted.

---

## Understanding LangChain before building with it

LangChain is a framework for composing language model applications. Its fundamental insight is that LLM applications are not single API calls — they are pipelines of steps where the output of one step becomes the input of the next, with the LLM being one step among several. LangChain gives you a standardised way to describe, compose, and run those pipelines.

Before writing any code, ask Claude to explain the following four concepts to you in plain English, and do not proceed until you can explain each one back to Claude in your own words.

The first is the Runnable interface. Everything in LangChain implements the same interface: it has an `invoke` method that takes input and produces output. A prompt template is a Runnable. A model is a Runnable. An output parser is a Runnable. This uniformity is what makes composition possible — you can chain any two Runnables together because they speak the same language.

The second is LangChain Expression Language, or LCEL. LCEL is the syntax for composing Runnables into chains using the pipe operator. `prompt | model | parser` is an LCEL chain that passes the output of the prompt template into the model, then passes the model's output into the parser. The chain itself is also a Runnable, so it can be composed with other chains. Understanding LCEL is the foundation for everything that follows in this phase.

The third is prompt templates. A prompt template is a reusable prompt with variable placeholders. When you invoke a prompt template with a dictionary of values, it returns a formatted prompt ready to send to the model. LangChain provides `ChatPromptTemplate` for chat models, which formats messages with roles (system, human, assistant) rather than as a single string.

The fourth is output parsers. The raw output of an LLM is a string. Output parsers transform that string into a structured Python or TypeScript object. `StrOutputParser` gives you the string directly. `JsonOutputParser` parses the output as JSON. `PydanticOutputParser` validates the output against a Pydantic model, which gives you both type safety and useful error messages when the LLM produces malformed output.

Once you can explain all four of these concepts in plain English, you are ready to start building.

---

## Step 1 — Chat application registration

Register the Chat application in your platform shell. It lives at the path `/chat` and has three sub-pages accessible from its own sub-navigation: Conversation (the main chat interface), History (a log of past sessions), and Settings (model selection and system prompt configuration). Only the Conversation page needs to be functional in Phase 2. History and Settings can be placeholders that you will revisit in Phase 3 and beyond.

The Chat application's sub-navigation should be visible and usable as soon as the user switches to it. It should disappear — or be replaced — when the user switches to a different application. This is the sub-navigation separation that the platform shell architecture was designed for.

---

## Step 2 — LangChain core setup

Install LangChain and the relevant model integration package for your chosen LLM provider — `langchain-anthropic` for Claude or `langchain-openai` for OpenAI. Also install `langchain-core`, which provides the base abstractions.

Build your first LCEL chain before adding any application logic. The chain should: take a user message as input, format it with a `ChatPromptTemplate` that includes a system message describing the assistant's purpose, pass the formatted messages to the LLM, and pass the model's response through a `StrOutputParser` to get a clean string. Test this chain independently — invoke it with a test message and confirm it returns a sensible response. This is your baseline before adding any complexity.

Document what each step in the chain does in your ADR for this phase. Explain why the chain is built with LCEL rather than by calling the LLM directly. The answer — composability, streaming support, automatic tracing with LangSmith, and consistent interface for testing — is worth understanding and articulating.

---

## Step 3 — Structured output

Add a structured output layer to your chain. Instead of returning a raw string, the chain should return a structured object — for example, an object with a `response` field for the text answer, a `confidence` field rated low, medium, or high, and a `sources` field listing any tools that were called.

Use LangChain's `with_structured_output` method on the model, passing a Pydantic model or a JSON schema as the structure definition. This instructs the LLM to format its output to match the schema, and LangChain handles the validation and parsing automatically.

Test structured output with a few known inputs and verify that the returned object always matches the expected schema. Edge case to test: what happens when the LLM's response does not cleanly fit the schema? Document what LangChain does in this case and how your application should handle it.

---

## Step 4 — Tools and tool binding

LangChain's tool system gives the LLM the ability to call functions during a conversation. When you bind a tool to a model, the model can choose to call that tool at any point during its response generation — your code executes the function, returns the result to the model, and the model incorporates it into its final answer.

Define at minimum two tools using LangChain's `@tool` decorator or the `Tool` class: a `get_platform_user_count` tool that queries the users table and returns the current count, and a `get_recent_signins` tool that accepts an integer parameter N and returns the N most recent sign-in events from the sessions table. Both tools must query the real PostgreSQL database — not mock data.

Bind both tools to your LLM using the model's `bind_tools` method and update your LCEL chain to include tool call handling. The updated chain must handle the case where the model calls a tool and the case where it does not — both paths should produce a clean final response. Test that asking "how many users are registered?" causes the model to call `get_platform_user_count` and incorporate the result into its answer.

Document each tool with a docstring that explains what it does, what it queries, and what it returns. The docstring is especially important for tools because LangChain passes it to the LLM as part of the tool description — a good docstring directly improves the LLM's ability to decide when and how to use the tool.

---

## Step 5 — Conversation memory

Wire up LangChain's conversation memory so that the chat maintains context across multiple turns. Without memory, every message is treated as the first message in a fresh conversation — the LLM has no awareness of what was said earlier in the same session.

LangChain provides `ConversationBufferWindowMemory` for a sliding window of recent messages, and `ConversationSummaryMemory` for a compressed summary of older context. Start with `ConversationBufferWindowMemory` with a window of ten turns. Store the memory by session ID so that different users have independent conversation histories. The session ID from your Phase 1 authentication system is the right key.

Test that the chatbot correctly remembers the context of earlier messages within a session. A good test is a two-turn conversation where the second message refers to something from the first: "Tell me how many users are registered" followed by "And how many of those signed in this week?" — the second question is only answerable if the bot remembers the context of the first.

---

## Step 6 — LangServe

LangServe is the LangChain component for deploying chains as production-ready REST APIs. It takes an LCEL chain and automatically generates API endpoints for it, including a `/invoke` endpoint, a `/stream` endpoint for streaming responses, and a `/playground` page for interactive testing directly in the browser.

Wrap your LangChain chat chain with LangServe in your FastAPI application. The chain is served at `/api/chat`. The `/api/chat/playground` page becomes a useful development and demonstration tool — document it in your API Reference page in the Docs application.

Using LangServe instead of writing manual API routes teaches the right pattern for productionising LangChain applications. It is not just convenience — LangServe adds input validation, schema exposure, and streaming support that would take significant manual work to replicate correctly.

---

## Step 7 — MCP server

Build a minimal MCP server that exposes your LangChain tools as MCP-compatible endpoints. MCP — Model Context Protocol — is the standardised protocol that allows AI agents and clients to discover and call tools through a consistent interface. By implementing an MCP server in Phase 2, you establish the tool infrastructure that Phase 3's agents will call directly.

Your MCP server exposes the same tools defined in Step 4. It runs as a separate Docker service. The server must respond to a tool manifest request with a valid JSON description of the available tools, and must handle tool call requests by executing the corresponding database query and returning the result.

Document MCP in your Architecture page: what it is, what problem it solves, and how your implementation fits into the standard. The explanation should be clear enough for a non-technical client to understand why it exists.

---

## Phase 2 checklist

- [ ] ADR written: LangChain architecture decisions for this phase (LCEL chain design, tool definitions, memory approach)
- [ ] Chat application registered in the platform shell at `/chat`
- [ ] Chat sub-navigation: Conversation, History, Settings (History and Settings can be placeholders)
- [ ] LangChain and relevant model integration packages installed
- [ ] LCEL chain built: prompt template → model → output parser
- [ ] LCEL chain tested independently before any application logic is added
- [ ] Structured output implemented: response, confidence, and sources fields validated
- [ ] `get_platform_user_count` tool defined, bound to model, and queries real database
- [ ] `get_recent_signins` tool defined, bound to model, and queries real database
- [ ] Both tools documented with docstrings that also serve as LLM tool descriptions
- [ ] Tool call loop tested end-to-end: model calls tool, result returned, model incorporates it
- [ ] Conversation memory wired with session ID keying
- [ ] Multi-turn memory tested: second message can reference context from first
- [ ] LangServe serving the chat chain at `/api/chat` with `/playground` accessible
- [ ] MCP server running as a Docker service with tool manifest endpoint
- [ ] API Reference page in Docs updated with LangServe endpoints
- [ ] Every new function documented with docstring or JSDoc
- [ ] Every new function has at least one test
- [ ] AI-Driven Development validation review completed before PR opened
- [ ] CI pipeline passes
- [ ] Deployed to Dokploy live URL

---

*Phase 2 complete → PR opened and merged → open `03-phase-3-agents.md`.*

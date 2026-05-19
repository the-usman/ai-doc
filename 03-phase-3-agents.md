# Phase 3 — Agents

**Duration:** Weeks 5 to 7
**Branch:** `phase-3/agents`
**Deliverable:** A LangGraph-powered multi-agent system registered as the Agents application in the platform shell, implementing a supervisor-and-worker pattern with at least two specialised worker agents. An n8n workflow that triggers the agent pipeline autonomously on a schedule or webhook. Results visible in the platform.

---

## What you are building

Phase 2 gave you a chatbot — a single LLM call per message, managed by a chain. Phase 3 upgrades that into an orchestrated system where multiple agents collaborate on a task, each with a specific responsibility, coordinated by a supervisor that decides who should act next and when the task is complete.

The difference is not just architectural complexity. It reflects a genuinely different capability. A single agent can answer a question. A multi-agent system can decompose a complex task into sub-tasks, assign each sub-task to the agent best suited to handle it, gather and synthesise the results, and return a coherent final output — all without a human orchestrating each step. This is the pattern underlying most serious AI product work in the market today.

The n8n integration removes the human from the initiation step entirely. When the workflow fires on its schedule, the agent pipeline runs, the workers execute, and the results appear in the database and the platform — with no one pressing a button. Autonomy is the point.

---

## Understanding LangGraph before building with it

LangGraph is LangChain's framework for building stateful, multi-step agent systems. Its fundamental model is a directed graph where each node is a function that transforms state, and edges define the routing logic — which node runs next, under what conditions.

The key mental shift from LangChain chains to LangGraph graphs is the introduction of explicit state. In an LCEL chain, data flows through in a single pass. In a LangGraph graph, state is a typed object that accumulates information as it passes through nodes, persists across turns in a conversation, and can branch into different paths depending on what has happened so far.

Before writing any code, ask Claude to explain the following concepts in plain English and do not proceed until you can explain each one back in your own words.

The `StateGraph` is the object you use to define the graph. You tell it what state looks like (using a TypedDict in Python or a typed interface in TypeScript), you add nodes, and you add edges. When you compile the graph, you get a Runnable that accepts the initial state and runs the graph until it reaches the END node.

A node is a Python or TypeScript function that takes the current state and returns an updated state. It is the unit of work. A node might call an LLM, use a tool, run a database query, or just transform data — what makes it a node is that it reads from the shared state and writes back to it.

An edge is a routing instruction. A normal edge says "always go from node A to node B." A conditional edge says "look at the current state and decide which node to go to next." The conditional edge is what gives LangGraph its flexibility — the supervisor node uses a conditional edge to decide whether to route to worker A, worker B, or END depending on what the task requires.

The supervisor-and-worker pattern is the most important pattern you will learn in this phase. The supervisor receives the incoming task, analyses what needs to be done, and routes to the appropriate worker. Each worker executes its specialised task using tools, then returns control to the supervisor. The supervisor evaluates the worker's output and either routes to another worker or ends the run. This pattern is infinitely extensible — adding a new capability means adding a new worker node, not restructuring the whole system.

---

## Step 1 — Agents application registration

Register the Agents application in the platform shell at the path `/agents`. Its sub-navigation has three pages: Pipeline (the main interface for triggering and viewing agent runs), Run History (a log of completed pipeline executions with their results), and Configuration (settings for worker types and system prompts). The Pipeline page needs to be functional in Phase 3. The others can be placeholders.

The Agents application has its own visual identity within the platform shell — it is a different tool from the Chat application, even though both use LLMs under the hood.

---

## Step 2 — Agent state design

Before writing a single node, design your state object. The state is the shared context that every node reads from and writes to. Getting the state design right before building is one of the most important habits this phase teaches — a poorly designed state object causes constant friction as the graph grows, because every node has to work around what the state can and cannot hold.

For the AI-Doc agent pipeline, the state should hold at minimum: the incoming task description, the supervisor's routing decision (which worker to call next), the list of worker results accumulated so far, the current status of the run (in progress, completed, or failed), and the final synthesised output.

Document the state design as an ADR before writing any node. The ADR should explain each field, why it exists, and what would go wrong if it were missing.

---

## Step 3 — Supervisor node

The supervisor is the first node in the graph and the node the graph returns to after each worker completes. It receives the current state, reads the task and any worker results so far, and makes a routing decision: call worker A, call worker B, or end the run.

Implement the supervisor as a LangChain LCEL chain. The supervisor's prompt should instruct the LLM to act as an orchestrator — to read the task, assess what has been done and what still needs doing, and output a structured routing decision. Use structured output for the routing decision: an object with a `next` field that contains either the name of the worker to call or the string "FINISH". This makes the conditional edge logic in the graph trivially simple — check the `next` field and route accordingly.

---

## Step 4 — Worker agents

Define at minimum two worker agents. Their specific responsibilities should reflect the data available in your system — reasonable examples are a DataAgent that answers questions about users and session activity using the tools from Phase 2, and a ReportAgent that synthesises accumulated results into a brief structured summary. Document the purpose and tool access of each worker in an ADR.

Each worker is a LangGraph node — a function that takes the current state, runs a LangChain agent (a ReAct agent using `create_react_agent` from LangChain is the right pattern here), and returns an updated state with the worker's result appended. Each worker has access to a specific set of tools from the MCP server — extend the MCP server with any new tools the workers need, following the same pattern established in Phase 2.

Test each worker node independently by calling it with a mock state object before assembling the full graph. A worker that you have tested in isolation is far easier to debug when the full graph behaves unexpectedly, because you can rule out the worker itself as the source of the problem.

---

## Step 5 — Graph assembly and compilation

Assemble the full graph. Add the supervisor node, both worker nodes, and the END node. Add the edges: a conditional edge from the supervisor that routes to the correct worker or to END based on the `next` field in the state, and normal edges from each worker back to the supervisor. Compile the graph.

Test the full graph with at least three distinct task inputs: one that requires only the DataAgent, one that requires only the ReportAgent, and one that requires both in sequence. For each test, inspect the state at each node transition to confirm the routing is correct and the state is accumulating results as expected. LangGraph's built-in trace output is useful here — log it during development and reference it when the routing behaves unexpectedly.

The Pipeline page in the Agents application should display the current run state as the graph executes — not just the final result. Showing the intermediate steps (which worker ran, what it returned) makes the system transparent and demonstrable.

---

## Step 6 — Persisting and displaying results

Write completed pipeline runs to the database. Create a `pipeline_runs` table in `schema/schema.sql` with fields for a UUID primary key, the task description, the final output, the complete run trace as a JSON field (the accumulated worker results), the run status, timestamps, and a foreign key to the user who triggered the run.

The Run History page in the Agents application reads from this table and displays completed runs in reverse chronological order. Each run should be expandable to show the full trace — which workers were called, in what order, and what each one returned.

---

## Step 7 — n8n automation

Install n8n or use an existing instance. Create a workflow that fires on a schedule — daily at a fixed time is a good starting point — and sends an HTTP POST request to a dedicated trigger endpoint in your application. The payload is a task description. The trigger endpoint starts the LangGraph pipeline, saves the run to the database, and returns immediately with a run ID. The workflow logs the response.

This makes the pipeline autonomous. When the n8n workflow fires, the pipeline runs without a human initiating it, and the results appear in the Run History page the next time someone opens the Agents application.

Export the workflow as JSON and commit it to `automations/pipeline_trigger.json`. Any developer who sets up the project can import the file into their n8n instance and have the automation running within minutes.

---

## Phase 3 checklist

- [ ] ADR written: LangGraph state design with field-by-field reasoning
- [ ] ADR written: supervisor routing logic and worker responsibilities
- [ ] Agents application registered in the platform shell at `/agents`
- [ ] Agents sub-navigation: Pipeline (functional), Run History (functional), Configuration (placeholder)
- [ ] `StateGraph` implemented with typed state object
- [ ] Supervisor node implemented using LCEL chain with structured routing output
- [ ] DataAgent worker node implemented with tools from MCP server
- [ ] ReportAgent worker node implemented with synthesis tools
- [ ] Each worker node tested independently with mock state before graph assembly
- [ ] Full graph assembled with correct conditional edges
- [ ] Three distinct tasks tested end-to-end through the full graph
- [ ] Pipeline page shows intermediate steps during execution
- [ ] `pipeline_runs` table in schema.sql
- [ ] Completed runs persisted to database
- [ ] Run History page displays completed runs with expandable trace
- [ ] n8n workflow triggers the pipeline on a schedule
- [ ] n8n workflow JSON exported to `automations/pipeline_trigger.json`
- [ ] MCP server extended with any new tools required by workers
- [ ] All new functions documented with docstring or JSDoc
- [ ] All new functions have at least one test
- [ ] AI-Driven Development validation review completed before PR opened
- [ ] CI pipeline passes
- [ ] Deployed to Dokploy live URL

---

*Phase 3 complete → PR opened and merged → open `04-phase-4-rag.md`.*

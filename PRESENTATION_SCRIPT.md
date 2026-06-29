# AI-Doc — Project Presentation Script (20 minutes)

> **Setup before you start:** Live app open in one tab, GitHub repo in another, project board in a third. Camera on, mic checked. Take a breath before you begin.
>
> Spoken parts are what you say out loud. **[SHOW: …]** lines are screen cues. **⏱** markers keep you on time. Written to land at roughly 20 minutes at a calm, normal pace.

---

## PART 1 — Set the ground: what I was asked to do  ⏱ 0:00–3:00

> *Plain language, no jargon. If you must use a technical word, define it in one sentence.*

"Hi everyone, thanks for your time. Over the next twenty minutes I'm going to walk you through a project I built called **AI-Doc**. I'll explain what it is, how I planned it, how I built it, then I'll show it working live, and finish with a quick look at the GitHub repository. Please hold any questions to the end — I've left ten minutes for those.

Let me start with the problem, because if this part is clear, everything else will make sense.

The task was to build a **developer platform** — not a single app, but a container that holds several different applications under **one login**. The best way to picture it is Google Workspace. When you log into Google, you sign in once, and then you can move between Gmail, Calendar, Docs, and Drive without logging in again. Each of those is its own application with its own menus, but they share one identity and one account.

AI-Doc works exactly the same way. You sign in once at the platform level, and then you can switch between several applications — a home dashboard, a chat assistant, an AI agents panel, and a knowledge base — each with its own pages, all sharing the same login and the same database.

**Why does this matter?** Because building things this way is how real products grow. Instead of building five separate tools with five separate logins, you build one platform and add applications into it over time. The hard part — security, login, navigation — is solved once and reused everywhere.

So what did a finished version need to do? Three things. **One**, a user signs in securely with their existing Google or GitHub account. **Two**, once signed in, they can move between several applications from a shared menu. **Three**, those applications actually do useful AI work — answering questions, running automated tasks, and searching uploaded documents.

The project was built in **phases**, where each phase adds a new application to the same codebase without breaking what came before. That's the whole idea — it grows."

---

## PART 2 — How I planned it  ⏱ 3:00–6:00

> **[SHOW: project board / tickets tab]**

"Before writing any code, I broke the work down by phase, and each phase became a set of tickets on this board.

**[SHOW: point at the columns / tickets]**

The plan was deliberately ordered so that each phase depended on the one before it:

- **Phase 1 — Foundations.** Get the platform shell, the login, the database, and Docker working first. Nothing else can exist until a user can sign in and the apps have a frame to live in.
- **Phase 2 — Chat.** Add the first real application: an AI chat assistant.
- **Phase 3 — Agents.** Add a multi-step AI pipeline that can run on its own.
- **Phase 4 — Knowledge.** Add a document search tool that answers questions from uploaded files.
- **Phase 5 — Production.** Deploy it live and harden it.

I built them in that order on purpose — foundations first, then one application at a time.

I also made a few key decisions early and wrote them down as short documents called **ADRs** — Architecture Decision Records. That's just a one-page note explaining *why* I made a choice, so that six months later the reasoning isn't lost.

**[SHOW: briefly open docs/adr folder on GitHub if quick]**

A few examples of those early decisions:

- I chose **PostgreSQL** as the database because I needed both normal data and, later, AI vector search — and one database extension gives me both.
- I chose to handle login on the **backend**, not the frontend, so secrets never touch the browser.
- I decided the database schema would be written **once, up front**, covering all phases, so the database design stays in a single file instead of drifting across the project.

So the plan was: solid foundations, one application per phase, and decisions documented as I went."

---

## PART 3 — How I implemented it  ⏱ 6:00–12:00

> **[SHOW: GitHub repository tab]** This is a guided tour, not a line-by-line code read.

"Now let me show you how it's actually built.

**[SHOW: repo root, then the folder structure]**

The project splits into two halves and a shared database.

The **frontend** — what you see in the browser — is built with **React**. That's a popular tool for building web interfaces. The **backend** — the engine behind it — is built with **FastAPI**, which is a Python framework for building web services. And the **database** is PostgreSQL.

**[SHOW: frontend/src/platform/appRegistry.ts]**

Let me show you the single most important file, because it's the heart of the 'platform' idea. This file is a **registry** — basically one list — of every application on the platform. Each entry is just a name, an icon, a web address, and its menu items.

**[SHOW: scroll through the APP_REGISTRY entries]**

When I want to add a new application, I add **one entry here**, and the platform automatically builds the navigation for it. I don't touch the login, I don't touch the menu code. That's what makes this a platform and not just a pile of separate apps — and honestly it's the part I'm most proud of.

**[SHOW: backend/app/main.py]**

On the backend side, here's the entry point. Each application — chat, agents, knowledge — is registered here, but notice they're wrapped in guarded imports. **[SHOW: the try/except registration blocks]** What that means in plain terms: if one of the heavier AI applications isn't available, the rest of the platform keeps running. The login and the core never go down because of an optional feature. That was a deliberate safety choice.

Let me touch on the three AI applications quickly.

**[SHOW: backend/app/chat folder]**

The **Chat** app uses **LangChain**, a toolkit for building AI chat features. What makes mine more than a plain chatbot is that it's connected to the database through **tools** — so it can answer real questions like 'how many users have signed up?' by actually looking it up, not guessing.

**[SHOW: backend/app/agents/graph.py]**

The **Agents** app is the most advanced part. It's a **supervisor-and-workers pipeline** built with **LangGraph**. Think of it like a small team: a supervisor reads the task and decides which specialist to hand it to. One worker — the Data Agent — looks up facts. Another — the Report Agent — writes the result up. The supervisor keeps routing between them until the job is done. **[SHOW: the build_graph function and the START → supervisor → workers structure]** Every run is saved to the database with a full trace of what happened, so you can look back at exactly how it reached its answer.

**[SHOW: backend/app/knowledge folder]**

The **Knowledge** app is what's called **RAG** — retrieval-augmented generation. In plain terms: you upload a document, the system breaks it into small pieces, converts each piece into numbers that capture its meaning, and stores them. Later, when you ask a question, it finds the most relevant pieces and gives them to the AI as background so the answer is grounded in your actual documents, not made up.

**The hardest part** for me was Phase 3, the agents pipeline. Getting the supervisor to reliably decide *when to stop* was tricky — early on it would loop, handing work back and forth without finishing. I worked through it by giving the supervisor a clear 'finish' signal and testing the routing logic on its own, separately from the AI, so I could prove the wiring was correct before involving the model. **[SHOW: tests folder, the agents test files]** You can see that in the test suite — there's a test file for each piece of the pipeline."

---

## PART 4 — The execution: show it working live  ⏱ 12:00–17:00

> **[SHOW: live project tab]** Walk through it as a real user. Be honest about rough edges.

"Now let me show you the real thing, working live.

**[SHOW: the sign-in page]**

Here's the platform. The first thing any user hits is the sign-in screen. I'll sign in with Google.

**[ACTION: sign in]**

And we're in. Notice I only signed in once. Now look at the top — **[SHOW: the app switcher / nav]** — these are the applications: Home, Chat, Agents, Knowledge, and Docs. I can move between all of them without logging in again. That's the single sign-on working.

**[SHOW: Chat app]**

Let me open **Chat** and ask it something that needs real data — I'll ask, 'how many users are registered on the platform?'

**[ACTION: send the message, wait for the grounded answer]**

There — it didn't guess. It actually queried the database through its tools and gave the real number.

**[SHOW: Agents app → Pipeline]**

Now the **Agents** app. I'll give the pipeline a task and run it.

**[ACTION: trigger a run]**

**[SHOW: Run History]**

And here on the Run History page you can see the completed run, with the trace of which workers were involved. This same pipeline can also be triggered automatically on a schedule by an external automation tool — so it can run with nobody pressing a button.

**[SHOW: Knowledge app]**

Finally the **Knowledge** app. I've already uploaded a document here. I'll ask a question about its contents.

**[ACTION: ask a question in Knowledge chat]**

And the answer comes back grounded in that document.

**One honest note on what's still rough:** the AI model occasionally returns an 'overloaded' error when the provider is busy. I've added automatic retries to handle most of these, but under heavy load it can still surface. If I were taking this further, the next step would be a friendlier message in the interface and a short queue, so the user never sees a raw error. I'd rather flag that openly than pretend it's perfect."

---

## PART 5 — How my GitHub showcases the work  ⏱ 17:00–20:00

> **[SHOW: GitHub repo]** This part is about hireability.

"Last part — a quick look at the repository itself, because this is what an employer would actually see.

**[SHOW: README]**

This is the **README**, the front page of the project. It tells the whole story: what AI-Doc is, the technologies I used, how to run it locally with a single command, the live link, and a map of how the code is organised. Someone new could clone this and have it running in minutes.

**[SHOW: commit history]**

Here's the **commit history**. You can see steady, real work over time — small, meaningful commits with clear messages, organised by phase and feature branches rather than one giant dump. Every change came in through a reviewed pull request, never straight onto the main branch.

**[SHOW: architecture diagram in README, and docs/adr + phase docs]**

There's an **architecture diagram** showing how the frontend, backend, and database fit together, and a set of **decision records and phase guides** that act as a learning log — they explain not just what I built, but why.

**Why would this make sense to someone considering hiring me?** Because it shows I can do more than make something work. I can structure a real project, document my decisions, test my code, work in clean version-controlled steps, and explain the whole thing simply. That's the package, not just the code.

That is everything I had to show. I am happy to take any questions now."

---

## Quick timing card (keep this visible)

| Part | Topic | Clock |
|------|-------|-------|
| 1 | The task | 0:00 – 3:00 |
| 2 | Planning | 3:00 – 6:00 |
| 3 | Implementation | 6:00 – 12:00 |
| 4 | Live demo | 12:00 – 17:00 |
| 5 | GitHub | 17:00 – 20:00 |

## Delivery reminders

- Do one full practice run out loud, watching the clock.
- Define any technical word in one sentence, then move on.
- Show the project actually working — live, not screenshots.
- Be honest about what was hard and what is still rough; that reads as maturity.
- In Q&A: listen to the whole question, pause if needed, answer in plain language first. If you don't know, say "I'm not sure, but here's how I'd find out." Never guess and present it as fact.
- Close cleanly: "That is everything I had to show. I am happy to take any questions now."

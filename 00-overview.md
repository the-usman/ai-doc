# AI-Doc — Overview and Mindset

Read this document completely before opening any phase file. It is not background reading you can skim and move past — it is the operating system that every phase runs on top of. If a phase instruction makes no sense to you, the answer is almost always in this document.

---

## What AI-Doc is

AI-Doc is a personal developer platform and AI-engineering portfolio that you will build, extend, and deploy across a growing series of phases. It is a real product. You will use it. It grows with you, and there is no fixed end point — each phase you complete adds a permanent layer to the same codebase, and new phases will be added to the programme as you advance.

The name is plain English. A place where raw material is shaped into something useful and durable through disciplined, repeated work. That is exactly what this programme is. The goal is not to complete an assignment — it is to develop an engineer. Each phase is a step in that direction, and the platform you are building is the evidence of the work.

---

## The platform you are building

AI-Doc is not a single-purpose application. It is a platform — a container that holds multiple applications under a single sign-on, each accessible from a shared navigation shell with its own menu and sub-menus.

Think of it the way Google Workspace works. When you log into Google, you are authenticating at the platform level — not at the Gmail level or the Calendar level. Once authenticated, you can switch between Gmail, Calendar, Docs, and Drive — each with its own navigation, its own features, and its own URL namespace — without logging in again. The identity layer is shared. The applications are independent.

AI-Doc works the same way. The outer shell handles authentication, top-level navigation, and application switching. Each application registered inside the platform has its own section in the navigation, its own sub-menus, and its own routes. Phase 1 sets up this shell with the first application (the platform home). Phase 2 adds the LangChain chatbot as a second application. Phase 3 adds the agents panel as a third. Phase 4 adds the knowledge base as a fourth. Phases beyond that will each add further applications — the architecture is designed to accommodate this without ever needing to restructure the shell.

The registration pattern is the architectural key. Adding a new application means adding one entry to a central configuration — a name, an icon, a root path, and a sub-navigation definition. The shell reads that configuration and builds the navigation automatically. Every application you register can have its own collection of sub-pages with their own menus, while the shared login, the shared database, and the shared navigation chrome remain completely untouched. This is what makes a platform different from a collection of separate tools, and understanding it from the inside is one of the most transferable things this programme teaches.

---

## The Software Development Life Cycle

Every feature in AI-Doc follows the SDLC. This is not a formality — it is the discipline that separates an engineer who can work on real teams from one who cannot. The six stages are planning, requirements, design, implementation, testing, and deployment with review. You will practice all six on every non-trivial piece of work in this assignment.

Planning is where you decide what you are actually building before you write code. For each phase task, write two or three sentences in your Architecture Decision Record — your ADR — explaining what you are about to build and why. This takes five minutes and prevents hours of rework.

Requirements is where you define what done looks like. Before starting a feature, list the conditions that must be true for it to be complete. These conditions become your test cases. If you cannot describe what done looks like, you are not ready to start.

Design is where you think through the structure before committing to it. For a database table, this means deciding the columns and relationships before writing SQL. For an API endpoint, this means defining the contract — the URL, the method, the request shape, the response shape — before writing code. Use Claude as a thinking partner during design, but you make the final call and document why.

Implementation is where you write the code. At this stage, the design is already settled. You are executing a plan, not discovering one mid-build.

Testing is non-negotiable. Every function you write has a test. Every endpoint has an integration test. Tests are written before or alongside the code — not after. If you write tests after the code already passes, you are writing tests that confirm what you built rather than verifying what you intended to build. Those are different things.

Deployment and review closes the loop. Every phase ends with a deployment to a live URL and a pull request reviewed before merging. The PR description is part of the deliverable.

---

## AI-Driven Development

You are expected to use AI tools actively throughout this assignment. Claude is the recommended tool. This section explains how to use it in a way that actually makes you a better engineer, rather than a faster copy-paster.

The distinction that matters is this: AI-Assisted Development means using an AI to speed up work you already know how to do. AI-Driven Development means using an AI as a thinking partner at every stage of the SDLC — from requirements through testing — while retaining ownership of every decision and validating every output before it enters the codebase. One of these approaches produces engineers. The other produces engineers who are dependent on the tool and cannot explain what they built.

During planning and requirements, describe to Claude what you are trying to build and ask it to identify edge cases, missing requirements, and alternative approaches you have not considered. Then make your own decision and write it down.

During design, share your proposed structure with Claude and ask whether it will cause problems at scale, what the failure modes are, and whether there is a simpler way to achieve the same result. Then make your own decision and write it down.

During implementation, use Claude to generate scaffolding, explain unfamiliar APIs, and suggest patterns. Do not paste generated code without reading every line. If you cannot explain what a line does, do not merge it until you can.

During testing, ask Claude to help you generate test case scenarios for a function, then add the edge cases it did not think of. This is where AI-Driven Development is most powerful — the combination of AI breadth and your specific knowledge of the system produces a better test suite than either alone.

The validation rule is absolute: every output from an AI tool must be read, run, checked against the requirements, and confirmed passing tests before it enters the codebase. This is not a suggestion. A developer who cannot validate AI output cannot be trusted on a client system.

The documentation rule is equally absolute: every function you write — whether you wrote it from scratch or generated it with AI — must have a docstring or JSDoc comment explaining what it does, what its parameters are, what it returns, and any side effects or error conditions. If you cannot write that comment, you do not understand the function well enough to merge it. Write the comment yourself, never ask Claude to write it for you.

---

## Branch and commit discipline

Create a branch for each phase and for each significant feature within a phase. The naming convention is `phase-N/short-description` for phase work and `feature/short-description` for standalone features within a phase. Examples: `phase-1/auth-setup`, `phase-1/database-schema`, `phase-2/langchain-chat`, `phase-3/langgraph-supervisor`.

Never commit directly to `main`. Every change enters through a pull request. This is not bureaucracy — it is the mechanism that ensures every change is reviewed, the pipeline passes, and there is a written record of why it was made.

Write commit messages in the imperative mood and make them specific. "Add Google OAuth callback route" is a good commit message. "fix stuff" is not. A commit message is a message to your future self and to every engineer who will ever read this history. Make it count.

---

## How phases work

Each phase document walks through the work in order. It tells you what to build, why you are building it, and what to watch out for. It does not write the code for you. The gap between the instruction and the implementation is intentional — that gap is where the learning happens.

Each phase ends with a GitHub Pull Request. The PR cannot be merged until the CI pipeline is green and the PR has been reviewed. Phase 1 and Phase 5 each end with a mandatory live demonstration, as does every phase after Phase 5 that involves a significant new capability.

The current programme has five phases. New phases will be added as you progress. Every new phase extends the same codebase and platform — you will never start from scratch. The work you do in Phase 1 is still running when you are in Phase 8. That continuity is the point.

Read the phase document before starting. Read it again after you finish. The second reading often surfaces things you glossed over on the first pass.

---

## Prerequisites

You should be comfortable with basic SQL before starting — SELECT, INSERT, UPDATE, and CREATE TABLE. You should understand what Docker is and roughly how containers work. You should understand what a REST API is and what an HTTP request looks like. You should know basic Git — clone, commit, push, and pull request. If any of these feel genuinely unfamiliar, spend a day with them before starting Phase 1. Phase 1 assumes they are in place.

Before starting, you must have installed Git, Docker Desktop, and pgAdmin on your local machine. Your Dokploy credentials will be provided by TSS — if you have not received them, ask before you begin. A Claude.ai account is required from Phase 1. n8n is introduced in Phase 3.

---

*Read this document. Then open `docs/setup.md`. Then open `01-phase-1-foundations.md`.*

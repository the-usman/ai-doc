# Phase 1 — Foundations

**Duration:** Weeks 1 and 2
**Branch:** `phase-1/foundations`
**Deliverable:** A deployed, working platform shell with single sign-on, a PostgreSQL database, a passing CI/CD pipeline, documentation living inside the application, and a multi-application navigation structure ready to receive the applications you will build in Phases 2 through 4. Demonstrated live.

---

## What you are building

Phase 1 delivers an application that has no AI features yet — and that is deliberate. By the end of this phase, a user can visit your live URL, sign in with their Google or GitHub account, land on a home dashboard, and navigate between application slots that are waiting to be filled in later phases. The database is running, connected, and migrated correctly. The CI/CD pipeline turns green or red on every push before any code reaches `main`. Docker runs the full stack locally from a single command. The production configuration is deployed on Dokploy.

This feels like infrastructure work, not product work. That is exactly right. Infrastructure is the feature in Phase 1. Every subsequent phase is clean and fast because this phase was done properly. Every subsequent phase is painful and full of hidden breakage when this phase was improvised.

Before writing a line of application code, read `docs/setup.md` completely and apply every practice it describes. This is not optional pre-reading — it is the first task of Phase 1.

---

## The multi-application platform architecture

AI-Doc is a platform, not a single application. The architecture you design in Phase 1 must support that from the start. Retrofitting a platform shell onto a single-application codebase later is expensive and messy — it is far better to design for it on day one when the codebase is small and the cost of changing the structure is low.

The outer shell is responsible for three things: authentication (the user logs in once and is authenticated across all applications), top-level navigation (a persistent navigation element that shows the available applications and allows switching between them), and routing (each application lives under its own URL prefix and manages its own sub-routes).

Each application registered inside the platform is responsible for three things: its own sub-navigation (a sidebar or secondary menu that shows the pages and views within that application), its own routes (all nested under its prefix), and its own page components. Applications share the authentication state and the database, but they are otherwise self-contained.

In Phase 1, register two applications. The first is the platform Home — the landing page after login, which shows the user what applications are available and any platform-level information. The second is the Docs application — the living documentation for the entire platform, described in detail below. Phases 2, 3, and 4 each add one more application.

The top-level navigation should be designed so that adding a new application means adding one entry to a central configuration or registry — not reaching into multiple files. This single-registration-point pattern is the difference between a platform that stays manageable as it grows and one that becomes tangled.

Document this architectural decision in an ADR. The ADR should explain the multi-application structure, why you chose to separate the shell from the applications, and how new applications will be registered.

---

## Step 1 — Repository and project hygiene

Create your fork of the AI-Doc repository and clone it locally. Before adding any code, apply every practice in `docs/setup.md`. This means: creating your `.gitignore` covering secrets, build artefacts, and IDE files; creating your `.env.example` with every required variable; setting up `.editorconfig` for consistent formatting; and writing your first ADR documenting your stack choice.

Your stack choice is a real decision and should be treated as one. The most common combinations are Next.js with no separate backend (self-contained, good for frontend-first developers), React with FastAPI (the recommended split for AI engineering roles — most international AI product teams use this combination), or Vue or Svelte with FastAPI (appropriate only if you have existing strong experience in those frameworks). Whichever you choose, document the reasoning in ADR-001 before you write a single line of application code.

Open your first pull request with just this setup work. The PR description should explain what hygiene practices you applied and why. This establishes the pattern that every PR has a meaningful description.

---

## Step 2 — Docker setup

Install Docker Desktop locally if you have not already. Create the `docker/docker-compose.yml` file for local development and the `docker/docker-compose.prod.yml` file for production. These two files are deliberately different — read `docs/setup.md` for the full explanation of why, and then apply those differences consciously rather than just copying one from the other.

Your local compose file runs: the application container (or containers for a split stack), a PostgreSQL container using the `pgvector/pgvector:pg16` image, and a Redis container. All ports are accessible to localhost. Source code is mounted as a volume for hot-reload. A single `docker compose up` from the project root starts the entire stack.

Your production compose file runs the same services but without exposing database or Redis ports to the internet, without source code volume mounts, and pulling from a built image rather than running in development mode. The differences between these two files represent real security and stability decisions — document them in an ADR.

Add health checks to every service in both compose files. Health checks are how Docker and Dokploy know whether a service is actually ready rather than merely started. A database container that has started but has not yet finished initialising will fail connection attempts from the application — a health check with a `pg_isready` command prevents this by making the application wait until Postgres is genuinely ready.

---

## Step 3 — Database setup and schema

Your PostgreSQL instance runs via Docker. Now connect your application to it and apply the initial schema from `schema/schema.sql`.

The schema is the single source of truth for the database structure. Every table, index, constraint, trigger, and view is defined there. The file is version-controlled alongside the code, which means the database structure and the code that depends on it are always in sync. Never make a manual change to the database without also updating the schema file.

For Phase 1, the schema creates the `users` table with a UUID primary key, an email field, the OAuth provider name, the provider's own ID for the user, a display name, an avatar URL, and timestamps. The unique constraint is on the combination of provider and provider user ID — not on email alone, because the same email address can exist on multiple OAuth providers as genuinely separate identities. The `sessions` table stores active session tokens with a reference to the user and an expiry timestamp. Both tables have the `updated_at` auto-trigger.

Choose your migration strategy before writing any schema and document it in an ADR. The two options are: a single idempotent `schema.sql` file using `CREATE TABLE IF NOT EXISTS` throughout (simpler, appropriate for projects with one developer), or a numbered migrations folder managed by Alembic (Python) or Drizzle (TypeScript). Either is acceptable. What is not acceptable is having no migration strategy at all — that is a project where no one knows what state the database is in.

---

## Step 4 — Single sign-on

Configure one OAuth provider. Google OAuth is recommended as the first choice — it is the most universally recognised in client contexts and demonstrates a clean, professional integration. GitHub OAuth is a close second and slightly simpler to configure.

Understand the OAuth 2.0 authorisation code flow before you implement it. Ask Claude to walk you through it: what the authorisation code is, why it is exchanged server-side rather than client-side, and what the state parameter is for and why omitting it is a security vulnerability. You should be able to explain this flow in plain English by the time you are done implementing it, because clients will ask.

The flow is: user clicks sign in, is redirected to the provider's login page, authenticates, is redirected to your callback URL with a code, your backend exchanges the code for a token, fetches the user profile from the provider, creates or updates the user record in your database, establishes a session, and redirects the user to the platform home. Each step should have a test. The callback route with a valid code must create a user and return a session. A second login from the same provider must update the existing record rather than creating a duplicate. An invalid code must return an appropriate error.

---

## Step 5 — Multi-application platform shell

This step is the architectural centrepiece of Phase 1. Design the shell before building it, and document the design as an ADR.

The shell has three layers. The outermost layer is the authenticated wrapper — any route inside the platform requires an active session, and unauthenticated requests are redirected to the sign-in page. The middle layer is the platform navigation — a persistent top bar or sidebar that shows the registered applications and allows switching between them. The inner layer is the application frame — a container that renders the currently active application, which manages its own sub-navigation and routes.

Each registered application needs: a unique key used in routing and the navigation registry, a display name shown in the platform navigation, an icon or visual identifier for the application switcher, a root path (e.g. `/home`, `/chat`, `/agents`, `/knowledge`), and its own sub-navigation definition (the pages and sections within the application).

The application switcher in the navigation should be visually clear about which application is currently active. Sub-navigation for each application should only be visible when that application is active — not cluttering the interface with all sub-menus simultaneously.

In Phase 1, register two applications in the registry: Home (root `/`, sub-pages: Overview, Settings) and Docs (root `/docs`, sub-pages: Architecture, Decisions, Runbook, API Reference). The routes exist and are navigable. The pages do not need full content yet — placeholders are acceptable, except for the Docs pages described in Step 6.

---

## Step 6 — Documentation inside the application

The Docs application is not a placeholder. It is a first-class part of the platform from Phase 1. Every architectural decision you make, every integration you build, and every operational procedure you establish is documented here, inside the running product.

The Architecture page describes the system structure. It should contain a plain-text or Mermaid diagram of the platform layers and a plain-English explanation of each component. Update it as the platform grows in each subsequent phase.

The Decisions page is the living log of Architecture Decision Records. Every non-trivial decision you made during the build is recorded here in the format defined in `docs/decisions.md`. By the end of Phase 1, there should be at minimum four ADRs: your stack choice, your OAuth provider and flow design, your migration strategy, and your multi-application shell architecture. The ADR count will grow with each phase.

The Runbook page follows the structure in `docs/runbook.md`. It explains how to run the project locally, how to deploy it, and how to troubleshoot the most common problems. Write it for a developer who has never seen the project before. Update it whenever you discover a problem that took more than ten minutes to resolve.

The API Reference page starts as a placeholder in Phase 1. You will populate it in Phase 2 when the first real API routes are added.

---

## Step 7 — Test-driven development in practice

Before writing any application logic, write a failing test for it. Phase 1's minimum test suite covers: the health check endpoint returns HTTP 200 with a JSON body, the OAuth callback with a valid code creates a user record and returns a session, the OAuth callback with an invalid code returns HTTP 400, the users table enforces the unique constraint on provider plus provider user ID, and the platform navigation renders the correct number of registered applications.

Set up your test runner before writing these tests — pytest for Python, Vitest or Jest for TypeScript. Configure it to run inside the Docker environment using the CI database connection. Tests that pass on your laptop but fail in CI because of environment differences are tests that give false confidence.

Every function in the codebase at the end of Phase 1 must have a docstring or JSDoc comment. The comment explains what the function does, what its inputs are, what it returns, and any side effects. This is not optional and will be checked in the PR review.

---

## Step 8 — CI/CD pipeline

Create `.github/workflows/ci.yml`. This pipeline runs on every push to any branch and on every pull request targeting `main`. It must run in sequence: lint, test, build, and schema validation. If any step fails, the pipeline fails. No PR is merged with a failing pipeline.

Enable branch protection on `main` in your GitHub settings. Required status checks: the CI pipeline must pass. Required reviews: one approval. These two rules mean that nothing reaches `main` without passing the full pipeline and being seen by a reviewer.

The schema validation step uses sqlfluff to lint `schema/schema.sql` against the postgres dialect. This catches SQL syntax errors and style inconsistencies before they reach the database.

---

## Step 9 — Dokploy deployment

Your Dokploy credentials are provided by TSS. Log in to your panel, create a new application pointing at `docker/docker-compose.prod.yml`, connect the GitHub repository, and configure all environment variables in the Dokploy secrets panel. Never put real values in files that are committed to the repository — always use the secrets panel for production credentials.

Trigger a deployment. Watch the logs. When the deployment succeeds, visit the live URL, sign in, and confirm the platform shell renders correctly and authentication works end-to-end. Share the live URL with TSS.

If the deployment fails, read the logs, understand what failed, and fix it. Production debugging is a skill. Practice it here where the cost of failure is low.

---

## Phase 1 checklist

- [ ] ADR-001 written: stack choice with reasoning
- [ ] ADR-002 written: OAuth provider and flow design
- [ ] ADR-003 written: migration strategy
- [ ] ADR-004 written: multi-application shell architecture and application registration pattern
- [ ] `.gitignore` covers secrets, build artefacts, and IDE files
- [ ] `.env.example` lists every required variable with placeholder values
- [ ] `.editorconfig` configured and applied
- [ ] `docker-compose.yml` runs the full local stack with `docker compose up`
- [ ] `docker-compose.prod.yml` is production-safe (no exposed DB/Redis ports, no source mounts)
- [ ] Health checks on all services in both compose files
- [ ] `schema/schema.sql` applied: users table with UUID PK, sessions table, updated_at trigger
- [ ] Migration strategy chosen, documented in ADR-003, and applied
- [ ] Google or GitHub OAuth working end-to-end (login, user record creation, session)
- [ ] Second login from same provider updates record rather than duplicating it
- [ ] Multi-application shell with application switcher in place
- [ ] Two applications registered: Home and Docs
- [ ] Each application has its own sub-navigation structure
- [ ] Application switching is visually clear about the active application
- [ ] Docs application populated: Architecture, Decisions, Runbook pages written
- [ ] Every function in the codebase has a docstring or JSDoc comment
- [ ] Minimum five tests written and passing
- [ ] CI pipeline passes: lint, test, build, schema validation
- [ ] Branch protection on `main` configured
- [ ] Application deployed to live URL via Dokploy
- [ ] Live URL shared with TSS

---

## Live demonstration

Phase 1 ends with a mandatory live screen-share session. You will: navigate to your live URL and demonstrate the sign-in flow; sign in and reach the platform home; switch between the Home and Docs applications and demonstrate the sub-navigation; open a terminal and run `docker compose up` from scratch so the reviewer sees the stack start cleanly; open GitHub and walk through the CI pipeline on a recent commit; read aloud one ADR you wrote and explain the decision it documents; answer questions.

Questions will be asked about things you have not prepared specific answers for. The best preparation is to understand what you built and why, which means reading your own ADRs before the session and being able to defend each choice.

Phase 2 does not begin until the Phase 1 live demonstration is complete.

---

*Phase 1 complete → PR opened and merged → live demo delivered → open `02-phase-2-langchain.md`.*

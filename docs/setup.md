# Setup and Senior Developer Practices

This document covers the practices that experienced engineers apply before writing a single line of application code. These are not preferences — they are habits that compound over time. A project set up correctly from the start is a project that stays maintainable for years. A project that skips these steps accumulates invisible debt that eventually makes every change painful.

Read this document before starting Phase 1. Apply every practice it describes before opening your first phase file.

---

## Git hygiene

Git is not a backup tool. It is a communication channel — every commit is a message to your future self and to every engineer who will ever work on this codebase. Treat it like one.

**Commit messages** should be written in the imperative mood — "Add OAuth callback route" not "Added OAuth callback route" and not "oauth stuff". The subject line should complete the sentence "If applied, this commit will...". Keep subject lines under 72 characters. If the commit needs more explanation, add a body after a blank line. A good commit message makes code review faster, makes git blame useful, and makes debugging a regression by reading history actually possible.

**Branch naming** should communicate intent. Use a prefix that describes what kind of work it is, followed by a short description using hyphens. Phase work follows the convention `phase-N/short-description`. Feature work uses `feature/short-description`. Bug fixes use `fix/short-description`. Examples: `phase-1/auth-setup`, `feature/document-upload`, `fix/embedding-dimension-mismatch`. Avoid names like `test`, `dev`, `temp`, or your own name. Branch names are visible to everyone who clones the repository.

**Never commit directly to `main`.** Every change to `main` enters through a pull request. This is not bureaucracy — it is the mechanism that ensures every change is reviewed, the pipeline passes, and there is a written record of why the change was made. A `main` branch with a clean PR history is a branch you can audit, revert, and reason about. A `main` branch with direct commits is a branch you have to read the code to understand.

**Commit atomically.** One commit, one logical change. A commit that adds a feature, fixes a bug, updates the README, and reformats two unrelated files is a commit that is impossible to review meaningfully and impossible to revert safely. If you find yourself writing "and" in a commit message subject line, consider whether it should be two commits.

---

## Environment variable discipline

Environment variables are how a codebase knows things that differ between environments — database passwords, API keys, feature flags, URLs. Getting this wrong is one of the most common and most damaging mistakes in software engineering. A secret committed to a public repository is compromised from the moment it is committed, even if deleted in the next commit. Git remembers everything.

The rule is simple: the `.env` file is never committed. It lives in `.gitignore` from the very first commit. The file that is committed is `.env.example` — an identical structure with every variable present, but all values replaced with descriptive placeholders. This file tells anyone who clones the repository exactly what they need to configure to run the project.

When you add a new environment variable to your application, add it to `.env.example` at the same time, in the same commit. An `.env.example` that is out of sync with the actual requirements is worse than no `.env.example`, because it gives the false impression of documentation.

The naming convention for environment variables is uppercase with underscores. Group related variables with a prefix: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_PASSWORD`. `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`. This makes the purpose of each variable clear without reading the code that uses it.

---

## Editor configuration

`.editorconfig` is a file that tells editors how to format files consistently — indentation style (tabs or spaces), indentation size, end-of-line character, and whether to trim trailing whitespace. Without it, two developers with different editor settings will produce constant formatting noise in diffs — every line they touch will show formatting changes alongside the actual logic changes, making code review harder.

Create a `.editorconfig` file at the project root and apply it from the first commit. The specific settings matter less than consistency. Choose a standard for your stack — two-space indentation for JavaScript and TypeScript, four-space for Python is common — and commit to it. If you are using a linter (ESLint, Prettier, flake8, ruff), the `.editorconfig` settings should agree with the linter settings. Conflicts between the two produce an environment that constantly fights itself.

---

## README as contract

The README is the first thing anyone reads when they open a repository. It is the contract between you and every developer who will ever clone, fork, or review the project. A good README answers four questions: what does this project do, how do I run it locally, how do I deploy it, and how do I contribute to it.

The discipline is to write the README before you build, not after. This forces you to think about the interface of the project — what someone needs to know to run it — before you are too deep in the implementation to see it clearly. Then update it as you build. A README that describes what the project will do is a planning document. A README that describes what the project currently does is documentation. Keep it current.

---

## Architecture Decision Records

An Architecture Decision Record — ADR — is a short document that captures an important technical decision: the context, the options considered, the decision made, and the reasoning. The format is deliberately lightweight so that writing one takes minutes, not hours.

ADRs matter because decisions that seem obvious in the moment become mysterious six months later. Why is the database PostgreSQL and not SQLite? Why is authentication handled by the backend and not the frontend? Why is Redis used for session storage and not the database? Without ADRs, the only way to find out is to ask the original developer — who may be unavailable — or to infer it from the code, which may not make the tradeoffs visible.

The template for an ADR in DevAI-Doc is simple. Status (Proposed, Accepted, or Superseded). Context (one paragraph explaining the problem being solved and the constraints). Options considered (a brief description of two or more approaches). Decision (what was chosen). Consequences (what becomes easier, what becomes harder, what the known risks are).

You will write at minimum one ADR per phase. By Phase 5, you will have a meaningful record of how the system was built and why, which becomes the backbone of your case study.

---

## Docker discipline

Docker is the mechanism that ensures the application runs the same way on every machine — your laptop, your colleague's laptop, and the production server. It removes the class of problems where code works locally and fails in deployment because of a missing dependency, a different version of a runtime, or a different operating system behaviour.

The key discipline in Docker for this project is the separation between `docker-compose.yml` (local development) and `docker-compose.prod.yml` (production). These files serve different masters and should look different.

The local compose file should: expose database and service ports to your localhost so you can connect pgAdmin and debug directly, mount your source code as a volume so that changes are reflected immediately without rebuilding the image, set environment variables that enable debug logging and hot reload, and use lightweight base images that start quickly.

The production compose file must: not expose database ports to the internet (a database port exposed to the internet is an attack surface), pull from a built and versioned image rather than mounting source code, set only the environment variables needed for production (no debug flags), and include health checks that allow Dokploy to know whether the service is running correctly.

A production compose file that looks identical to the local compose file is a production compose file that has never been reviewed with security in mind. Always review both files side by side and ask yourself: if someone hostile could reach the production server, what could they do?

---

## Testing philosophy

Testing is often taught as a phase that happens after the code is written. This is backwards, and the consequences of getting it backwards are: you write tests that confirm what you built rather than verifying what you intended, you discover bugs late when they are expensive to fix, and you build a habit of skipping tests under deadline pressure because they feel optional.

Test-Driven Development means writing a test that describes the intended behaviour before writing the code that implements it. The test fails first — because the implementation does not exist yet — and then you write the minimum code needed to make it pass. This sequence matters because it ensures that the test was actually testing something. A test that you write after the code already passes is a test you have never seen fail, which means you do not know if it would catch a regression.

The minimum testing bar for this project is one test per function for core logic, integration tests for every API endpoint, and at least one test that verifies each database constraint. Coverage metrics are a lagging indicator — a high coverage percentage with weak assertions is less valuable than targeted tests for the most important paths.

Every test should be readable without explaining it. A test is documentation of intent. `test_oauth_callback_creates_user` tells you exactly what should happen. `test_3` does not.

---

## Documenting functions

Every function you write, whether you wrote it from scratch or generated it with AI assistance, must have a docstring (Python) or JSDoc comment (TypeScript/JavaScript) before the PR is opened. The comment must answer four questions: what does this function do, what are the parameters and their types, what does it return, and what can go wrong or what side effects does it have.

This is not about generating documentation pages — it is about the habit of thinking clearly about the interface of every piece of logic you write. A function whose purpose you cannot describe in two sentences is a function you do not understand well enough to maintain.

When you use Claude to generate a function, the first thing you do after reading and validating the code is to write the docstring yourself. Not ask Claude to write it — write it yourself. If you cannot write the docstring, you do not understand the function well enough to merge it.

---

## Keeping secrets out of logs

One specific practice worth calling out separately: never log secrets, tokens, passwords, or personally identifiable information. Log statements are the most common place that sensitive data accidentally ends up in production logs, which are stored, shipped to logging services, and visible to multiple people.

The rule is to log identifiers and statuses, not values. Log `user_id` not `email`. Log `oauth_token received` not the token itself. If you are ever uncertain whether something is safe to log, ask yourself: if this log line appeared in a breach report, would it cause harm? If yes, do not log it.

---

*Apply every practice in this document before opening Phase 1. These habits are the foundation everything else builds on.*

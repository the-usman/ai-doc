# Architecture Decision Records

This file is the living log of every significant architectural decision made during the development of AI-Doc. A decision belongs here if it involved a genuine choice between alternatives, if the reasoning is not visible from the code alone, or if someone reading the codebase six months from now would reasonably wonder why a particular approach was taken.

The goal is not to document every line of code. It is to capture the context and reasoning behind choices that are difficult to reverse or that carry meaningful tradeoffs — so that future contributors, including yourself, can understand and build on the decisions rather than inadvertently undoing them.

---

## Template

Copy this template for each new ADR. Number them sequentially.

```
## ADR-XXX — [Short descriptive title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Superseded by ADR-XXX

### Context
One paragraph. What problem were you solving? What constraints were in play?
What made this a non-trivial decision rather than an obvious one?

### Options considered
A brief description of two or more approaches you evaluated.

### Decision
What did you choose and why? Reference the options above by name.

### Consequences
What becomes easier as a result of this decision?
What becomes harder or more constrained?
What are the known risks or tradeoffs you are accepting?
```

---

## ADR-001 — Stack choice

**Date:** [Fill in when written]
**Status:** Accepted

### Context
[Describe what you evaluated: Next.js alone, React plus FastAPI, Vue plus FastAPI, or another combination. Describe the constraints — your existing experience, the role you are targeting, the complexity tradeoffs between a monolith and a split stack. This is your first ADR and it sets the standard for the ones that follow.]

### Options considered
[Fill in the options you genuinely evaluated.]

### Decision
[Fill in what you chose and why.]

### Consequences
[Fill in what becomes easier, what becomes harder, and what risks you are accepting.]

---

## ADR-002 — OAuth provider and flow design

**Date:** [Fill in]
**Status:** Accepted

### Context
[Describe why you chose Google or GitHub OAuth rather than username-password authentication. Describe what the authorisation code grant type is and why the code exchange happens server-side. Describe what the state parameter does and why omitting it is a vulnerability.]

### Options considered
[Fill in]

### Decision
[Fill in]

### Consequences
[Fill in]

---

## ADR-003 — Database migration strategy

**Date:** [Fill in]
**Status:** Accepted

### Context
[Describe the two primary options: a single idempotent schema.sql file using CREATE TABLE IF NOT EXISTS throughout, versus a numbered migrations folder managed by Alembic (Python) or Drizzle (TypeScript). Describe the operational difference: the idempotent file is simple and safe but loses the history of incremental changes; numbered migrations preserve history but require a migration runner and more discipline to maintain.]

### Options considered
[Fill in]

### Decision
[Fill in]

### Consequences
[Fill in]

---

## ADR-004 — Multi-application shell architecture

**Date:** [Fill in]
**Status:** Accepted

### Context
[Describe the platform architecture you designed in Phase 1: the outer shell handling authentication and top-level navigation, each application owning its own sub-navigation and routes, and the single-registration-point pattern for adding new applications. Explain why this structure was chosen over a simpler single-page application or a separate deployment per tool.]

### Options considered
[Fill in]

### Decision
[Fill in]

### Consequences
[Fill in]

---

*Add new ADRs below this line as the project progresses. Each phase requires at least one new ADR. By Phase 5, the ADR log should contain a minimum of ten records covering all major decisions across the system.*

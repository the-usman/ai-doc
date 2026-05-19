# Pull Request

## Phase / Feature
<!-- Which phase or feature does this PR complete? e.g. Phase 1 — Foundations -->

## What this PR does
<!-- Two to four sentences. What did you build or change, and why? -->

## How to test it
<!-- Steps a reviewer can follow to verify the work is correct. -->
<!-- Be specific — "run the tests" is not enough. What should they see? -->

1. 
2. 
3. 

## Checklist
<!-- Tick every box before requesting review. A PR with unticked boxes will not be merged. -->

- [ ] All phase checklist items in the phase document are complete
- [ ] Every new function has a docstring or JSDoc comment
- [ ] Every new function has at least one test
- [ ] Tests pass locally (`docker compose run --rm app pytest` or equivalent)
- [ ] CI pipeline is green on this branch
- [ ] I have done an AI-Driven Development validation review (asked Claude to identify missing error handling, undocumented functions, and missing tests)
- [ ] `.env.example` is up to date with any new environment variables
- [ ] The relevant ADR(s) have been written in `docs/decisions.md`
- [ ] The `/docs` route in the application is updated if the architecture changed

## ADRs written in this PR
<!-- List the ADR numbers and titles you wrote for this PR. At least one per phase. -->

## What I would do differently
<!-- Honest reflection. What did you learn? What would you change if you started this again? -->
<!-- This is not graded. It is the most useful part of the PR. -->

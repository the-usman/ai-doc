# Phase 5 — Production

**Duration:** Weeks 9 to 10
**Branch:** `phase-5/production`
**Deliverable:** LangSmith observability integrated across all agent traces, OWASP LLM Top 10 reviewed and applied, an eval harness using LLM-as-judge producing a measurable score, the CI/CD pipeline at its final state, a written case study, a recorded demo, and a live presentation delivered.

---

## What you are building

Phase 5 does not add new features. It does something harder: it proves that what you already built is trustworthy, observable, secure, and maintainable by someone who was not part of building it.

This is the phase that most junior developers skip in their personal projects, and it is precisely why most junior developer projects do not get taken seriously by clients. A prototype that works when you are present to run it is a demo. A system that passes an observability review, a security checklist, and an evaluation harness is evidence that you know how to build software that can be operated by others. That distinction is what Phase 5 is about.

The live presentation at the end of this phase is the gate that closes Phase 5 of the AI-Doc programme. You will present a production-grade, deployed system, explain its architecture and the decisions behind it, walk through real observability data, present quantified evaluation results, and answer questions you have not prepared for. This is the format of a real technical client engagement. Doing it here, with TSS, is the practice run.

---

## Step 1 — LangSmith integration

LangSmith is the observability and evaluation platform for LangChain applications. Every LLM call, every chain step, every tool invocation, and every LangGraph node transition generates a trace in LangSmith when the integration is active. These traces are the production visibility layer — when something goes wrong in a deployed system, LangSmith is where you go to understand what the system actually did, in what order, at what latency, with what inputs and outputs.

Create a LangSmith project named `ai-doc` and configure the API key in your environment variables and the Dokploy secrets panel. Enable tracing by setting the `LANGCHAIN_TRACING_V2=true` environment variable. This single variable is enough to activate tracing for all LangChain operations — no code changes are required.

Once tracing is active, use the system normally: send a chat message, trigger an agent pipeline, upload a document and ask a question about it. Then open LangSmith and examine the traces. You will see the full execution tree for each operation — the supervisor decision, the worker invocations, the tool calls, the retrieved chunks, the LLM inputs and outputs at each step, and the latency for each node. This is the visibility that makes production systems maintainable.

Write a reflection in your case study about what you found when you first examined your traces. Were there any unexpected paths? Did the supervisor route to the wrong worker for any input? Were there tool calls that succeeded but returned empty results? Were there any calls with latency that surprised you? Honest reflection on real observations is worth more in a case study than polished generalisations.

---

## Step 2 — LangSmith as evaluation platform

LangSmith is not only for tracing. It includes a dataset and evaluation framework that you will use in Step 3. Before building the eval harness, create a LangSmith dataset named `ai-doc-eval` and populate it with your evaluation examples. A LangSmith dataset is a collection of input-output pairs — inputs are the questions you will ask, outputs are the reference answers you expect. The dataset lives in LangSmith and can be used to run evaluations against any version of the system.

---

## Step 3 — Evaluation harness

An eval harness is an automated system for measuring the quality of your agent's responses. Without an eval harness, you have no quantitative way to know whether a change to the system improved things or made them worse. This matters enormously in AI systems, where changes to a prompt, a chunk size, a retrieval parameter, or a model version can have non-obvious effects on output quality.

Create an `evals/` folder in the repository. Inside it, create `eval_set.json` with at minimum twelve evaluation examples spread across three categories. Four examples should test the LangChain chatbot from Phase 2 — questions about platform data that require tool use to answer correctly. Four should test the LangGraph agent pipeline from Phase 3 — tasks that require routing to a specific worker and producing a structured output. Four should test the RAG pipeline from Phase 4 — questions about documents where the answer is present in the uploaded content and the LLM must cite the correct chunk.

Write an evaluation script in `evals/run_evals.py` (or the TypeScript equivalent) that loops through the eval set, sends each question through the appropriate interface, and then makes a second LLM call — the judge call — that scores the response on three dimensions: accuracy (is the answer factually correct given the context), completeness (does the answer address all parts of the question), and groundedness (does the answer rely on the provided data or retrieved chunks rather than the model's training knowledge). Each dimension is scored one to three. The overall score for an example is the sum, giving a maximum of nine per example and a maximum of 108 for the full set of twelve.

Run the eval harness twice: once before applying any improvements, and once after addressing any weaknesses the traces revealed in Step 1. Document both scores and the changes you made between runs in your case study. The before-and-after comparison is the evidence that your eval harness is doing what it is supposed to do.

Add the eval harness to the CI/CD pipeline as a separate on-demand job using `workflow_dispatch`. It should not run on every push — each run makes real LLM calls with real cost and latency. The on-demand trigger means you run it deliberately, not automatically.

---

## Step 4 — OWASP LLM security review

The OWASP Top 10 for LLM Applications is the industry-standard reference for AI system security. Go through each of the ten risks and assess whether and how it applies to AI-Doc. For three of the risks — prompt injection, insecure output handling, and excessive agency — write a detailed assessment that includes a concrete attack scenario relevant to your specific system, the mitigation you have implemented, and the residual risk that remains.

Prompt injection is the risk that a malicious input causes the LLM to behave in ways the application did not intend — for example, a user who uploads a document containing hidden instructions that override the system prompt when the document is retrieved and injected into the context. This is directly relevant to your Phase 4 RAG system. Insecure output handling is the risk that structured output or tool call results from the LLM are used without validation, allowing malformed data to reach the database or the frontend. Excessive agency is the risk that the agent is given more tool access or autonomy than necessary, so that a misbehaving agent can cause disproportionate damage.

Add the OWASP assessment to the Security page of the Docs application. Any client doing a technical review of the system will look for evidence that you have thought about security systematically — this page is that evidence.

---

## Step 5 — CI/CD final state

Review the CI/CD pipeline and bring it to its final form. The pipeline should run lint, tests, build, and schema validation on every push and PR. The eval harness job should be configured as a separate on-demand workflow. Branch protection on `main` should require the CI pipeline to pass and require one reviewer approval.

Add a CI status badge to the `README.md`. The badge shows the current state of the pipeline on the main branch — green if passing, red if failing. This is a small thing, but it is the first thing a client or employer sees when they visit the repository. A green badge communicates that the project is maintained.

---

## Step 6 — Case study

Write a case study for AI-Doc. It is a professional document, four to six pages, written for a technically literate audience that has not seen the code. Its purpose is to communicate what you built, why you made the key decisions you made, what you learned from building it, and what you would do differently.

Structure the case study as follows. Open with one paragraph that explains what AI-Doc is and what it demonstrates, without jargon. Follow with a system architecture section that includes a diagram of the platform layers and a plain-English description of how they interact. Then write a section covering four or five key engineering decisions — for each one, state the problem you were solving, the alternatives you considered, what you chose, and why. Follow this with an honest reflection on what you learned — not what went well, but what changed in how you think about building software. Close with a brief note on what you would add or improve with more time.

The case study is not a summary of the phase documents. It is a synthesis of your experience written from the perspective of someone who has now built the whole system and can see it clearly. Use Claude to help you with a first draft, then rewrite it substantially in your own voice. Ask Claude to identify where the draft is vague, where it is jargon-heavy without explanation, and where the reasoning is not visible. Fix those spots yourself. The case study should sound like you.

Commit the case study to `docs/case-study.md` so it is part of the repository and rendered in the Docs application under a new Case Study page.

---

## Step 7 — Recorded demo

Record a video walkthrough of the platform, no more than twelve minutes. The video must show: the live platform at the deployed URL, the sign-in flow, navigation between all four applications using the platform switcher, a live conversation in the Chat application that triggers at least one tool call, a live agent pipeline run in the Agents application with intermediate steps visible, a document upload and a retrieval-augmented question in the Knowledge application, a brief walkthrough of one interesting section of code with an explanation of why it is designed the way it is, and one LangSmith trace that corresponds to something you just demonstrated.

Practice the walkthrough at least twice before recording. The video should be confident and clear, not scripted — you should be narrating what you are doing and why, not reading from notes. A developer who can walk through their own system conversationally and explain what it is doing is a developer a client can trust in a meeting.

Upload the video to Loom or a similar platform and add the link to the README and to the Docs application home page.

---

## Live presentation

Phase 5 ends with the final live presentation — forty-five to sixty minutes with TSS.

You will open the live platform at its deployed URL and walk through all four applications. You will explain the platform shell architecture and how it handles authentication and routing across applications. You will walk through the LangChain chain design from Phase 2 and explain what LCEL is and why you used it. You will explain the LangGraph supervisor-and-worker pattern and describe a specific routing decision the supervisor makes. You will explain the RAG pipeline and what happens to a document from the moment it is uploaded to the moment a retrieved chunk appears in the LLM's context. You will open LangSmith and walk through a real trace. You will present your eval harness results before and after. You will walk through the OWASP assessment for one risk. You will answer questions.

The questions will not all be ones you have prepared for. That is deliberate. The live presentation is not a performance — it is a check that you genuinely understand what you built, not just that you can walk through it. The best preparation is to re-read your ADRs, re-read your case study, and be honest with yourself about which parts of the system you understand least well — then spend time on those before the session.

---

## Phase 5 checklist

- [ ] LangSmith project created and API key configured in environment variables and Dokploy
- [ ] `LANGCHAIN_TRACING_V2=true` set in production
- [ ] Traces verified in LangSmith for chat, agent pipeline, and RAG query
- [ ] LangSmith observations documented in case study
- [ ] LangSmith `ai-doc-eval` dataset created with evaluation examples
- [ ] `evals/eval_set.json` with twelve examples across three categories
- [ ] `evals/run_evals.py` (or equivalent) implemented and running
- [ ] Eval run completed before any improvements: score recorded
- [ ] Improvements applied based on trace observations
- [ ] Eval run completed after improvements: score recorded
- [ ] Before-and-after scores documented in case study
- [ ] OWASP Top 10 reviewed
- [ ] Prompt injection, insecure output handling, and excessive agency fully assessed with attack scenarios and mitigations
- [ ] OWASP assessment in the Docs application Security page
- [ ] CI pipeline at final state: lint, test, build, schema validation on every push
- [ ] Eval harness configured as on-demand `workflow_dispatch` job
- [ ] CI status badge in README
- [ ] Case study written and committed to `docs/case-study.md`
- [ ] Case Study page added to Docs application
- [ ] Recorded demo uploaded and linked in README and Docs application
- [ ] All functions in the codebase documented with docstring or JSDoc
- [ ] Deployed to Dokploy live URL — final state
- [ ] Live presentation delivered

---

## Phase 5 is a milestone, not an ending

When the live presentation is done, Phase 5 is complete. The first chapter of the AI-Doc programme is behind you.

What you have at this point is not a tutorial output. It is a deployed, production-grade, four-application platform with authentication, a relational database, a LangChain chatbot with tool use and structured output, a LangGraph multi-agent orchestration system, a RAG pipeline backed by pgvector, Redis-backed persistent memory, LangSmith observability, a quantified evaluation harness, an OWASP security review, a full CI/CD pipeline, a written case study, and a live presentation you delivered under questioning.

That is a serious foundation. The phases that follow will build on every part of it — deeper LangChain patterns, more sophisticated agent architectures, evaluation at scale, deployment hardening, and integrations with real external systems. None of that work starts from scratch. It starts from here.

When TSS opens the next phase, you will pick up in the same codebase, the same repository, and the same platform you have been building since Phase 1.

---

*Phase 5 complete → live presentation delivered → wait for Phase 6.*

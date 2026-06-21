# Automations

Exported n8n workflows that drive AI-Doc autonomously. Any developer can import a
file here into their own n8n instance and have the automation running in minutes.

## `pipeline_trigger.json` — daily agent pipeline (Phase 3)

Fires once a day at 07:00 and starts a LangGraph agent pipeline run without a
human pressing a button. The result appears on the Agents → Run History page the
next time someone opens the platform.

### What it does

1. **Every day at 07:00** — a Schedule Trigger node.
2. **Build task** — sets the task description sent to the pipeline.
3. **Start pipeline run** — `POST {AI_DOC_API_URL}/api/agents/trigger` with the
   task in the JSON body and the shared secret in the `X-Trigger-Token` header.
   The endpoint starts the pipeline, persists the run, and returns a `run_id` and
   `status`.
4. **Log response** — records the returned `run_id` and `status` so the execution
   log shows what was triggered.

### Import and configure

1. In n8n, open **Workflows → Import from File** and select
   `automations/pipeline_trigger.json`.
2. Set two environment variables on your n8n instance (Settings → Variables, or
   the host environment):
   - `AI_DOC_API_URL` — base URL of the AI-Doc API, e.g.
     `https://your-name.tss-domain.com` (no trailing slash).
   - `AGENTS_TRIGGER_TOKEN` — must match `AGENTS_TRIGGER_TOKEN` in the API's
     environment. The trigger endpoint returns **503** when the API has no token
     configured and **401** when the header does not match.
3. Adjust the schedule or the task text in **Build task** to taste.
4. **Activate** the workflow.

### Test it manually

```bash
curl -X POST "$AI_DOC_API_URL/api/agents/trigger" \
  -H "Content-Type: application/json" \
  -H "X-Trigger-Token: $AGENTS_TRIGGER_TOKEN" \
  -d '{"task": "Summarise the platform user count and recent sign-ins."}'
```

A `200` response with `{"run_id": "...", "status": "completed"}` confirms the
endpoint and token are wired correctly.

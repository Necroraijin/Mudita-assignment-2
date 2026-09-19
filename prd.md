Assignment 2 — Three Connected Mini-Agents
Goals & Scope
Goal: turn a fictional meeting transcript plus company rules into a reviewed, corrected action plan via three genuinely separate LLM agents (Intake → Planning → Review) handing off structured data — not one prompt wearing three hats.
In scope:
• Intake Agent: extract decisions/requirements/constraints with source references, flag gaps/conflicts, never invent owners or deadlines
• Planning Agent: tasks/owners/deadlines/dependencies from Intake's output plus rules, with facts vs. recommendations vs. open questions clearly separated
• Review Agent: checks the plan against transcript and rules, sends specific corrections to Planning, rechecks, stops after a bounded number of attempts and surfaces unresolved issues
• Persistent run state: run ID, source facts, context versions, agent outputs, handoff messages; resumable without duplicating completed work
• Demo cases: one full run, a rule violation sent back for correction, a changed source fact propagating through the plan, recovery after a simulated model failure, two isolated sessions
Out of scope:
• Real transcript ingestion from an actual meeting tool (a pasted/uploaded fictional transcript is enough)
• More than one company-rules document/policy set at a time
• A general-purpose agent framework beyond what these three roles need
Architecture & Data Model
Frontend: Next.js on Vercel — New Run, Run Detail, Run List pages, polling or SSE for live per-agent status.
Backend: FastAPI + LangGraph on GCP Cloud Run. LangGraph models the Intake→Planning→Review handoff as a graph, gives each agent its own node with a defined input/output schema, and its checkpointing covers "resume without duplicating completed work" largely for free.
LLM: Claude (Anthropic API), one call per agent per step; each agent sees only its own declared inputs — no shared mutable scratchpad between agents.
Datastore: Cloud SQL (Postgres) for run state — the safer default given the uniqueness and versioning needs below (Firestore would also work if you prefer nested documents for handoff messages).
Key entities:
• Run(id, transcript, rules, status, created_at)
• ContextVersion(id, run_id, fact_key, value, version, superseded_by)
• AgentOutput(id, run_id, agent, version, schema_version, payload_json, created_at)
• HandoffMessage(id, run_id, from_agent, to_agent, content, created_at)
• ReviewCycle(id, run_id, attempt_number, corrections, resolved boolean)
• ActionLog(id, run_id, actor, action, detail, created_at)
API & Agent Orchestration Contract
Internal API:
• POST /runs — start a run from a transcript + rules (or the built-in sample input)
• GET /runs — list runs by ID, for the isolation demo
• GET /runs/{id} — full run detail: each agent's status, inputs/outputs, handoff messages, final plan
• POST /runs/{id}/facts/{fact_id} — correct a source fact; bumps its version and recomputes only the downstream steps that depended on it
• POST /runs/{id}/reset — clear a run back to its starting state
• POST /runs/{id}/simulate-failure — inject a labeled fault at a chosen step, for the recovery demo
Agent handoff contract:
• Each agent node has an explicit schema (Pydantic) for its input and output; a downstream agent never receives a malformed or unvalidated payload from an upstream one — a failed validation is a visible error state, not a silent pass-through.
• Review's output to Planning is a structured list of {issue, evidence, required_change} objects, not free text, so Planning can act on it deterministically.
• Review is capped at N attempts (config value); on cap-out, the run surfaces "unresolved: <list>" instead of looping forever or silently accepting the plan.
Security & Reliability
Security:
• Same secret-management baseline as Assignment 1: all keys in GCP Secret Manager, least-privilege service account.
• Every AgentOutput and HandoffMessage is schema-validated before it's persisted or passed downstream — this is the main injection/hallucination defense here, since a transcript could contain adversarial text (e.g. "ignore prior rules"); validation means a bad instruction embedded in the transcript can influence content but can't skip the schema or the bounded-retry structure.
• Per-run scoping: every query is filtered by run_id, and the dashboard requires the same internal-user auth as Assignment 1 — this is what makes "two sessions don't share private context" true by construction rather than something proven after the fact.
• Full input/output of every agent call is logged for audit, with API keys and any secrets stripped before the log line is written.
Reliability & idempotency:
• Explicit per-agent status machine: pending → running → succeeded / failed / needs_review. A retried step resumes from the last successful checkpoint (LangGraph's checkpointing, keyed by run_id + step) instead of redoing completed work.
• Simulated model failures are injected through POST /runs/{id}/simulate-failure, not by actually breaking the LLM call path, and are always labeled [simulated fault] in the UI and action log — never indistinguishable from a real failure.
• Changed-fact propagation: editing a fact bumps its ContextVersion; only the agent steps that read that fact are recomputed, everything else is served from cache — this is what makes the "changed fact propagates through the plan" demo show real dependency tracking rather than a full rerun.
Pages / UI
1. New Run — paste/upload transcript + rules, a "load sample input" button, submit to start.
2. Run Detail — the three agents shown in sequence: Intake's extracted items with source refs and flagged gaps; Planning's tasks/owners/deadlines with facts vs. recommendations vs. open questions visually separated; Review's feedback-and-recheck cycle through to the final plan. Inline fact correction shows a visible "recomputing affected steps" state.
3. Run List — past runs by ID; opening two side by side is how you demonstrate session isolation live.
Deployment, Testing & Observability
• Frontend: Vercel project; env var for the backend base URL only.
• Backend: Dockerized FastAPI on GCP Cloud Run, separate GCP project/service from Assignment 1; Secret Manager for the Anthropic key and DB credentials.
• Logging: structured logs per agent call (agent, run_id, step, tokens in/out, latency) — this is what feeds the "approximate cost per run" figure the brief asks for.
• Tests: schema-validation unit tests per agent's output; a test for the bounded-retry cap (Review never loops past N attempts); a test for fact-version propagation (edit a fact, assert only downstream steps recompute).
• Repo docs: setup steps, env var names, an architecture diagram of the LangGraph graph, known limitations, approximate cost per run.
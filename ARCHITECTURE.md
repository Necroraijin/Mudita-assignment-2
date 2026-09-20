# MA2 — Multi-Agent Action Planner

## What the App Does

MA2 takes a meeting transcript and a set of company rules as input, then runs them through three separate AI agents in sequence to produce a reviewed, corrected action plan.

The pipeline works like this:

1. A user pastes a meeting transcript and company rules into the web UI
2. The **Intake Agent** reads the transcript and extracts structured facts — decisions, requirements, and constraints — with source references back to the original text
3. The **Planning Agent** takes those facts plus the company rules and builds a task-based action plan with owners, deadlines, dependencies, and clear labeling of what is fact vs. recommendation vs. open question
4. The **Review Agent** checks the plan against the original transcript and rules, and either approves it or sends structured corrections back to the Planning Agent
5. If corrections are needed, Planning revises and Review checks again — up to a configurable maximum (default: 3 cycles)
6. The final output is a reviewed action plan with full traceability back to the source transcript

Users can also:
- Edit individual facts and watch only the affected downstream steps recompute
- Inject simulated failures to test recovery behavior
- Reset runs and re-execute them
- View two runs side by side to verify session isolation

---

## Folder Structure

```
MA2/
|
|-- backend/                    Python FastAPI + LangGraph backend
|   |-- app/
|   |   |-- agents/             AI agent logic and LangGraph orchestration
|   |   |   |-- graph.py        StateGraph definition: nodes, edges, conditional routing
|   |   |   |-- state.py        TypedDict defining the shared graph state
|   |   |   |-- intake_agent.py Intake node: extracts facts from transcript
|   |   |   |-- planning_agent.py Planning node: builds action plan from facts
|   |   |   |-- review_agent.py Review node: validates plan, sends corrections
|   |   |   |-- prompts.py      System and user prompt templates for each agent
|   |   |   |-- llm.py          Vertex AI (Gemini) client wrapper with logging and secret stripping
|   |   |
|   |   |-- models/             SQLAlchemy ORM models (database tables)
|   |   |   |-- run.py          Run — the top-level entity for each pipeline execution
|   |   |   |-- context_version.py ContextVersion — versioned facts with superseded_by tracking
|   |   |   |-- agent_output.py AgentOutput — stored output of each agent call (JSON + metadata)
|   |   |   |-- handoff_message.py HandoffMessage — data passed between agents
|   |   |   |-- review_cycle.py ReviewCycle — one review attempt with corrections and resolution status
|   |   |   |-- action_log.py   ActionLog — audit trail of every action taken in a run
|   |   |
|   |   |-- schemas/            Pydantic models for validation and serialization
|   |   |   |-- common.py       Shared enums: AgentName, RunStatus, AgentStatus
|   |   |   |-- intake.py       IntakeInput, IntakeOutput, SourceFact, Gap
|   |   |   |-- planning.py     PlanningInput, PlanningOutput, TaskItem
|   |   |   |-- review.py       ReviewInput, ReviewOutput, ReviewCorrection
|   |   |   |-- run.py          API request/response schemas: RunCreate, RunDetailResponse, etc.
|   |   |
|   |   |-- services/           Business logic layer
|   |   |   |-- run_service.py  Create, list, get, execute, and reset runs
|   |   |   |-- fact_service.py Fact versioning and selective downstream recomputation
|   |   |   |-- failure_service.py Simulated failure injection
|   |   |   |-- audit_service.py Action logging with secret stripping
|   |   |
|   |   |-- routers/
|   |   |   |-- runs.py         All 6 API endpoints (POST/GET /runs, facts, reset, simulate-failure)
|   |   |
|   |   |-- middleware/
|   |   |   |-- rate_limit.py   SlowAPI rate limiter
|   |   |   |-- logging_middleware.py Request/response structured logging
|   |   |
|   |   |-- db/
|   |   |   |-- base.py         SQLAlchemy DeclarativeBase
|   |   |   |-- session.py      Async engine, session factory, get_db dependency
|   |   |
|   |   |-- config.py           Pydantic Settings: reads all config from environment variables
|   |   |-- main.py             FastAPI app factory: CORS, middleware, router registration
|   |
|   |-- alembic/                Database migration scripts
|   |   |-- versions/
|   |       |-- 001_initial_schema.py  Creates all 6 tables with indexes
|   |
|   |-- tests/                  Pytest test suite
|   |   |-- test_schemas.py     Validates that each agent schema rejects bad data
|   |   |-- test_bounded_retry.py Proves review never loops past MAX_REVIEW_CYCLES
|   |   |-- test_api.py         API endpoint validation and health check
|   |   |-- test_session_isolation.py Verifies runs don't share state
|   |
|   |-- Dockerfile              Multi-stage production build (non-root user)
|   |-- requirements.txt        Python dependencies
|   |-- .env.example            Required environment variables
|
|-- frontend/                   Next.js 14 TypeScript + Tailwind CSS frontend
|   |-- src/
|   |   |-- app/                Next.js App Router pages
|   |   |   |-- page.tsx        Root redirect to /runs
|   |   |   |-- layout.tsx      Nav bar, global styles
|   |   |   |-- runs/
|   |   |       |-- page.tsx    Run List — table of all runs with status badges
|   |   |       |-- new/
|   |   |       |   |-- page.tsx New Run — transcript + rules form with "Load Sample"
|   |   |       |-- [id]/
|   |   |           |-- page.tsx Run Detail — full agent pipeline view
|   |   |
|   |   |-- components/         React components
|   |   |   |-- RunForm.tsx     Transcript/rules input with sample data loader
|   |   |   |-- RunList.tsx     Table of runs with real-time status polling
|   |   |   |-- RunDetail.tsx   Main detail view: agent panels, fact editor, timeline, audit log
|   |   |   |-- AgentPanel.tsx  Collapsible panel showing one agent's status and output
|   |   |   |-- IntakeView.tsx  Renders extracted facts, gaps, and conflicts
|   |   |   |-- PlanningView.tsx Renders task table with owners, deadlines, priorities
|   |   |   |-- ReviewView.tsx  Renders review verdict, correction cycles, unresolved issues
|   |   |   |-- FactEditor.tsx  Inline fact editing with "Save & Recompute" button
|   |   |   |-- HandoffTimeline.tsx Visual timeline of data passed between agents
|   |   |   |-- StatusBadge.tsx Color-coded status indicator with spinner for "running"
|   |   |   |-- ui/            Shared primitives: Button, Card, Badge, Spinner
|   |   |
|   |   |-- hooks/              React hooks
|   |   |   |-- usePolling.ts   Generic polling hook with configurable interval
|   |   |   |-- useRun.ts       Polls GET /runs/{id} every 2s while status is running
|   |   |   |-- useRuns.ts      Polls GET /runs every 5s for the list view
|   |   |
|   |   |-- lib/                Shared utilities
|   |       |-- api.ts          Typed fetch wrapper for all backend endpoints
|   |       |-- types.ts        TypeScript interfaces mirroring backend Pydantic schemas
|   |       |-- constants.ts    API base URL, polling interval
|   |       |-- sample-data.ts  Sample meeting transcript and company rules
|   |
|   |-- Dockerfile              Multi-stage production build (non-root user)
|   |-- .env.example            NEXT_PUBLIC_API_URL only
|
|-- docker-compose.yml          Local dev: Postgres + backend + frontend
|-- prd.md                      Product requirements document
```

---

## How It Works End-to-End

### 1. User Creates a Run

The user fills in the New Run form (or clicks "Load Sample Input") and submits. The frontend calls `POST /api/runs` with the transcript and rules text.

### 2. Backend Creates a Run Record

The API creates a `Run` row in PostgreSQL with status `pending` and all three agent statuses set to `pending`. It returns the run ID immediately.

### 3. Pipeline Executes in Background

The API kicks off the LangGraph pipeline as a background task. The graph has this topology:

```
START --> intake_node --> planning_node --> review_node --> review_router
                              ^                               |
                              |         (corrections)         |
                              +-------------------------------+
                                                              |
                                                    (approved OR cap hit)
                                                              v
                                                             END
```

Each node runs one Gemini API call (via Vertex AI), parses the JSON response, validates it against the Pydantic schema, and returns the validated data.

### 4. Frontend Polls for Updates

The Run Detail page polls `GET /api/runs/{id}` every 2 seconds. Each poll returns:
- Per-agent status (pending / running / succeeded / failed / needs_review)
- All agent outputs, handoff messages, review cycles, facts, and audit logs

The UI updates each agent panel independently — so you see Intake complete, then Planning start, etc.

### 5. Review Feedback Loop

After Planning produces a plan, Review checks it. If Review finds issues:
- It returns `approved: false` with a list of `ReviewCorrection` objects
- Each correction has: `issue`, `evidence` (quote from transcript/rules), `required_change`, and `related_task_ids`
- The graph routes back to Planning with these corrections
- Planning addresses each correction and produces a revised plan
- Review checks again

This loops until either:
- Review approves the plan (`approved: true`)
- The maximum number of review cycles is reached (default: 3)

If the cap is reached, the run completes with status `completed_with_issues` and the unresolved corrections are surfaced in the UI.

### 6. Fact Correction and Selective Recomputation

Users can edit any extracted fact in the Run Detail page. When they do:
1. The old `ContextVersion` row gets `superseded_by` set to the new version's ID
2. A new `ContextVersion` row is created with `version + 1`
3. Only Planning and Review re-execute (Intake's work is already done)
4. The new plan is based on the corrected fact set

This demonstrates real dependency tracking — not a full re-run.

### 7. Simulated Failure and Recovery

Users can inject a simulated failure at any agent step. When triggered:
- The targeted agent node checks `state["simulated_failure_at"]` before calling Gemini
- If it matches, the node sets `error = "[simulated fault] ..."` and the run fails
- The failure is always tagged `[simulated fault]` in the UI (orange warning banner) and audit log
- The user can then reset the run and re-execute it to demonstrate recovery

---

## The Three AI Agents

All three agents use Gemini (Google Vertex AI) with structured JSON output. Each agent:
- Receives only its declared inputs (no shared mutable scratchpad)
- Produces Pydantic-validated output
- Has its output stored as an `AgentOutput` row with token counts and latency
- Has its handoff data stored as a `HandoffMessage` row

### Agent 1: Intake Agent

**Purpose:** Extract structured information from the raw meeting transcript.

**Input:**
- Meeting transcript (raw text)
- Company rules (raw text)

**Output (IntakeOutput):**
```
facts: [
  {
    fact_id: "fact_001"           -- unique identifier
    fact_key: "deadline_q4"       -- short descriptive key
    value: "December 15th"        -- the extracted value
    source_reference: "Rachel said: 'ship by December 15th'"
    category: "decision" | "requirement" | "constraint"
  }
]
gaps: [
  {
    description: "No rollback plan discussed for data migration"
    severity: "blocking" | "warning" | "info"
  }
]
conflicts: ["Budget constraint conflicts with contractor needs"]
```

**Key rules for this agent:**
- NEVER invents owners or deadlines not in the transcript
- Every fact must have an exact source reference (quote)
- Gaps are flagged by severity so Planning can prioritize
- Uses fact_id format: fact_001, fact_002, etc.

**Prompt configuration:** See `backend/app/agents/prompts.py` — `INTAKE_SYSTEM_PROMPT` and `INTAKE_USER_PROMPT`

---

### Agent 2: Planning Agent

**Purpose:** Build an action plan from the extracted facts and company rules.

**Input:**
- Facts from Intake (list of SourceFact objects)
- Gaps from Intake
- Conflicts from Intake
- Company rules
- Corrections from Review (empty on first pass, populated on subsequent passes)

**Output (PlanningOutput):**
```
tasks: [
  {
    task_id: "task_001"
    description: "Complete dashboard redesign with accessibility compliance"
    owner: "Alex" | null           -- only if explicitly in transcript
    deadline: "December 15th" | null
    dependencies: ["task_002"]     -- task IDs that must complete first
    source_fact_ids: ["fact_001"]   -- traceability to source facts
    item_type: "fact" | "recommendation" | "open_question"
    priority: "high" | "medium" | "low"
  }
]
assumptions: ["Team has capacity for parallel workstreams"]
open_questions: ["Who will handle the data migration rollback plan?"]
```

**Key rules for this agent:**
- Only assigns owners/deadlines that are EXPLICITLY in the transcript
- Unassigned items get `null` (not invented names)
- Each task must reference its source_fact_ids for traceability
- Must clearly separate facts (from transcript) vs. recommendations (agent suggestions) vs. open questions (need stakeholder input)
- When receiving corrections from Review, must address each one specifically
- Tasks must comply with all company rules

**Prompt configuration:** `PLANNING_SYSTEM_PROMPT`, `PLANNING_USER_PROMPT`, `PLANNING_CORRECTIONS_SECTION`

---

### Agent 3: Review Agent

**Purpose:** Validate the action plan against the original transcript and company rules.

**Input:**
- Original meeting transcript
- Company rules
- Extracted facts from Intake
- Action plan from Planning
- Current attempt number

**Output (ReviewOutput):**
```
approved: true | false
corrections: [
  {
    issue: "Missing security review task before deployment"
    evidence: "Rule 1: 'All deployments require security review sign-off'"
    required_change: "Add a security review task as a dependency of the deployment task"
    related_task_ids: ["task_005"]
  }
]
unresolved_issues: []              -- populated only on final attempt if cap is hit
summary: "Plan covers main deliverables but misses required security step"
```

**Key rules for this agent:**
- Checks that every task is grounded in the transcript or clearly marked as a recommendation
- Verifies compliance with ALL company rules
- Confirms no owners or deadlines were invented
- Checks for missing tasks (decisions in transcript not covered by the plan)
- Verifies task dependencies are logical
- Corrections must be structured (not free text) — each has issue, evidence, and required_change
- Evidence must be a direct quote from transcript or rules

**Prompt configuration:** `REVIEW_SYSTEM_PROMPT`, `REVIEW_USER_PROMPT`

---

## Agent Configuration

All agent configuration is managed through environment variables loaded by `backend/app/config.py`:

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | (required) | Google Generative AI API key |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Which Gemini model to use for all agents |
| `MAX_REVIEW_CYCLES` | `3` | Maximum review-planning loop iterations before stopping |
| `MAX_TRANSCRIPT_LENGTH` | `50000` | Maximum characters allowed in transcript input |
| `MAX_RULES_LENGTH` | `10000` | Maximum characters allowed in rules input |
| `DEBUG` | `false` | Enables /docs and /redoc endpoints when true |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |

---

## Security Measures

| Concern | How It Is Handled |
|---|---|
| **Secrets** | DB credentials in environment variables / Secret Manager. Vertex AI uses IAM-based auth (no API key). |
| **SQL Injection** | SQLAlchemy ORM exclusively. No raw SQL. All queries parameterized. |
| **Schema Validation** | Every agent output validated through Pydantic before storage or handoff. Invalid output = visible error, not silent pass-through. |
| **XSS** | React's default JSX escaping. No dangerouslySetInnerHTML. Transcript rendered as plain text. |
| **CORS** | Explicit allow_origins whitelist. Only GET and POST methods allowed. |
| **Rate Limiting** | SlowAPI middleware on all endpoints. |
| **Per-Run Scoping** | Every DB query filtered by run_id. No endpoint returns cross-run data. |
| **Audit Logging** | Every action logged with API keys and secrets stripped via regex before writing. |
| **Input Validation** | Transcript and rules have maximum length limits. Empty inputs rejected. |
| **Container Security** | Docker images run as non-root user. Multi-stage builds minimize attack surface. |

---

## Database Schema

Six tables, all scoped by `run_id`:

- **runs** — Top-level: transcript, rules, overall status, per-agent status, review attempt count
- **context_versions** — Versioned facts with `superseded_by` for edit tracking
- **agent_outputs** — JSON payload of each agent call with version, token counts, latency
- **handoff_messages** — Data passed between agents (intake->planning, planning->review, review->planning)
- **review_cycles** — One row per review attempt: corrections list and resolved boolean
- **action_logs** — Audit trail: who did what when (system, intake, planning, review, user)

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/runs` | Create a new run from transcript + rules. Returns run ID immediately, executes pipeline in background. |
| `GET` | `/api/runs` | List all runs with their statuses. |
| `GET` | `/api/runs/{id}` | Full run detail: all agent outputs, handoffs, review cycles, facts, audit log. |
| `POST` | `/api/runs/{id}/facts/{fact_id}` | Correct a source fact. Triggers selective recomputation of Planning and Review. |
| `POST` | `/api/runs/{id}/reset` | Reset a run to its initial state (clears all outputs, resets statuses). |
| `POST` | `/api/runs/{id}/simulate-failure` | Inject a simulated failure at a specific agent step (intake, planning, or review). |

---

## Deployment Architecture

```
                    Internet
                       |
          +------------+------------+
          |                         |
    [Vercel CDN]              [Cloud Run]
    Next.js Frontend          FastAPI Backend
    (Static + SSR)            (2 workers, autoscale 0-5)
          |                         |
          |    /api/* rewrites      |
          +------------------------>|
                                    |
                              [Cloud SQL]
                              PostgreSQL 16
                              (Private IP)
                                    |
                              [Secret Manager]
                              CLOUD_SQL_PASSWORD
```

### Frontend — Vercel

The Next.js app deploys to Vercel automatically on git push.

**How it connects to the backend:**
- In **production**, `BACKEND_URL` is set as a server-side env var on Vercel (not exposed to the browser). Next.js rewrites proxy all `/api/*` requests to the Cloud Run backend URL. The browser only talks to the Vercel domain — no CORS needed.
- In **local dev**, `NEXT_PUBLIC_API_URL=http://localhost:8000/api` is set, and the frontend calls the backend directly (CORS is configured for localhost:3000).

**Vercel environment variables to set:**
| Variable | Value | Visibility |
|---|---|---|
| `BACKEND_URL` | `https://ma2-backend-xxxxx-uc.a.run.app` | Server-side only |

Do NOT set `NEXT_PUBLIC_API_URL` on Vercel — it would expose the Cloud Run URL to the browser and bypass the rewrite proxy.

**Security headers** (configured in `next.config.ts`):
- `X-Frame-Options: DENY` — prevents clickjacking
- `X-Content-Type-Options: nosniff` — prevents MIME sniffing
- `Content-Security-Policy` — restricts script/style/connect sources
- `Permissions-Policy` — disables camera, microphone, geolocation

### Backend — GCP Cloud Run

The FastAPI backend runs as a Docker container on Cloud Run.

**Key Cloud Run settings** (configured in `cloudbuild.yaml`):
- 1 GiB memory, 2 vCPUs
- 300s request timeout (agents need time for Gemini API calls)
- Autoscale 0-5 instances (scales to zero when idle)
- Non-root container user
- Cloud SQL instance attached via `--add-cloudsql-instances`

**How secrets are managed:**
- `CLOUD_SQL_PASSWORD` — stored in GCP Secret Manager, injected at deploy time via `--set-secrets`
- Vertex AI uses IAM-based authentication — the Cloud Run service account has `aiplatform.user` role, so no API key is needed
- The Cloud Run service account has only the minimum required roles

**How the database connects:**
- In production, `USE_CLOUD_SQL_CONNECTOR=true` activates the Google Cloud SQL Python Connector
- The connector uses IAM-authenticated Unix socket connections — no public IP needed
- Connection pooling: 5 connections, max 10 overflow, 30-minute recycle

**Auto-migration:**
- On startup in production/staging, the app runs `alembic upgrade head` automatically
- This is idempotent — if migrations are already applied, it's a no-op

### Database — Cloud SQL (PostgreSQL 16)

**Instance configuration** (set by `gcp-setup.sh`):
- `db-f1-micro` tier (scale up as needed)
- Automated daily backups at 03:00 UTC
- SSL required for all connections
- Storage auto-increase enabled

**Service account permissions** (least privilege):
| Role | Purpose |
|---|---|
| `cloudsql.client` | Connect to Cloud SQL |
| `secretmanager.secretAccessor` | Read DB password from Secret Manager |
| `aiplatform.user` | Call Vertex AI (Gemini) models |
| `logging.logWriter` | Write structured logs |
| `monitoring.metricWriter` | Write Cloud Monitoring metrics |

---

## Setup & Deployment Guide

### Local Development

```bash
# 1. Start Postgres
docker-compose up db -d

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # edit with your GCP_PROJECT_ID
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Or with Docker Compose (authenticate with GCP first):
```bash
# Authenticate for Vertex AI (local dev)
gcloud auth application-default login
export GCP_PROJECT_ID=your-project-id
docker-compose up
```

### Production Deployment

**One-time GCP setup:**
```bash
cd backend
chmod +x gcp-setup.sh
./gcp-setup.sh <PROJECT_ID> <REGION>
```

This creates: Cloud SQL instance, database, service account (with Vertex AI access), and stores DB credentials in Secret Manager.

**Deploy backend to Cloud Run:**
```bash
cd backend
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_REGION=us-central1,_SERVICE_NAME=ma2-backend,_CLOUD_SQL_INSTANCE=<connection-name>,_SERVICE_ACCOUNT=<sa-email>
```

**Deploy frontend to Vercel:**
1. Connect the `frontend/` directory to a Vercel project
2. Set `BACKEND_URL` to the Cloud Run URL in Vercel project settings (server-side only)
3. Push to main branch — Vercel deploys automatically

**Update CORS after getting Vercel domain:**
```bash
gcloud run services update ma2-backend \
  --region=us-central1 \
  --update-env-vars='CORS_ORIGINS=["https://your-app.vercel.app"]'
```

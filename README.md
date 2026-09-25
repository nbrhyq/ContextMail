# ContextMail

ContextMail is an intent-aware communication agent. It converts a natural-language goal and supporting materials into an evidence-grounded email, independently reviews it, and stops at an explicit human approval boundary before a mocked email action.

## MVP flow

```text
User goal
  → Planner
  → dynamic Context / Research selection
  → shared evidence
  → Writer
  → Reviewer
  → Planner re-planning when required
  → editable preview
  → Approve / Reject
  → mock email action
```

Supported intents: `JOB_APPLICATION`, `PHD_OUTREACH`, `SCHOOL_AFFAIRS`, `OTHER`, and `UNCERTAIN`. Ambiguous requests remain uncertain and stop to request input.

## What is implemented

- FastAPI backend with typed Pydantic state and API contracts
- LangGraph orchestration with adaptive routing and bounded re-planning
- Context, Research, Writer, and Reviewer agents
- real local PDF, DOCX, and TXT extraction
- structured, traceable evidence objects
- SQLite run persistence
- upload, run, draft edit, approve, reject, and run status APIs
- strict approval guard around a mock email tool
- structured execution trace without chain-of-thought exposure
- provider-neutral LLM and external-tool interfaces
- evaluation schemas and aggregation for baseline comparisons
- responsive Next.js/TypeScript frontend

The default LLM is the locally installed Ollama `qwen3:latest` model (Qwen3 8B). Planner, Writer, and Reviewer request schema-constrained structured output from Ollama. If Ollama is unavailable or produces invalid output, each component falls back to its deterministic implementation. Web research remains mocked and never invents external findings.

## Run locally

### Backend

Requires Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,workflow,documents]'
uvicorn app.main:app --app-dir backend --reload
```

API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Ollama must be running locally:

```bash
ollama serve
ollama list  # should include qwen3:latest
```

### Frontend

Requires Node.js 18+ and pnpm/npm.

```bash
cd frontend
pnpm install
cp .env.local.example .env.local
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

### Tests and production build

```bash
.venv/bin/python -m pytest
cd frontend && pnpm build
```

## Key modules

- `backend/app/graph/workflow.py` — LangGraph topology and routing
- `backend/app/graph/state.py` — shared typed state
- `backend/app/agents/` — planner and specialist agents
- `backend/app/tools/` — deterministic tool interfaces and implementations
- `backend/app/services/run_store.py` — SQLite persistence
- `backend/app/evaluation/` — baseline and metric contracts
- `frontend/app/page.tsx` — complete MVP workspace

## Safety and current boundaries

- Email sending is always mocked and rejects unapproved calls.
- Uploaded files are limited to PDF, DOCX, and TXT and 10 MB each.
- Qwen3 runs locally through Ollama; no cloud LLM API key is required.
- Real web search is deliberately not enabled by default.
- Secrets belong in environment variables; `.env` files are ignored by Git.

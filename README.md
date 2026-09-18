# ActionProof

**Every high-impact AI-agent action should carry its proof.**

ActionProof is a runtime safety layer between an AI agent and a protected tool. Before a high-impact action executes, it retrieves the evidence required for that action, validates freshness and authority, applies deterministic policy, and produces one of three outcomes:

- **ALLOW**
- **CONFIRM**
- **BLOCK**

Allowed actions execute through a protected runtime and are checked again after execution.

Built for **YC Fall 2026 × Moss — The Zero Latency Builder Sprint**.

**Live demo:** https://actionproof.onrender.com  
**Architecture:** [docs/architecture.md](docs/architecture.md)  
**Product requirements:** [docs/prd.md](docs/prd.md)

## Why it exists

An agent can have valid credentials and still make the wrong operational move because its context is stale, incomplete, or missing.

A restart is a simple example. If a service disconnects while external state is still unreconciled, restarting immediately can be the wrong next step. ActionProof makes current context part of authorization rather than treating retrieval as an explanation step after the fact.

## Hero scenario

1. A service loses connectivity.
2. Reconciliation is incomplete.
3. The agent proposes a restart.
4. ActionProof retrieves restart policy, live state, and the recovery runbook with Moss.
5. The restart is **BLOCKED**.
6. Reconciliation runs through the protected runtime.
7. Postflight verification confirms the new state.
8. The restart is evaluated again and becomes **ALLOW**.

The Proof Inspector shows the evidence, freshness, matched rule, decision code, trace, and measured preflight latency used for each decision.

## Architecture

```text
Agent action
    |
    v
ActionProof
    |
    +--> Moss context retrieval
    +--> authority / freshness validation
    +--> deterministic policy
    |
    v
ALLOW / CONFIRM / BLOCK
    |
    v
Protected tool
    |
    v
Postflight verification
    |
    v
Updated live state
```

The LLM may propose an action or explain a result. It is not the final safety authority.

ActionProof defaults to Moss **SessionIndex** for the protected hot path. Policy, runbook, and live operational state are retrieved through real Moss sessions in-process. Cloud-backed Moss mode remains available with `MOSS_RUNTIME_MODE=cloud`.

See [Architecture](docs/architecture.md), [Product Requirements](docs/prd.md), and [Local Moss Runtime](docs/local-moss-runtime.md).

## Product surfaces

- **Mission Control** — current state, decision, safe next action, Moss evidence, proof, and runtime timeline
- **Scenario Lab** — deterministic ALLOW / CONFIRM / BLOCK cases against the same live control path
- **Latency Lab** — repeatable p50 / p95 / p99 / max measurement from the real preflight engine
- **Proof Inspector** — evidence and latency detail for the exact decision shown on screen

## Run locally

Create `.env` from `.env.example` and add your Moss project credentials. Do not commit the file.

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --port 5173
```

Open `http://localhost:5173`.

The Vite development server proxies `/api` to the backend, so the browser uses the same API path in development and deployment.

## Docker

From the repository root:

```bash
docker compose up --build
```

Open `http://localhost:5173`.

The production frontend proxies `/api` and the runtime event stream to the backend. The backend image includes the canonical policy, runbook, and scenario datasets required to seed local Moss sessions.

## Hosted deployment

ActionProof can be deployed as a small backend web service plus a static frontend.

Backend requirements:

- build from `backend/Dockerfile` with the repository root as Docker context
- set `MOSS_PROJECT_ID` and `MOSS_PROJECT_KEY`
- keep `MOSS_RUNTIME_MODE=local` for the in-process Moss SessionIndex path
- set `ACTIONPROOF_ALLOWED_ORIGINS` to the public frontend origin

Frontend requirements:

- build from `frontend`
- run `npm install && npm run build`
- publish `frontend/dist`
- set `VITE_API_URL` to the public backend URL

The backend honors the platform-provided `PORT` environment variable.

## Verification

```bash
python scripts/seed_moss.py
python scripts/verify_moss.py
python scripts/verify_runtime.py

cd backend
pytest -q -m moss_live
pytest -q

cd ../frontend
npm run build
```

The final submission only reports measurements produced by the real ActionProof runtime. No sponsor benchmark number is presented as an ActionProof result.

## Repository layout

```text
backend/      FastAPI control and runtime service
frontend/     React + TypeScript product interface
data/         Canonical policy, runbook, and scenario evidence
docs/         PRD, architecture, retrieval, runtime, and benchmark notes
benchmarks/   Benchmark methodology and local result output
scripts/      Seeding, verification, profiling, and demo utilities
```

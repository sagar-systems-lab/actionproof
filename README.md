# ActionProof

ActionProof is a runtime safety layer for AI agents that can call high-impact tools.

Before an action reaches a protected tool, ActionProof gathers the current operational context, checks whether that context is usable, applies deterministic policy, and returns one of three outcomes:

- **ALLOW**
- **CONFIRM**
- **BLOCK**

If an action is allowed and executed, the resulting state is checked again so the next decision is based on what actually happened.

Built for **YC Fall 2026 × Moss — The Zero Latency Builder Sprint**.

## The problem

An agent can have valid credentials and still make the wrong operational move because its context is stale, incomplete, or missing.

A restart is a good example. If a service disconnects while external state is still unreconciled, "restart the service" sounds reasonable but may be the wrong next step.

ActionProof treats context retrieval as part of authorization, not as an optional explanation layer.

## Demo scenario

The first scenario is intentionally simple:

1. A service loses connectivity.
2. Reconciliation is incomplete.
3. The agent proposes `restart_service`.
4. ActionProof checks policy, current state, and the recovery runbook.
5. The restart is blocked.
6. Reconciliation runs and is verified.
7. The state changes.
8. The restart is proposed again and can now be allowed.

## Architecture

```text
Agent action
    |
    v
ActionProof
    |
    +--> context lookup (Moss)
    +--> freshness / authority checks
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
```

The LLM can propose an action or explain a result. It does not make the final safety decision.

## Project structure

```text
backend/      FastAPI service
frontend/     React + TypeScript interface
data/         Local scenario fixtures used during development
docs/         Product requirements and architecture notes
benchmarks/   Retrieval / preflight benchmark work
scripts/      Development and demo utilities
```

## Run locally

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Health endpoint: `http://localhost:8000/api/health`.

## Current state

The interface and API skeleton are in place. The decision engine, Moss integration, protected tool path, postflight verification, and benchmarks are being wired in incrementally.

No benchmark numbers are published until the real retrieval path is running.

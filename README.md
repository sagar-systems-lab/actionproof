# ActionProof

> **Every high-impact AI-agent action should carry its proof.**

ActionProof is a real-time context-proof and safety gate for AI agents. Before a high-impact tool call reaches a protected system, ActionProof retrieves the current operational context, validates the evidence, applies deterministic policy, and returns **ALLOW**, **CONFIRM**, or **BLOCK**. Allowed actions are verified postflight so the next decision is based on updated state.

**Hackathon:** YC Fall 2026 × Moss — The Zero Latency Builder Sprint  
**Theme:** Agent Reliability, Security & Evaluation  
**Current status:** Phase 1 — Product Foundation + Judge Contract

## 30-second workflow

```text
Agent proposes action
        ↓
ActionProof preflight
        ↓
Moss retrieves policy + live state + runbook   [Phase 3]
        ↓
Evidence freshness + authority validation
        ↓
Deterministic policy decision
        ↓
ALLOW / CONFIRM / BLOCK
        ↓
Protected tool execution
        ↓
Postflight verification → updated state
```

## Why this exists

AI agents can have valid credentials and still make the wrong operational move because the context they are acting on is missing, stale, or incomplete. ActionProof turns context retrieval into a runtime authorization primitive rather than an optional explanation step.

The hero scenario is intentionally understandable without trading knowledge:

1. A production-like execution service loses connectivity.
2. Reconciliation is incomplete, so outstanding external state is unknown.
3. The agent proposes a restart.
4. ActionProof retrieves relevant context and blocks the unsafe restart.
5. Reconciliation is executed and verified.
6. State is updated.
7. The same restart is retried and can now be allowed.

## Judge score alignment

| Dimension | Weight | ActionProof response |
|---|---:|---|
| Product & UX | 35% | Decision, reason, evidence, next action and latency are visually obvious. |
| Technical Execution | 30% | Deterministic control plane, retrieval validation, protected tool boundary, postflight verification. |
| Speed & Latency | 20% | Moss sits in the critical path; real p50/p95/p99/max are measured. |
| Demo & Presentation | 15% | One closed-loop incident tells the complete story. |

## Product surfaces

- **Mission Control** — state, proposed action, decision, proof, latency, incident timeline.
- **Proof Inspector** — exact evidence and rule behind the decision.
- **Scenario Lab** — five deterministic stories.
- **Latency Lab** — honest measured retrieval/preflight distributions after the real path exists.

## Repository map

```text
docs/        Frozen contracts, PRD, scorecard, demo story
backend/     FastAPI skeleton; deterministic control starts in Phase 2
frontend/    React + TypeScript judge-facing product shell
data/        Canonical fixtures
benchmarks/  Real benchmarks after Moss integration
scripts/     Reset, seed and verification utilities in later phases
```

## Run Phase 1 locally

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Backend skeleton

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Health endpoint: `http://localhost:8000/api/health`.

### Verification

```bash
make verify-phase1
```

Phase 1 fixture data is intentionally limited to the visual shell. The final submission will not mock Moss or the decision-critical runtime.

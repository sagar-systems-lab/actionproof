# ActionProof — Architecture Blueprint V1

**Status:** Frozen foundation  
**Competition:** YC Fall 2026 × Moss — The Zero Latency Builder Sprint  
**Theme:** Agent Reliability, Security & Evaluation  
**Tagline:** Every high-impact agent action should carry its proof.

## Judge-driven architecture

| Judge dimension | Weight | Architectural response |
|---|---:|---|
| Product & UX | 35% | Decision, reason, evidence, next action, and latency are visible without a terminal. |
| Technical Execution | 30% | Real control boundary, deterministic policy, failure handling, postflight verification. |
| Speed & Latency | 20% | Moss lives in the action-critical retrieval path and is measured directly. |
| Demo & Presentation | 15% | One before → incident → decision → recovery → verified outcome story. |

## Product thesis

Valid tool permission does not prove that an AI-agent action is safe *right now*. Missing, stale, or incomplete operational context can make an otherwise plausible action wrong. ActionProof is the runtime preflight layer between an agent and a protected tool.

## Core product

```text
Agent intent
   ↓
ActionProof Gate
   ├─ Intent validation
   ├─ Context requirement resolver
   ├─ Moss retrieval
   ├─ Freshness / authority validation
   ├─ Deterministic policy
   └─ Action Proof Packet
          ↓
   ALLOW / CONFIRM / BLOCK
          ↓
Protected tool executor
          ↓
Postflight verification
          ↓
Updated retrievable state
```

## Retrieval domains

Moss is a first-class dependency, not a decorative API call:

1. Policy index — trusted, versioned rules.
2. Runbook/history index — recovery procedures and prior operational context.
3. Live-state index — dynamic, freshness-sensitive incident state.

Retrieval is semantic + structured + freshness-aware. Similarity alone is never treated as authority.

## Critical decision

The LLM may propose an action or explain a result, but it does **not** own the safety decision.

```text
trusted retrieved context
+ current structured state
+ deterministic policy
= ALLOW / CONFIRM / BLOCK
```

## Hero incident

```text
HEALTHY
  ↓ connection loss
DISCONNECTED + RECONCILIATION INCOMPLETE
  ↓ agent proposes restart
MOSS CONTEXT + POLICY + STATE
  ↓
BLOCK
  ↓
RECONCILE
  ↓ postflight
VERIFIED
  ↓ state update
RETRY RESTART
  ↓
ALLOW
```

## V1 invariants

- High-impact actions fail closed when required context cannot be verified.
- Stale required context cannot silently authorize an action.
- Protected tools have no direct bypass path.
- Displayed evidence is the evidence actually used.
- Displayed performance is measured; no sponsor marketing number is copied as our benchmark.
- No TREX code, credentials, proprietary architecture, or real-money trading is used.

## Frozen stack

React + TypeScript frontend; Python + FastAPI backend; Moss retrieval; deterministic policy; WebSocket/SSE realtime UX; Action Proof Packet as core artifact.

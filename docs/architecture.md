# Architecture

ActionProof sits between an AI agent and a protected tool.

```text
Agent
  |
  v
ActionProof
  |
  +-- determine required evidence
  +-- retrieve evidence with Moss
  +-- validate freshness / authority
  +-- apply deterministic policy
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

## Decision authority

The agent can propose an action, but the final authorization result is produced from structured state, trusted policy, and retrieved evidence.

An LLM is not the final authority over a high-impact tool call.

## Moss retrieval

The protected path uses three evidence domains:

- policy
- runbook / operational knowledge
- current live state

ActionProof defaults to Moss **SessionIndex** mode for the runtime hot path. Canonical policy and runbook documents are seeded into local Moss sessions at process startup, live state is maintained in its own Moss session, and the resolver retrieves only evidence required by the proposed action.

Cloud-backed Moss indexes remain supported through `MOSS_RUNTIME_MODE=cloud`. Runtime semantics are the same in either mode.

A restart currently requires:

- restart policy
- current connection and reconciliation state
- recovery runbook

Optional incident history remains available as knowledge but is not allowed to add latency to a decision it cannot change.

## Evidence validation

Retrieved documents are validated before they influence policy. Validation covers:

- source type
- authority
- version
- environment
- incident scope
- updated timestamp
- freshness TTL

Missing or stale required context cannot silently authorize a high-impact action.

## Protected execution

Only an ALLOW result can issue an execution authorization. The executor rejects direct calls that do not carry that authorization.

## Postflight

Tool success is not treated as final truth. ActionProof compares the expected transition with observed state, records the postflight result, and updates the operational state used by the next decision.

The hero recovery path is therefore closed-loop:

```text
unsafe restart
    ↓
BLOCK
    ↓
reconcile
    ↓
postflight VERIFIED
    ↓
state update
    ↓
retry restart
    ↓
ALLOW
```

## Measurement

Preflight timing uses monotonic nanosecond clocks for:

- normalization
- context requirement resolution
- Moss retrieval
- freshness validation
- deterministic policy evaluation
- proof construction
- total preflight

The Latency Lab reports observed p50 / p95 / p99 / max and error rate from repeatable runs. Setup writes are excluded from timed samples.

# Architecture

ActionProof sits between an AI agent and a protected tool.

```text
Agent
  |
  v
ActionProof
  |
  +-- determine required context
  +-- retrieve context with Moss
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
Postflight check
```

## Why the decision is deterministic

The model can propose an action, but the final authorization result is produced from structured state, trusted policy, and retrieved evidence.

That keeps the safety decision reproducible and avoids making an LLM the final authority over a high-impact tool call.

## Retrieval

The retrieval layer is split into three kinds of context:

- policy
- runbooks / incident history
- current operational state

The runtime only asks for evidence relevant to the proposed action. A restart, for example, needs restart policy, connection state, reconciliation state, and the recovery runbook.

Retrieved documents are checked for metadata such as source, version, environment, incident scope, and freshness before they can influence the decision.

## Failure behavior

High-impact actions do not silently fall through to ALLOW when required context is missing, stale, or unavailable.

## Postflight

An allowed action is not considered complete just because the tool returned success. ActionProof compares expected state with observed state, records the result, and updates the operational context used by the next decision.

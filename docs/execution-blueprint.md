# ActionProof — Execution Blueprint V1

## Doctrine

Every implementation decision must purchase judge score. Priority:

```text
UX → CORRECTNESS → MOSS → MEASUREMENT → DEMO → EXTRA FEATURES
```

## Product contract

```text
EVENT
→ AGENT PROPOSES ACTION
→ ACTIONPROOF INTERCEPTS
→ MOSS RETRIEVES REQUIRED CONTEXT
→ CONTEXT IS VALIDATED
→ DETERMINISTIC POLICY IS EVALUATED
→ ACTION PROOF PACKET IS GENERATED
→ ALLOW / CONFIRM / BLOCK
→ AUTHORIZED ACTION EXECUTES
→ POSTFLIGHT VERIFIES RESULT
→ NEW STATE BECOMES RETRIEVABLE
```

## Runtime zones

Judge-facing UI; API/orchestrator/event stream; agent intent layer; proof engine; simulator + protected executor + postflight verifier. These are logical boundaries, not mandatory microservices.

## Canonical action

Every operation becomes typed before control logic. Natural language may exist before normalization; deterministic control begins after it.

## Context resolution

A restart retrieves only relevant evidence: service state, connection state, reconciliation state, restart policy, recovery runbook. No blind whole-index retrieval.

## Evidence contract

Moss responses are normalized into stable evidence records with source type, authority, version, score, update time, freshness and content. Raw SDK objects do not leak through application logic.

## Decision states

- ALLOW — complete/current evidence and policy satisfied.
- CONFIRM — evidence/authority incomplete or operator confirmation required.
- BLOCK — policy or required state forbids execution.

## Action Proof Packet

One immutable proof object drives UI, audit, tests, demo and benchmarks.

## Protected tool path

```text
Agent → ActionProof → proof-bound authorization → Tool Executor
```

No second unguarded path.

## Canonical scenarios

Safe Restart; Unsafe Restart; Missing Context; Stale Context; Successful Recovery.

## Phase 1 boundary

Phase 1 is a product shell and repository contract only. Fixture data may drive UI preview states. The final system may not mock Moss, policy execution, latency, or postflight behavior.

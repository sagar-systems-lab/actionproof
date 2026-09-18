# ActionProof — Canonical Demo Story

## Opening
CONNECTED · reconciliation COMPLETE · HEALTHY.

## Incident
Connection becomes DISCONNECTED; reconciliation INCOMPLETE; outstanding state UNKNOWN.

## Agent intent
The operations agent proposes `restart_service`.

## Preflight
ActionProof intercepts. Moss retrieves policy, current state and recovery runbook. UI shows retrieval progress and measured latency.

## Decision

```text
BLOCK
Reason: Restart requires completed reconciliation.
Safe next action: run_reconciliation
```

## Recovery
Reconciliation executes through the protected tool path.

## Postflight
ActionProof verifies `reconciliation=COMPLETE` and updates retrievable state.

## Retry
The original restart is proposed again; ActionProof retrieves the new state and returns ALLOW.

## Close
Mission Control ends healthy; Latency Lab shows measured distributions; one clean architecture diagram closes the demo.

**Rule:** start with the operational failure, not the technology stack.

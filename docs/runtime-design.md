# Closed-loop runtime

Phase 4 turns ActionProof from a decision service into an enforced control loop.

The runtime path is:

Agent intent -> normalization -> Moss retrieval -> deterministic policy -> proof -> single-use execution permit -> simulated tool -> postflight verification -> Moss live-state update.

## Authorization boundary

The protected executor never accepts a raw agent request. It requires an execution permit minted from an ALLOW result. The permit is bound to a SHA-256 fingerprint of:

- tool
- operation
- arguments
- incident ID

Changing the action after authorization invalidates the permit. Permits are single-use.

## Simulated tools

V1 keeps all side effects inside the deterministic simulator:

- reconciliation
- service restart
- connection recovery
- resume operations

There are no exchange credentials, financial operations, or external side effects.

## Postflight

Execution is not treated as success merely because the simulator returned. Expected state for the authorized operation is compared with the observed runtime state. Only a matching state produces VERIFIED.

After verified execution, the new operational state is written to the Moss live-state index. A later decision therefore retrieves the result of the previous action instead of relying on caller-supplied context.

## Hero loop

The canonical scenario is deterministic:

1. inject a disconnect with incomplete reconciliation
2. evaluate restart
3. retrieve Moss context and block restart
4. surface run_reconciliation
5. evaluate and authorize reconciliation
6. execute through the protected executor
7. verify postflight state
8. publish the new state to Moss
9. retry restart
10. retrieve the updated state and allow restart

## Flight recorder and SSE

Every runtime session appends ordered events with sequence, trace ID, UTC timestamp, event type, and summary.

The API exposes:

- GET /api/runtime/events for a snapshot
- GET /api/runtime/events/stream for server-sent events
- POST /api/runtime/hero for the deterministic closed-loop scenario

The recorder is append-only for the lifetime of the process and is the source for the Phase 5 incident timeline.

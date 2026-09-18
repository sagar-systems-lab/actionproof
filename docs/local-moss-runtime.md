# Local Moss runtime

ActionProof supports a local Moss runtime mode for the decision path.

The mode uses Moss SessionIndex objects directly in-process. Policy, runbook, and initial live-state documents are seeded from the repository at process startup, semantic queries run locally, and dynamic live state is updated in the live SessionIndex.

This is still the real Moss retrieval path. The application does not replace Moss with a Python dictionary, mock retriever, or fixture decision.

## Why local mode exists

The product needs low-latency retrieval during protected actions. It also needs the demo to remain runnable when cloud index credits are unavailable.

Moss SessionIndex is designed for local, in-process add/query workloads. ActionProof therefore treats cloud indexes as an optional persistence/distribution layer rather than a hard dependency of every preflight.

## Configuration

Local mode is the default:

```text
MOSS_RUNTIME_MODE=local
```

Cloud-backed mode remains available:

```text
MOSS_RUNTIME_MODE=cloud
```

Both modes still require the Moss project credentials.

## Local mode behavior

At startup ActionProof creates three Moss SessionIndex instances:

- policy
- knowledge
- live state

Policy and knowledge documents are loaded from the repository datasets. Live state starts from the canonical demo state and is then updated by the runtime as scenarios execute.

Nothing is pushed to Moss cloud in local mode.

## Integrity

Decision semantics do not change between runtime modes:

- the agent action is normalized
- the resolver selects required evidence
- Moss retrieves policy/runbook/live state
- metadata and freshness are validated
- deterministic policy returns ALLOW / CONFIRM / BLOCK
- proof assembly records the retrieved Moss evidence
- runtime execution and postflight remain unchanged

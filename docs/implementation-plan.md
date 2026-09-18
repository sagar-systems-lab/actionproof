# ActionProof — Seven-Phase Implementation Plan V1

Phases are blocking. A later phase does not begin until the current phase passes its gate and Sagar approves merge.

1. **Product Foundation + Judge Contract**
2. **Deterministic Control Core**
3. **Moss Critical-Path Retrieval**
4. **Closed-Loop Runtime + Enforcement**
5. **Judge-Facing Product Experience**
6. **Performance + Reliability + Deployment Qualification**
7. **Submission Freeze + Judge Attack**

## Branches

```text
main
phase/01-foundation
phase/02-control-core
phase/03-moss-retrieval
phase/04-runtime-loop
phase/05-product-ux
phase/06-qualification
phase/07-submission
```

`main` receives only reviewed phase work. Failed phase work stays on its branch until fixed.

## Non-negotiables

No feature creep, architecture drift, TREX IP, real-money trading, fabricated metrics, final mock Moss, LLM safety authority, direct protected-tool bypass, public secrets, or premature low-level optimization.

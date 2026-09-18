# Preflight retrieval scope

Restart authorization waits only for evidence that can change the decision:

- restart policy
- current live state
- recovery runbook

Incident history remains seeded in Moss for product exploration, but it is not required to authorize or block a restart. Keeping optional history off the preflight path avoids spending retrieval time on evidence that cannot change the deterministic decision.

The Proof Inspector contract still exposes the required policy, state, runbook, freshness, matched rule, decision code, trace, and latency.

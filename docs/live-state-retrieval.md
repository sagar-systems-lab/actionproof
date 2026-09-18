# Live-state retrieval path

ActionProof keeps policy and runbook search on loaded Moss semantic indexes.

Live operational state uses a Moss SessionIndex instead of the cloud management get_docs API. The profiler showed that semantic policy/runbook queries were single-digit milliseconds while cloud document reads were roughly 0.6 seconds each on the test machine. A Moss session keeps live-state add/read operations in-process after startup, which removes that network round trip from the preflight path.

The live-state session is still Moss-backed: it is opened from the configured Moss index, updated with session.add_docs, and read with session.get_docs. Static policy/runbook evidence continues to use semantic Moss retrieval.

This change is intentionally limited to the measured bottleneck. It does not alter policy semantics, decision codes, proof contents, or the scenario contract.

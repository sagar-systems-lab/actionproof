# Retrieval design

ActionProof uses Moss in the authorization path rather than as an explanation-only lookup.

Three indexes are kept separate:

- `actionproof-policy` — authoritative policy
- `actionproof-knowledge` — runbooks and incident history
- `actionproof-live-state` — current operational state

The action normalizer runs first. A context requirement resolver then asks only for evidence relevant to the normalized operation. A restart needs restart policy, current incident state, and a recovery runbook. Similar incident history is useful but is not required to authorize the action.

Moss responses are normalized before application code sees them. Each item must carry source type, authority, version, environment, update time, and TTL. Incident-scoped state must also match the incident being evaluated.

Dynamic state is freshness-sensitive. Stale required evidence cannot silently authorize a high-impact action. A retrieval failure on a required query fails closed.

Independent policy, state, and runbook lookups are issued concurrently. Retrieval timing is measured with a monotonic high-resolution clock and stored in the proof packet.

## Local setup

Copy `.env.example` to `.env`, add Moss project credentials, then run:

```bash
python scripts/seed_moss.py
python scripts/verify_moss.py
```

The verification command must retrieve policy, runbook, and live-state evidence from Moss and produce the expected blocked restart decision.

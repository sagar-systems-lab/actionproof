# Product requirements

## Goal

Make high-impact AI-agent actions inspectable and safe to execute without turning every tool call into a slow manual review.

## Core user

An engineer or operator running an AI agent that can change production state.

## Main workflow

1. Agent proposes a tool action.
2. ActionProof determines what evidence is required.
3. Moss retrieves the relevant policy, state, and runbook.
4. Retrieved context is checked for authority and freshness.
5. Deterministic policy returns ALLOW, CONFIRM, or BLOCK.
6. The UI shows the reason and evidence.
7. Allowed actions run through a protected executor.
8. The result is checked again after execution.

## First scenario

A service disconnects while reconciliation is incomplete. The agent proposes a restart. ActionProof blocks it, recommends reconciliation, verifies the recovery, then allows the restart when the state is safe.

## Required product surfaces

- Mission Control
- Proof Inspector
- Scenario Lab
- Latency Lab

## Reliability requirements

- no direct path from agent to protected tool
- missing or stale required context cannot silently authorize a high-impact action
- LLM output cannot override deterministic policy
- UI evidence must match the evidence used by the decision
- published latency must come from measured runtime data

## Out of scope

Real-money trading, exchange credentials, custom model training, distributed consensus, kernel tuning, and unrelated infrastructure complexity.

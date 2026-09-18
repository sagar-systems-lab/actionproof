# ActionProof — Product Requirements Document V1

## Product statement

**ActionProof is a real-time context-proof and safety gate for AI agents.** Every consequential action must arrive with enough current evidence to justify execution.

## Problem

AI agents increasingly invoke tools that restart services, deploy software, modify infrastructure, alter records, or perform financial workflows. A model can generate a plausible action while operating on missing, stale, or incomplete operational context. Valid tool permission therefore does not imply that an action is safe *right now*.

## Target users

Teams operating AI agents that can change production systems or invoke consequential tools: DevOps/SRE, cloud operations, cybersecurity response, autonomous developer tooling, financial workflow automation, and trading-infrastructure operations.

## Core job

Before a high-impact action executes, determine whether current evidence is sufficient and policy-compliant, make the decision inspectable, and verify the result after execution.

## V1 functional requirements

1. Normalize intent into a typed action.
2. Resolve required evidence.
3. Retrieve policy, state and recovery context with Moss.
4. Validate authority, version, scope and freshness.
5. Produce deterministic ALLOW / CONFIRM / BLOCK.
6. Generate an immutable Action Proof Packet.
7. Prevent protected-tool execution without valid authorization.
8. Verify expected versus observed state postflight.
9. Make updated state retrievable.
10. Expose reason, evidence, safe next action, trace and latency in UI.

## Product surfaces

Mission Control; Proof Inspector; Scenario Lab; Latency Lab.

## Reliability requirements

Fail closed on unverifiable high-impact context; stale required state cannot authorize; LLM cannot override policy; no direct tool bypass; displayed latency and evidence must be real.

## Non-goals

No real-money trading, exchange credentials, Kubernetes, distributed consensus, custom vector database/model, FPGA/kernel tuning, voice pipeline, or multi-agent swarm.

## Success criterion

A judge can trigger the unsafe incident, see ActionProof block it with evidence, execute reconciliation, observe postflight verification, retry and see ALLOW, inspect proof, and run latency measurement without a terminal.

export type DecisionStatus = 'ALLOW' | 'CONFIRM' | 'BLOCK'
export type Freshness = 'FRESH' | 'STALE' | 'UNKNOWN'

export type SimulatorState = {
  connection: string
  reconciliation: string
  service: string
  health: string
  outstanding: string
}

export type NormalizedAction = {
  action_id: string
  trace_id: string
  actor: string
  tool: string
  operation: string
  arguments: Record<string, unknown>
  impact: string
  incident_id: string
  timestamp: string
}

export type PolicyDecision = {
  status: DecisionStatus
  code: string
  matched_rule: string
  reason: string
  recommended_next_action: string | null
}

export type EvidenceFact = {
  source: string
  key: string
  value: string
  document_id: string | null
  source_type: string | null
  authority: string | null
  version: string | null
  freshness: Freshness | null
  score: number | null
  updated_at: string | null
}

export type LatencyBreakdown = {
  retrieval_us: number
  freshness_us: number
  policy_us: number
  proof_us: number
  total_us: number
}

export type ProofPacket = {
  proof_id: string
  trace_id: string
  action: NormalizedAction
  risk: string
  decision: DecisionStatus
  decision_code: string
  evidence: EvidenceFact[]
  matched_policy: string
  safe_next_action: string | null
  latency: LatencyBreakdown
}

export type EvaluationResult = {
  action: NormalizedAction
  decision: PolicyDecision
  proof: ProofPacket
}

export type ToolExecutionResult = {
  success: boolean
  state_changes: Record<string, string>
  message: string
  state: SimulatorState
}

export type PostflightResult = {
  status: 'VERIFIED' | 'FAILED'
  expected: Record<string, string>
  observed: Record<string, string>
  message: string
}

export type ExecutedActionResult = {
  evaluation: EvaluationResult
  execution: ToolExecutionResult
  postflight: PostflightResult
}

export type RuntimeEvent = {
  sequence: number
  trace_id: string
  event: string
  timestamp: string
  summary: string
}

export type ScenarioDefinition = {
  id: string
  label: string
  description: string
  expected: string
}

export type ProductScenarioResult = {
  scenario_id: string
  label: string
  description: string
  incident_id: string
  initial_state: SimulatorState | null
  primary_evaluation: EvaluationResult
  recovery: ExecutedActionResult | null
  final_evaluation: EvaluationResult | null
  final_state: SimulatorState | null
  events: RuntimeEvent[]
}

export type RetrievalStatus = {
  configured: boolean
  environment: string
  indexes: {
    policy: string
    knowledge: string
    live_state: string
  }
}

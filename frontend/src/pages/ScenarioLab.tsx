import { useEffect, useMemo, useState } from 'react'
import type {
  ProductScenarioResult,
  RuntimeEvent,
  ScenarioDefinition,
} from '../types'

type Props = {
  scenarios: ScenarioDefinition[]
  result: ProductScenarioResult | null
  runningId: string | null
  runStartedAt: number | null
  events: RuntimeEvent[]
  apiOnline: boolean
  onRun: (id: string) => void
}

function expectedTone(expected: string) {
  if (expected.includes('ALLOW') && !expected.includes('BLOCK')) return 'allow'
  if (expected.includes('CONFIRM')) return 'confirm'
  if (expected.includes('BLOCK')) return 'block'
  return 'neutral'
}

const STAGE_LABELS: Record<string, string> = {
  SCENARIO_STARTED: 'Scenario started',
  INCIDENT_CREATED: 'Loading incident state',
  AGENT_INTENT_CREATED: 'Preparing agent action',
  ACTION_NORMALIZED: 'Classifying protected action',
  MOSS_QUERY_STARTED: 'Retrieving Moss context',
  MOSS_QUERY_COMPLETED: 'Moss context retrieved',
  CONTEXT_VALIDATED: 'Validating context',
  POLICY_EVALUATED: 'Applying policy',
  PROOF_CREATED: 'Building proof packet',
  ACTION_BLOCKED: 'Action blocked safely',
  ACTION_ALLOWED: 'Action authorized',
  ACTION_EXECUTED: 'Executing protected action',
  POSTFLIGHT_VERIFIED: 'Verifying postflight state',
  POSTFLIGHT_FAILED: 'Postflight verification failed',
}

export default function ScenarioLab({
  scenarios,
  result,
  runningId,
  runStartedAt,
  events,
  apiOnline,
  onRun,
}: Props) {
  const [now, setNow] = useState(Date.now())

  useEffect(() => {
    if (!runningId) return undefined
    const timer = window.setInterval(() => setNow(Date.now()), 200)
    return () => window.clearInterval(timer)
  }, [runningId])

  const activeScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === runningId) || null,
    [runningId, scenarios],
  )
  const latestEvent = events.length ? events[events.length - 1] : null
  const stage = latestEvent
    ? STAGE_LABELS[latestEvent.event] || 'Runtime progressing'
    : 'Starting protected runtime'
  const elapsedSeconds = runStartedAt
    ? Math.max(0, (now - runStartedAt) / 1000)
    : 0

  return (
    <main className="workspace utility-view">
      <section className="page-heading">
        <div>
          <div className="breadcrumb">ActionProof / Scenario Lab</div>
          <h1>Five deterministic cases. One protected runtime.</h1>
          <p>
            Every run uses the same Moss retrieval, policy, proof, and runtime path shown in Mission Control.
          </p>
        </div>
      </section>

      <section className="card scenario-table">
        <div className="scenario-table-head">
          <span>Scenario</span>
          <span>What it proves</span>
          <span>Expected</span>
          <span />
        </div>
        {scenarios.map((scenario) => {
          const isRunning = runningId === scenario.id
          const wasLast = result?.scenario_id === scenario.id
          return (
            <article
              className={[
                'scenario-line',
                wasLast ? 'last-run' : '',
                isRunning ? 'scenario-running' : '',
              ].filter(Boolean).join(' ')}
              key={scenario.id}
            >
              <div>
                <strong>{scenario.label}</strong>
                <code>{scenario.id}</code>
              </div>
              <p>{scenario.description}</p>
              <span className={`expected-chip ${expectedTone(scenario.expected)}`}>{scenario.expected}</span>
              <button
                className="button secondary"
                onClick={() => onRun(scenario.id)}
                disabled={Boolean(runningId) || !apiOnline}
              >
                {isRunning ? 'Running…' : 'Run live'}
              </button>
            </article>
          )
        })}
      </section>

      {runningId && (
        <section className="card scenario-run-status" aria-live="polite">
          <div className="scenario-run-head">
            <div>
              <span className="scenario-live-dot" />
              <strong>{activeScenario?.label || 'Scenario'} is running</strong>
            </div>
            <span>{elapsedSeconds.toFixed(1)} s elapsed</span>
          </div>

          <div className="scenario-run-stage">
            <strong>{stage}</strong>
            <span>{latestEvent?.summary || 'Waiting for the first runtime event.'}</span>
          </div>

          <div className="scenario-run-track">
            <div />
          </div>

          <div className="scenario-run-meta">
            <span>{events.length} runtime event{events.length === 1 ? '' : 's'} received</span>
            <span>The result opens in Mission Control when the run completes.</span>
          </div>
        </section>
      )}

      <section className="scenario-note">
        <strong>No fixture decisions.</strong>
        <span>
          Scenario controls mutate or omit actual runtime context, then ask ActionProof to retrieve and decide.
        </span>
      </section>
    </main>
  )
}

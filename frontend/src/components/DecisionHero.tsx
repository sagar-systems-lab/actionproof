import type { EvaluationResult } from '../types'
import LatencyCard from './LatencyCard'

type Props = {
  evaluation: EvaluationResult | null
  scenarioLabel: string | null
  loading: boolean
  hasFinal: boolean
  showingFinal: boolean
  onToggleFinal: () => void
  onViewProof: () => void
}

const titles = {
  ALLOW: 'Action allowed',
  CONFIRM: 'Confirmation required',
  BLOCK: 'Action blocked',
} as const

function operationLabel(operation?: string) {
  if (!operation) return 'No live action yet'
  return operation.replaceAll('_', ' ')
}

export default function DecisionHero({
  evaluation,
  scenarioLabel,
  loading,
  hasFinal,
  showingFinal,
  onToggleFinal,
  onViewProof,
}: Props) {
  const status = evaluation?.decision.status
  const tone = status?.toLowerCase() || 'idle'

  return (
    <section className={`card decision-hero decision-${tone}`}>
      <div className="decision-accent" />
      <div className="decision-heading">
        <div>
          <span className="section-kicker">DECISION</span>
          <h1>{loading ? 'Evaluating live context…' : status ? titles[status] : 'No action evaluated'}</h1>
          <p>
            {evaluation
              ? evaluation.decision.reason
              : 'Run a scenario to intercept an agent action and build a real proof packet.'}
          </p>
        </div>
        <span className={`decision-pill ${tone}`}>{status || 'READY'}</span>
      </div>

      <div className="proposed-action">
        <div>
          <span className="section-kicker">PROPOSED ACTION</span>
          <strong>{operationLabel(evaluation?.action.operation)}</strong>
        </div>
        {scenarioLabel && <span className="scenario-chip">{scenarioLabel}</span>}
      </div>

      <div className="why-next-grid">
        <div>
          <span className="section-kicker">WHY</span>
          <p>{evaluation?.decision.reason || 'No policy decision has been made yet.'}</p>
        </div>
        <div className="next-action">
          <span className="section-kicker">SAFE NEXT ACTION</span>
          <p>{evaluation?.decision.recommended_next_action?.replaceAll('_', ' ') || (status === 'ALLOW' ? 'Proceed through protected execution.' : 'Run a scenario to establish the next action.')}</p>
        </div>
      </div>

      <LatencyCard evaluation={evaluation} />

      <div className="decision-meta">
        <div>
          <span>Decision code</span>
          <code>{evaluation?.decision.code || '—'}</code>
        </div>
        <div>
          <span>Proof</span>
          <code>{evaluation?.proof.proof_id || '—'}</code>
        </div>
        <div className="decision-actions">
          {hasFinal && (
            <button className="button secondary" onClick={onToggleFinal}>
              {showingFinal ? 'View initial block' : 'View after recovery'}
            </button>
          )}
          <button className="button primary" onClick={onViewProof} disabled={!evaluation}>
            View proof
          </button>
        </div>
      </div>
    </section>
  )
}

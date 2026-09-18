import type {
  EvaluationResult,
  ProductScenarioResult,
  RuntimeEvent,
} from '../types'
import DecisionHero from '../components/DecisionHero'
import IncidentTimeline from '../components/IncidentTimeline'
import StatePanel from '../components/StatePanel'

type Props = {
  result: ProductScenarioResult | null
  events: RuntimeEvent[]
  apiOnline: boolean
  mossConfigured: boolean
  streamLive: boolean
  loading: boolean
  showingFinal: boolean
  onToggleFinal: () => void
  onViewProof: () => void
  onRunHero: () => void
}

function evidenceLabel(evaluation: EvaluationResult | null) {
  if (!evaluation) return 'No proof yet'
  return `${evaluation.proof.evidence.length} retrieved records`
}

export default function MissionControl({
  result,
  events,
  apiOnline,
  mossConfigured,
  streamLive,
  loading,
  showingFinal,
  onToggleFinal,
  onViewProof,
  onRunHero,
}: Props) {
  const evaluation = showingFinal && result?.final_evaluation
    ? result.final_evaluation
    : result?.primary_evaluation || null
  const state = showingFinal && result?.final_state
    ? result.final_state
    : result?.initial_state || null

  const evidence = evaluation?.proof.evidence.slice(0, 3) || []

  return (
    <main className="workspace">
      <section className="page-heading mission-heading">
        <div>
          <div className="breadcrumb">ActionProof / Mission Control</div>
          <h1>Every high-impact agent action should carry its proof.</h1>
          <p>
            ActionProof retrieves live Moss context, applies deterministic policy, and verifies what happened after execution.
          </p>
        </div>
        <button className="button hero-run" onClick={onRunHero} disabled={loading || !apiOnline}>
          {loading ? 'Running live scenario…' : 'Run recovery scenario'}
        </button>
      </section>

      <section className="mission-grid">
        <StatePanel
          state={state}
          incidentId={result?.incident_id || null}
          apiOnline={apiOnline}
          mossConfigured={mossConfigured}
        />

        <DecisionHero
          evaluation={evaluation}
          scenarioLabel={result?.label || null}
          loading={loading}
          hasFinal={Boolean(result?.final_evaluation)}
          showingFinal={showingFinal}
          onToggleFinal={onToggleFinal}
          onViewProof={onViewProof}
        />

        <aside className="card evidence-preview">
          <div className="card-header">
            <div>
              <span className="section-kicker">MOSS EVIDENCE</span>
              <h2>{evidenceLabel(evaluation)}</h2>
            </div>
            {evaluation && <span className="fresh-chip">inspected</span>}
          </div>

          {evidence.length ? (
            <div className="evidence-preview-list">
              {evidence.map((item, index) => (
                <article key={`${item.document_id || item.key}-${index}`}>
                  <div>
                    <span className="source-chip">{item.source_type || item.key}</span>
                    <code>{item.document_id || item.key}</code>
                  </div>
                  <p>{item.value}</p>
                  <footer>
                    <span>{item.authority || 'unknown authority'}</span>
                    <span className={(item.freshness || '').toLowerCase()}>{item.freshness || '—'}</span>
                  </footer>
                </article>
              ))}
              <button className="text-button" onClick={onViewProof}>Inspect complete proof →</button>
            </div>
          ) : (
            <div className="panel-empty">
              <strong>No retrieved evidence yet</strong>
              <span>Run a scenario to see policy, live state, runbook, authority, freshness, and trace.</span>
            </div>
          )}
        </aside>

        {result?.recovery && (
          <section className="recovery-strip card">
            <div>
              <span className="section-kicker">RECOVERY ACTION</span>
              <strong>{result.recovery.evaluation.action.operation.replaceAll('_', ' ')}</strong>
            </div>
            <div>
              <span className="section-kicker">POSTFLIGHT</span>
              <strong className={result.recovery.postflight.status === 'VERIFIED' ? 'good-text' : 'bad-text'}>
                {result.recovery.postflight.status}
              </strong>
            </div>
            <div>
              <span className="section-kicker">RETRY</span>
              <strong className="good-text">{result.final_evaluation?.decision.status || '—'}</strong>
            </div>
            <p>{result.recovery.postflight.message}</p>
          </section>
        )}

        <IncidentTimeline events={events} live={streamLive} />
      </section>
    </main>
  )
}

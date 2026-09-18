import type { EvaluationResult, ProductScenarioResult } from '../types'
import { formatMicros } from '../components/LatencyCard'

type Props = {
  result: ProductScenarioResult | null
  showingFinal: boolean
}

function metricRows(evaluation: EvaluationResult | null) {
  const latency = evaluation?.proof.latency
  return [
    ['Moss retrieval', latency?.retrieval_us],
    ['Freshness validation', latency?.freshness_us],
    ['Policy evaluation', latency?.policy_us],
    ['Proof assembly', latency?.proof_us],
    ['Total preflight', latency?.total_us],
  ] as const
}

export default function LatencyLab({ result, showingFinal }: Props) {
  const evaluation = showingFinal && result?.final_evaluation
    ? result.final_evaluation
    : result?.primary_evaluation || null

  return (
    <main className="workspace utility-view">
      <section className="page-heading">
        <div>
          <div className="breadcrumb">ActionProof / Latency Lab</div>
          <h1>Observed preflight timing</h1>
          <p>
            These values come from the latest live action. No benchmark distribution is shown until a real benchmark run exists.
          </p>
        </div>
      </section>

      <section className="latency-lab-grid">
        <div className="card latest-run-card">
          <div className="card-header">
            <div>
              <span className="section-kicker">LATEST ACTION</span>
              <h2>{result?.label || 'No run yet'}</h2>
            </div>
            {evaluation && <code>{evaluation.proof.proof_id}</code>}
          </div>
          <div className="latency-detail-list">
            {metricRows(evaluation).map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{formatMicros(value)}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="card benchmark-placeholder">
          <span className="section-kicker">DISTRIBUTION BENCHMARK</span>
          <h2>p50 / p95 / p99 / max</h2>
          <p>
            Not published yet. ActionProof will only show a distribution after the reproducible benchmark harness has measured it.
          </p>
          <div className="benchmark-empty-grid">
            {['p50', 'p95', 'p99', 'max'].map((label) => (
              <div key={label}><span>{label}</span><strong>—</strong></div>
            ))}
          </div>
          <small>No fabricated latency numbers.</small>
        </div>
      </section>
    </main>
  )
}

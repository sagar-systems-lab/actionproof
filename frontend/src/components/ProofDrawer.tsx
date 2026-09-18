import type { EvaluationResult } from '../types'
import { formatMicros } from './LatencyCard'

type Props = {
  evaluation: EvaluationResult | null
  open: boolean
  onClose: () => void
}

export default function ProofDrawer({ evaluation, open, onClose }: Props) {
  if (!open || !evaluation) return null

  const { proof, decision } = evaluation

  return (
    <div className="drawer-backdrop" role="presentation" onMouseDown={onClose}>
      <aside
        className="proof-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="Action proof inspector"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="drawer-header">
          <div>
            <span className="section-kicker">ACTION PROOF</span>
            <h2>{proof.proof_id}</h2>
            <p>Evidence used by the deterministic decision path.</p>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close proof inspector">×</button>
        </div>

        <div className="proof-summary">
          <div><span>Decision</span><strong className={decision.status.toLowerCase()}>{decision.status}</strong></div>
          <div><span>Decision code</span><code>{decision.code}</code></div>
          <div><span>Matched rule</span><code>{decision.matched_rule}</code></div>
          <div><span>Trace</span><code>{proof.trace_id}</code></div>
        </div>

        <section className="drawer-section">
          <div className="drawer-section-title">
            <span className="section-kicker">RETRIEVED EVIDENCE</span>
            <strong>{proof.evidence.length} records</strong>
          </div>
          <div className="proof-evidence-list">
            {proof.evidence.map((item, index) => (
              <article key={`${item.document_id || item.key}-${index}`}>
                <div className="proof-evidence-head">
                  <span className="source-chip">{(item.source_type || item.key).replaceAll('_', ' ')}</span>
                  <code>{item.document_id || item.key}</code>
                </div>
                <p>{item.value}</p>
                <dl>
                  <div><dt>Authority</dt><dd>{item.authority || '—'}</dd></div>
                  <div><dt>Version</dt><dd>{item.version || '—'}</dd></div>
                  <div><dt>Freshness</dt><dd className={(item.freshness || '').toLowerCase()}>{item.freshness || '—'}</dd></div>
                  <div><dt>Score</dt><dd>{item.score === null ? '—' : item.score.toFixed(3)}</dd></div>
                </dl>
              </article>
            ))}
          </div>
        </section>

        <section className="drawer-section">
          <span className="section-kicker">LATENCY BREAKDOWN</span>
          <div className="proof-latency-grid">
            <div><span>Moss retrieval</span><strong>{formatMicros(proof.latency.retrieval_us)}</strong></div>
            <div><span>Freshness</span><strong>{formatMicros(proof.latency.freshness_us)}</strong></div>
            <div><span>Policy</span><strong>{formatMicros(proof.latency.policy_us)}</strong></div>
            <div><span>Proof build</span><strong>{formatMicros(proof.latency.proof_us)}</strong></div>
            <div className="total"><span>Total preflight</span><strong>{formatMicros(proof.latency.total_us)}</strong></div>
          </div>
          <p className="measurement-note">Observed values from this action only. Distribution benchmarks are reported separately.</p>
        </section>
      </aside>
    </div>
  )
}

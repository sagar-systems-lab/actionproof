import type { EvaluationResult } from '../types'

type Props = {
  evaluation: EvaluationResult | null
}

function formatMicros(value?: number) {
  if (value === undefined) return '—'
  if (value < 1000) return `${value.toLocaleString()} µs`
  return `${(value / 1000).toFixed(value < 10000 ? 2 : 1)} ms`
}

export default function LatencyCard({ evaluation }: Props) {
  const latency = evaluation?.proof.latency

  return (
    <div className="latency-inline">
      <div>
        <span>Moss retrieval</span>
        <strong>{formatMicros(latency?.retrieval_us)}</strong>
        <small>{latency ? 'observed this action' : 'not measured'}</small>
      </div>
      <div>
        <span>Policy</span>
        <strong>{formatMicros(latency?.policy_us)}</strong>
        <small>{latency ? 'deterministic evaluation' : 'not measured'}</small>
      </div>
      <div>
        <span>Total preflight</span>
        <strong>{formatMicros(latency?.total_us)}</strong>
        <small>{latency ? 'observed this action' : 'not measured'}</small>
      </div>
    </div>
  )
}

export { formatMicros }

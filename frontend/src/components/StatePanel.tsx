import type { SimulatorState } from '../types'

type Props = {
  state: SimulatorState | null
  incidentId: string | null
  apiOnline: boolean
  mossConfigured: boolean
}

function stateTone(value: string) {
  if (['CONNECTED', 'COMPLETE', 'HEALTHY', 'CLEAR', 'RUNNING'].includes(value)) return 'good'
  if (value === 'UNKNOWN') return 'warn'
  return 'bad'
}

export default function StatePanel({ state, incidentId, apiOnline, mossConfigured }: Props) {
  const rows = state
    ? [
        ['Connection', state.connection],
        ['Reconciliation', state.reconciliation],
        ['Service', state.service],
        ['Health', state.health],
        ['Outstanding', state.outstanding],
      ]
    : []

  return (
    <aside className="card state-panel">
      <div className="card-header">
        <div className="state-heading-copy">
          <span className="section-kicker">SYSTEM STATUS</span>
          <h2 title={incidentId || undefined}>{incidentId || 'No live incident'}</h2>
        </div>
        <span className={apiOnline && mossConfigured ? 'health-chip live' : 'health-chip'}>
          <span className="health-dot" />
          {apiOnline && mossConfigured ? 'runtime ready' : 'waiting'}
        </span>
      </div>

      {state ? (
        <div className="state-rows">
          {rows.map(([label, value]) => (
            <div className="state-row" key={label}>
              <span>{label}</span>
              <strong className={stateTone(value)}>
                <span className="status-dot" />
                {value}
              </strong>
            </div>
          ))}
        </div>
      ) : (
        <div className="panel-empty">
          <strong>No operational state loaded</strong>
          <span>Run a scenario to retrieve current state from Moss.</span>
        </div>
      )}

      <div className="runtime-contract">
        <span>Control plane</span>
        <strong>Deterministic policy</strong>
        <span>Context source</span>
        <strong>{mossConfigured ? 'Moss / live' : 'Moss / not configured'}</strong>
      </div>
    </aside>
  )
}

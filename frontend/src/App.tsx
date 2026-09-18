import { useMemo, useState } from 'react'

type Decision = 'ALLOW' | 'CONFIRM' | 'BLOCK'
type Page = 'Mission' | 'Scenarios' | 'Latency'

type Fixture = {
  decision: Decision
  title: string
  reason: string
  next: string
  connection: string
  reconciliation: string
  health: string
  code: string
}

const fixtures: Record<Decision, Fixture> = {
  ALLOW: {
    decision: 'ALLOW',
    title: 'Restart authorized',
    reason: 'Connection is stable and reconciliation is complete.',
    next: 'Execute restart, then verify the observed service state.',
    connection: 'CONNECTED',
    reconciliation: 'COMPLETE',
    health: 'HEALTHY',
    code: 'ALLOW_SAFE_STATE',
  },
  CONFIRM: {
    decision: 'CONFIRM',
    title: 'Operator confirmation required',
    reason: 'The reconciliation state cannot be established from current evidence.',
    next: 'Refresh operational state or confirm the action manually.',
    connection: 'CONNECTED',
    reconciliation: 'UNKNOWN',
    health: 'DEGRADED',
    code: 'CONFIRM_CONTEXT_INCOMPLETE',
  },
  BLOCK: {
    decision: 'BLOCK',
    title: 'Restart blocked',
    reason: 'Reconciliation is incomplete. Restarting now may leave external state unresolved.',
    next: 'Run reconciliation before restarting the service.',
    connection: 'DISCONNECTED',
    reconciliation: 'INCOMPLETE',
    health: 'DEGRADED',
    code: 'BLOCK_RECONCILIATION_REQUIRED',
  },
}

const events = [
  ['12:14:01.001', 'incident.opened', 'connection dropped'],
  ['12:14:01.104', 'agent.intent', 'restart_service'],
  ['12:14:01.106', 'context.plan', 'policy + state + runbook'],
  ['12:14:01.112', 'context.ready', '3 evidence records'],
  ['12:14:01.114', 'policy.result', 'restart policy evaluated'],
  ['12:14:01.115', 'decision.recorded', 'proof AP-104 written'],
]

function StatusValue({ value }: { value: string }) {
  const cls = value === 'HEALTHY' || value === 'CONNECTED' || value === 'COMPLETE'
    ? 'good'
    : value === 'UNKNOWN'
      ? 'warn'
      : 'bad'
  return <span className={`status-value ${cls}`}>{value}</span>
}

function MissionView({ fixture }: { fixture: Fixture }) {
  return (
    <main className="workspace">
      <aside className="left-rail">
        <div className="section-title">
          <span>INCIDENT</span>
          <strong>INC-104</strong>
        </div>

        <div className="incident-summary">
          <div className="incident-kicker">execution-service</div>
          <h2>Connection recovery</h2>
          <p>Agent is attempting a protected restart while service state is degraded.</p>
        </div>

        <div className="state-table">
          <div><span>Connection</span><StatusValue value={fixture.connection} /></div>
          <div><span>Reconciliation</span><StatusValue value={fixture.reconciliation} /></div>
          <div><span>Health</span><StatusValue value={fixture.health} /></div>
        </div>

        <div className="rail-note">
          <span>Actor</span>
          <strong>operations-agent</strong>
          <span>Resource</span>
          <strong>execution-service</strong>
        </div>
      </aside>

      <section className="decision-pane">
        <div className={`decision-strip state-${fixture.decision.toLowerCase()}`}>
          <div>
            <span className="mono-label">DECISION / {fixture.code}</span>
            <h1>{fixture.title}</h1>
          </div>
          <strong className="decision-state">{fixture.decision}</strong>
        </div>

        <div className="decision-body">
          <div className="intent-row">
            <span className="mono-label">PROPOSED TOOL CALL</span>
            <code>restart_service()</code>
          </div>

          <div className="reason-block">
            <span className="mono-label">WHY</span>
            <p>{fixture.reason}</p>
          </div>

          <div className="next-block">
            <span className="mono-label">SAFE NEXT ACTION</span>
            <p>{fixture.next}</p>
          </div>

          <div className="timing-row">
            <div>
              <span className="mono-label">RETRIEVAL</span>
              <strong>—</strong>
              <small>not measured</small>
            </div>
            <div>
              <span className="mono-label">POLICY</span>
              <strong>—</strong>
              <small>not measured</small>
            </div>
            <div>
              <span className="mono-label">TOTAL PREFLIGHT</span>
              <strong>—</strong>
              <small>not measured</small>
            </div>
          </div>
        </div>
      </section>

      <aside className="right-rail">
        <div className="section-title">
          <span>EVIDENCE</span>
          <strong>3 records</strong>
        </div>

        <div className="evidence-list">
          <article>
            <div><span className="evidence-type">POLICY</span><strong>POL-RESTART-001</strong></div>
            <p>Restart requires completed reconciliation.</p>
            <footer><span>authority: system</span><span>v4</span></footer>
          </article>

          <article>
            <div><span className="evidence-type">STATE</span><strong>INC-104</strong></div>
            <p>reconciliation = {fixture.reconciliation}</p>
            <footer><span>source: runtime</span><span>current</span></footer>
          </article>

          <article>
            <div><span className="evidence-type">RUNBOOK</span><strong>RB-DISCONNECT-004</strong></div>
            <p>Reconcile external state before service recovery.</p>
            <footer><span>owner: ops</span><span>v2</span></footer>
          </article>
        </div>
      </aside>

      <section className="event-log">
        <div className="section-title">
          <span>EVENT LOG</span>
          <strong>trace AP-104</strong>
        </div>
        <div className="event-table">
          {events.map(([time, type, detail]) => (
            <div className="event-row" key={time}>
              <time>{time}</time>
              <code>{type}</code>
              <span>{detail}</span>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}

function ScenarioView() {
  const scenarios = [
    ['safe-restart', 'Connected / reconciled / healthy', 'ALLOW'],
    ['unsafe-restart', 'Disconnected / reconciliation incomplete', 'BLOCK'],
    ['missing-context', 'Reconciliation state unavailable', 'CONFIRM'],
    ['stale-state', 'Required state is outside freshness window', 'BLOCK'],
    ['recovered-retry', 'Reconcile / verify / retry restart', 'ALLOW'],
  ]

  return (
    <main className="utility-page">
      <div className="utility-head">
        <div><span className="mono-label">SCENARIO LAB</span><h1>Repeatable incident cases</h1></div>
        <p>Small deterministic cases used to exercise the same decision path without relying on live failures.</p>
      </div>
      <div className="scenario-table">
        <div className="scenario-header"><span>ID</span><span>INITIAL STATE</span><span>EXPECTED</span><span /></div>
        {scenarios.map(([id, state, expected]) => (
          <div className="scenario-row" key={id}>
            <code>{id}</code>
            <span>{state}</span>
            <strong className={`expected expected-${expected.toLowerCase()}`}>{expected}</strong>
            <button disabled>not wired</button>
          </div>
        ))}
      </div>
    </main>
  )
}

function LatencyView() {
  return (
    <main className="utility-page">
      <div className="utility-head">
        <div><span className="mono-label">LATENCY LAB</span><h1>Preflight timing</h1></div>
        <p>Numbers remain empty until the real retrieval and decision path is measured end-to-end.</p>
      </div>

      <div className="latency-summary">
        {['p50', 'p95', 'p99', 'max'].map((label) => (
          <div key={label}><span>{label}</span><strong>—</strong><small>no run</small></div>
        ))}
      </div>

      <div className="chart-shell">
        <div className="chart-grid" />
        <span>benchmark data will render here</span>
      </div>
    </main>
  )
}

export default function App() {
  const [page, setPage] = useState<Page>('Mission')
  const [decision, setDecision] = useState<Decision>('BLOCK')
  const fixture = useMemo(() => fixtures[decision], [decision])

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="wordmark">ACTIONPROOF</span>
          <span className="product-note">runtime control for agent actions</span>
        </div>

        <div className="header-meta">
          <span>demo / local</span>
          <span className="health-dot">api pending</span>
        </div>
      </header>

      <div className="control-bar">
        <nav>
          <button className={page === 'Mission' ? 'active' : ''} onClick={() => setPage('Mission')}>Mission</button>
          <button className={page === 'Scenarios' ? 'active' : ''} onClick={() => setPage('Scenarios')}>Scenarios</button>
          <button className={page === 'Latency' ? 'active' : ''} onClick={() => setPage('Latency')}>Latency</button>
        </nav>

        <div className="state-switch">
          <span>preview state</span>
          {(['ALLOW', 'CONFIRM', 'BLOCK'] as Decision[]).map((item) => (
            <button
              key={item}
              className={decision === item ? `selected ${item.toLowerCase()}` : ''}
              onClick={() => setDecision(item)}
            >
              {item.toLowerCase()}
            </button>
          ))}
        </div>
      </div>

      {page === 'Mission' && <MissionView fixture={fixture} />}
      {page === 'Scenarios' && <ScenarioView />}
      {page === 'Latency' && <LatencyView />}
    </div>
  )
}

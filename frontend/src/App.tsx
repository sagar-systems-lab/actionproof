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
  summary: string
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
    summary: 'All required evidence is current and the restart policy is satisfied.',
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
    summary: 'The action may be valid, but required state is incomplete.',
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
    summary: 'The requested action violates the current restart policy.',
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
  return <span className={`status-value ${cls}`}><span className="status-dot" />{value}</span>
}

function DecisionBadge({ decision }: { decision: Decision }) {
  return <span className={`decision-badge badge-${decision.toLowerCase()}`}>{decision}</span>
}

function MissionView({ fixture }: { fixture: Fixture }) {
  return (
    <main className="workspace">
      <section className="page-heading">
        <div>
          <div className="breadcrumb">ActionProof / incidents / INC-104</div>
          <h1>Execution service recovery</h1>
          <p>Review the agent action against current operational state and policy evidence.</p>
        </div>
        <div className="heading-actions">
          <span className="env-chip">demo / local</span>
          <span className="api-chip"><span className="api-dot" />api pending</span>
        </div>
      </section>

      <section className="layout-grid">
        <aside className="context-card card">
          <div className="card-header">
            <div>
              <span className="section-kicker">INCIDENT CONTEXT</span>
              <h2>INC-104</h2>
            </div>
            <span className="severity-chip">DEGRADED</span>
          </div>

          <div className="context-copy">
            <strong>execution-service</strong>
            <p>Agent is attempting a protected restart while service state is degraded.</p>
          </div>

          <div className="state-list">
            <div><span>Connection</span><StatusValue value={fixture.connection} /></div>
            <div><span>Reconciliation</span><StatusValue value={fixture.reconciliation} /></div>
            <div><span>Health</span><StatusValue value={fixture.health} /></div>
          </div>

          <div className="meta-grid">
            <div><span>Actor</span><strong>operations-agent</strong></div>
            <div><span>Resource</span><strong>execution-service</strong></div>
          </div>
        </aside>

        <section className="decision-card card">
          <div className={`decision-accent accent-${fixture.decision.toLowerCase()}`} />
          <div className="decision-top">
            <div>
              <span className="section-kicker">ACTION DECISION</span>
              <h2>{fixture.title}</h2>
              <p>{fixture.summary}</p>
            </div>
            <DecisionBadge decision={fixture.decision} />
          </div>

          <div className="tool-call">
            <span>Proposed tool call</span>
            <code>restart_service()</code>
          </div>

          <div className="decision-sections">
            <div>
              <span className="section-kicker">WHY</span>
              <p>{fixture.reason}</p>
            </div>
            <div className="next-action-box">
              <span className="section-kicker">SAFE NEXT ACTION</span>
              <p>{fixture.next}</p>
            </div>
          </div>

          <div className="metric-strip">
            <div>
              <span>Retrieval</span>
              <strong>—</strong>
              <small>not measured</small>
            </div>
            <div>
              <span>Policy</span>
              <strong>—</strong>
              <small>not measured</small>
            </div>
            <div>
              <span>Total preflight</span>
              <strong>—</strong>
              <small>not measured</small>
            </div>
          </div>

          <div className="decision-footer">
            <code>{fixture.code}</code>
            <span>proof AP-104</span>
          </div>
        </section>

        <aside className="evidence-card card">
          <div className="card-header">
            <div>
              <span className="section-kicker">EVIDENCE</span>
              <h2>3 records</h2>
            </div>
            <span className="fresh-chip">CURRENT</span>
          </div>

          <div className="evidence-list">
            <article>
              <div className="evidence-heading">
                <span className="evidence-type">POLICY</span>
                <code>POL-RESTART-001</code>
              </div>
              <p>Restart requires completed reconciliation.</p>
              <footer><span>authority: system</span><span>v4</span></footer>
            </article>

            <article>
              <div className="evidence-heading">
                <span className="evidence-type">STATE</span>
                <code>INC-104</code>
              </div>
              <p>reconciliation = {fixture.reconciliation}</p>
              <footer><span>source: runtime</span><span>current</span></footer>
            </article>

            <article>
              <div className="evidence-heading">
                <span className="evidence-type">RUNBOOK</span>
                <code>RB-DISCONNECT-004</code>
              </div>
              <p>Reconcile external state before service recovery.</p>
              <footer><span>owner: ops</span><span>v2</span></footer>
            </article>
          </div>
        </aside>

        <section className="event-card card">
          <div className="card-header event-header">
            <div>
              <span className="section-kicker">EVENT TRACE</span>
              <h2>Decision timeline</h2>
            </div>
            <code>trace AP-104</code>
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
      <section className="page-heading compact">
        <div>
          <div className="breadcrumb">ActionProof / scenarios</div>
          <h1>Scenario lab</h1>
          <p>Deterministic incident cases for exercising the same authorization path.</p>
        </div>
      </section>

      <section className="table-card card">
        <div className="scenario-header">
          <span>ID</span><span>INITIAL STATE</span><span>EXPECTED</span><span />
        </div>
        {scenarios.map(([id, state, expected]) => (
          <div className="scenario-row" key={id}>
            <code>{id}</code>
            <span>{state}</span>
            <strong className={`expected expected-${expected.toLowerCase()}`}>{expected}</strong>
            <button disabled title="Scenario runtime is not wired yet">Not wired</button>
          </div>
        ))}
      </section>
    </main>
  )
}

function LatencyView() {
  return (
    <main className="utility-page">
      <section className="page-heading compact">
        <div>
          <div className="breadcrumb">ActionProof / latency</div>
          <h1>Preflight timing</h1>
          <p>Measured retrieval and decision latency will appear here after the real runtime is connected.</p>
        </div>
      </section>

      <section className="latency-card card">
        <div className="latency-summary">
          {['p50', 'p95', 'p99', 'max'].map((label) => (
            <div key={label}><span>{label}</span><strong>—</strong><small>no run</small></div>
          ))}
        </div>
        <div className="chart-shell">
          <div className="chart-grid" />
          <div className="empty-state">
            <strong>No benchmark run yet</strong>
            <span>Real measurements only. No placeholder latency numbers.</span>
          </div>
        </div>
      </section>
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
          <span className="brand-mark">AP</span>
          <div className="brand-copy">
            <strong>ActionProof</strong>
            <span>runtime control for agent actions</span>
          </div>
        </div>

        <div className="header-actions">
          <button type="button" className="header-button">Docs</button>
          <button type="button" className="header-button">Trace</button>
          <span className="header-divider" />
          <span className="header-user">local</span>
        </div>
      </header>

      <div className="nav-shell">
        <nav>
          <button className={page === 'Mission' ? 'active' : ''} onClick={() => setPage('Mission')}>Mission</button>
          <button className={page === 'Scenarios' ? 'active' : ''} onClick={() => setPage('Scenarios')}>Scenarios</button>
          <button className={page === 'Latency' ? 'active' : ''} onClick={() => setPage('Latency')}>Latency</button>
        </nav>

        <div className="state-switch">
          <span>Preview state</span>
          {(['ALLOW', 'CONFIRM', 'BLOCK'] as Decision[]).map((item) => (
            <button
              key={item}
              className={decision === item ? `selected ${item.toLowerCase()}` : ''}
              onClick={() => setDecision(item)}
            >
              {item}
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

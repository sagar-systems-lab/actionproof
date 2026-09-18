import { useMemo, useState } from 'react'

type Decision = 'ALLOW' | 'CONFIRM' | 'BLOCK'
type Page = 'Mission Control' | 'Scenario Lab' | 'Latency Lab'

type Fixture = {
  decision: Decision
  headline: string
  reason: string
  next: string
  connection: string
  reconciliation: string
  health: string
}

const fixtures: Record<Decision, Fixture> = {
  BLOCK: {
    decision: 'BLOCK',
    headline: 'Action blocked',
    reason: 'Restart requires completed reconciliation. Current reconciliation state is INCOMPLETE.',
    next: 'Run reconciliation before restarting the service.',
    connection: 'DISCONNECTED',
    reconciliation: 'INCOMPLETE',
    health: 'DEGRADED',
  },
  CONFIRM: {
    decision: 'CONFIRM',
    headline: 'Confirmation required',
    reason: 'Required operational context is incomplete. ActionProof cannot establish a safe authorization state.',
    next: 'Refresh state or request explicit operator confirmation.',
    connection: 'CONNECTED',
    reconciliation: 'UNKNOWN',
    health: 'DEGRADED',
  },
  ALLOW: {
    decision: 'ALLOW',
    headline: 'Action allowed',
    reason: 'Required context is complete, current, and satisfies the restart policy.',
    next: 'Execute protected restart and verify the observed result postflight.',
    connection: 'CONNECTED',
    reconciliation: 'COMPLETE',
    health: 'HEALTHY',
  },
}

const timeline = [
  ['12:14:01.001', 'Incident created'],
  ['12:14:01.104', 'Agent proposed restart_service'],
  ['12:14:01.106', 'Context requirements resolved'],
  ['12:14:01.112', 'Moss retrieval placeholder — real path in Phase 3'],
  ['12:14:01.114', 'Policy evaluation preview'],
  ['12:14:01.115', 'Proof packet preview rendered'],
]

function MissionControl({ fixture }: { fixture: Fixture }) {
  const decisionCode =
    fixture.decision === 'BLOCK'
      ? 'BLOCK_RECONCILIATION_REQUIRED'
      : fixture.decision === 'ALLOW'
        ? 'ALLOW_SAFE_STATE'
        : 'CONFIRM_CONTEXT_INCOMPLETE'

  return (
    <main className="content-grid">
      <section className={`decision-hero decision-${fixture.decision.toLowerCase()}`}>
        <div className="eyebrow">CURRENT DECISION</div>
        <div className="decision-row">
          <div>
            <h1>{fixture.headline}</h1>
            <p>{fixture.reason}</p>
          </div>
          <span className="decision-pill">{fixture.decision}</span>
        </div>
        <div className="next-action">
          <span>Safe next action</span>
          <strong>{fixture.next}</strong>
        </div>
      </section>

      <section className="panel state-panel">
        <div className="panel-heading">
          <div><span className="eyebrow">LIVE STATE</span><h2>Production incident</h2></div>
          <span className="state-chip">INC-104</span>
        </div>
        <dl className="state-list">
          <div><dt>Connection</dt><dd>{fixture.connection}</dd></div>
          <div><dt>Reconciliation</dt><dd>{fixture.reconciliation}</dd></div>
          <div><dt>Health</dt><dd>{fixture.health}</dd></div>
        </dl>
      </section>

      <section className="panel action-panel">
        <div className="panel-heading">
          <div><span className="eyebrow">AGENT INTENT</span><h2>Protected action</h2></div>
          <span className="risk-chip">HIGH IMPACT</span>
        </div>
        <code className="action-code">restart_service()</code>
        <p className="muted">Actor: operations-agent · Resource: execution-service</p>
      </section>

      <section className="panel proof-panel">
        <div className="panel-heading">
          <div><span className="eyebrow">ACTION PROOF</span><h2>Evidence used for this decision</h2></div>
          <button className="ghost-button" disabled>Proof drawer · Phase 5</button>
        </div>
        <div className="proof-grid">
          <div><span>Policy</span><strong>POL-RESTART-001</strong><small>Authority: system</small></div>
          <div><span>Live state</span><strong>{fixture.reconciliation}</strong><small>Freshness: preview</small></div>
          <div><span>Runbook</span><strong>RB-DISCONNECT-004</strong><small>Recovery sequence</small></div>
          <div><span>Decision code</span><strong>{decisionCode}</strong><small>Deterministic in Phase 2</small></div>
        </div>
      </section>

      <section className="panel latency-panel">
        <div className="panel-heading"><div><span className="eyebrow">LATENCY</span><h2>Preflight budget</h2></div></div>
        <div className="metric-grid">
          <div><span>Moss retrieval</span><strong>Phase 3</strong></div>
          <div><span>Total preflight</span><strong>Phase 3</strong></div>
        </div>
        <p className="muted">No fabricated measurements. Real timing appears only after the real Moss path exists.</p>
      </section>

      <section className="panel timeline-panel">
        <div className="panel-heading">
          <div><span className="eyebrow">INCIDENT TIMELINE</span><h2>Decision path</h2></div>
          <span className="live-dot">PREVIEW</span>
        </div>
        <div className="timeline">
          {timeline.map(([time, event]) => (
            <div className="timeline-row" key={time}>
              <time>{time}</time><span className="timeline-node" /><p>{event}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}

function ScenarioLab() {
  const scenarios = [
    ['Safe Restart', 'Connected · reconciled · healthy', 'ALLOW'],
    ['Unsafe Restart', 'Disconnected · reconciliation incomplete', 'BLOCK'],
    ['Missing Context', 'Required state unavailable', 'CONFIRM'],
    ['Stale Context', 'Required state exceeded freshness TTL', 'BLOCK'],
    ['Successful Recovery', 'Reconcile → verify → retry restart', 'ALLOW'],
  ]
  return (
    <main className="page-stack">
      <div className="page-intro">
        <span className="eyebrow">SCENARIO LAB</span>
        <h1>Five deterministic stories. No demo roulette.</h1>
        <p>Phase 1 renders the product contract. Runtime execution becomes real in Phases 2–4.</p>
      </div>
      <section className="scenario-grid">
        {scenarios.map(([name, state, expected]) => (
          <article className="scenario-card" key={name}>
            <span className="expected">Expected · {expected}</span>
            <h2>{name}</h2><p>{state}</p>
            <button disabled>Run in Phase 4</button>
          </article>
        ))}
      </section>
    </main>
  )
}

function LatencyLab() {
  return (
    <main className="page-stack">
      <div className="page-intro">
        <span className="eyebrow">LATENCY LAB</span>
        <h1>Measure the safety tax. Do not invent it.</h1>
        <p>The benchmark surface exists now; real Moss and total-preflight distributions appear only after the critical path exists.</p>
      </div>
      <section className="panel empty-lab">
        <div className="metric-grid wide">
          <div><span>p50</span><strong>—</strong></div>
          <div><span>p95</span><strong>—</strong></div>
          <div><span>p99</span><strong>—</strong></div>
          <div><span>max</span><strong>—</strong></div>
        </div>
        <div className="empty-chart"><span>Measured distribution will appear here in Phase 6.</span></div>
      </section>
    </main>
  )
}

export default function App() {
  const [page, setPage] = useState<Page>('Mission Control')
  const [decision, setDecision] = useState<Decision>('BLOCK')
  const fixture = useMemo(() => fixtures[decision], [decision])

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">AP</span>
          <div><strong>ActionProof</strong><small>Context proof before consequential action</small></div>
        </div>
        <div className="phase-badge">PHASE 1 · FIXTURE SHELL</div>
      </header>

      <nav className="nav-bar">
        <div className="nav-tabs">
          {(['Mission Control', 'Scenario Lab', 'Latency Lab'] as Page[]).map((item) => (
            <button key={item} className={page === item ? 'active' : ''} onClick={() => setPage(item)}>{item}</button>
          ))}
        </div>
        <div className="preview-controls" aria-label="Preview decision states">
          <span>Preview</span>
          {(['ALLOW', 'CONFIRM', 'BLOCK'] as Decision[]).map((item) => (
            <button key={item} className={`preview-${item.toLowerCase()} ${decision === item ? 'selected' : ''}`} onClick={() => setDecision(item)}>{item}</button>
          ))}
        </div>
      </nav>

      {page === 'Mission Control' && <MissionControl fixture={fixture} />}
      {page === 'Scenario Lab' && <ScenarioLab />}
      {page === 'Latency Lab' && <LatencyLab />}
    </div>
  )
}

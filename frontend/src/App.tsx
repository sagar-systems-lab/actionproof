import { useEffect, useMemo, useState } from 'react'
import ProofDrawer from './components/ProofDrawer'
import { ApiError, getHealth, getRetrievalStatus, listScenarios, runScenario, subscribeRuntimeEvents } from './lib/api'
import LatencyLab from './pages/LatencyLab'
import MissionControl from './pages/MissionControl'
import ScenarioLab from './pages/ScenarioLab'
import type {
  ProductScenarioResult,
  RetrievalStatus,
  RuntimeEvent,
  ScenarioDefinition,
} from './types'

type Page = 'Mission' | 'Scenarios' | 'Latency'

function productError(error: unknown) {
  if (error instanceof ApiError) return error.message
  return 'Required context could not be verified. High-impact action was not authorized.'
}

export default function App() {
  const [page, setPage] = useState<Page>('Mission')
  const [apiOnline, setApiOnline] = useState(false)
  const [retrieval, setRetrieval] = useState<RetrievalStatus | null>(null)
  const [scenarios, setScenarios] = useState<ScenarioDefinition[]>([])
  const [result, setResult] = useState<ProductScenarioResult | null>(null)
  const [events, setEvents] = useState<RuntimeEvent[]>([])
  const [streamLive, setStreamLive] = useState(false)
  const [runningId, setRunningId] = useState<string | null>(null)
  const [runStartedAt, setRunStartedAt] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [proofOpen, setProofOpen] = useState(false)
  const [showingFinal, setShowingFinal] = useState(false)

  useEffect(() => {
    let active = true

    Promise.all([getHealth(), getRetrievalStatus(), listScenarios()])
      .then(([health, retrievalStatus, scenarioList]) => {
        if (!active) return
        setApiOnline(health)
        setRetrieval(retrievalStatus)
        setScenarios(scenarioList)
      })
      .catch(() => {
        if (!active) return
        setApiOnline(false)
      })

    const unsubscribe = subscribeRuntimeEvents(
      (event) => {
        if (!active) return
        setEvents((current) => {
          if (event.event === 'SCENARIO_STARTED') return [event]
          if (current.some((item) => item.sequence === event.sequence)) return current
          return [...current, event].slice(-80)
        })
      },
      (connected) => {
        if (active) setStreamLive(connected)
      },
    )

    return () => {
      active = false
      unsubscribe()
    }
  }, [])

  const activeEvaluation = useMemo(() => {
    if (showingFinal && result?.final_evaluation) return result.final_evaluation
    return result?.primary_evaluation || null
  }, [result, showingFinal])

  async function executeScenario(id: string, navigate = true) {
    setRunningId(id)
    setRunStartedAt(Date.now())
    setError(null)
    setShowingFinal(false)
    setEvents([])

    try {
      const next = await runScenario(id)
      setResult(next)
      setEvents(next.events)
      if (navigate) setPage('Mission')
    } catch (cause) {
      setError(productError(cause))
    } finally {
      setRunningId(null)
      setRunStartedAt(null)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">AP</span>
          <div>
            <strong>ActionProof</strong>
            <span>proof before protected action</span>
          </div>
        </div>

        <div className="header-runtime">
          <span className={apiOnline ? 'runtime-indicator online' : 'runtime-indicator'}>
            <span />
            API {apiOnline ? 'online' : 'offline'}
          </span>
          <span className={retrieval?.configured ? 'runtime-indicator online' : 'runtime-indicator'}>
            <span />
            Moss {retrieval?.configured ? 'configured' : 'waiting'}
          </span>
        </div>
      </header>

      <div className="nav-shell">
        <nav>
          {(['Mission', 'Scenarios', 'Latency'] as Page[]).map((item) => (
            <button
              key={item}
              className={page === item ? 'active' : ''}
              onClick={() => setPage(item)}
            >
              {item}
            </button>
          ))}
        </nav>
        <div className="nav-context">
          <span>{result ? result.label : 'No scenario run'}</span>
          {result && <code>{result.incident_id}</code>}
        </div>
      </div>

      {error && (
        <div className="error-banner" role="alert">
          <div>
            <strong>Action not authorized</strong>
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {page === 'Mission' && (
        <MissionControl
          result={result}
          events={events}
          apiOnline={apiOnline}
          mossConfigured={Boolean(retrieval?.configured)}
          streamLive={streamLive}
          loading={runningId !== null}
          showingFinal={showingFinal}
          onToggleFinal={() => setShowingFinal((value) => !value)}
          onViewProof={() => setProofOpen(true)}
          onRunHero={() => executeScenario('successful-recovery')}
        />
      )}

      {page === 'Scenarios' && (
        <ScenarioLab
          scenarios={scenarios}
          result={result}
          runningId={runningId}
          runStartedAt={runStartedAt}
          events={events}
          apiOnline={apiOnline}
          onRun={(id) => executeScenario(id)}
        />
      )}

      {page === 'Latency' && (
        <LatencyLab result={result} showingFinal={showingFinal} />
      )}

      <ProofDrawer
        evaluation={activeEvaluation}
        open={proofOpen}
        onClose={() => setProofOpen(false)}
      />
    </div>
  )
}

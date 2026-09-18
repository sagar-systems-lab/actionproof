import type {
  ProductScenarioResult,
  ScenarioDefinition,
} from '../types'

type Props = {
  scenarios: ScenarioDefinition[]
  result: ProductScenarioResult | null
  runningId: string | null
  apiOnline: boolean
  onRun: (id: string) => void
}

function expectedTone(expected: string) {
  if (expected.includes('ALLOW') && !expected.includes('BLOCK')) return 'allow'
  if (expected.includes('CONFIRM')) return 'confirm'
  if (expected.includes('BLOCK')) return 'block'
  return 'neutral'
}

export default function ScenarioLab({
  scenarios,
  result,
  runningId,
  apiOnline,
  onRun,
}: Props) {
  return (
    <main className="workspace utility-view">
      <section className="page-heading">
        <div>
          <div className="breadcrumb">ActionProof / Scenario Lab</div>
          <h1>Five deterministic cases. One protected runtime.</h1>
          <p>
            Every run uses the same Moss retrieval, policy, proof, and runtime path shown in Mission Control.
          </p>
        </div>
      </section>

      <section className="card scenario-table">
        <div className="scenario-table-head">
          <span>Scenario</span>
          <span>What it proves</span>
          <span>Expected</span>
          <span />
        </div>
        {scenarios.map((scenario) => {
          const isRunning = runningId === scenario.id
          const wasLast = result?.scenario_id === scenario.id
          return (
            <article className={wasLast ? 'scenario-line last-run' : 'scenario-line'} key={scenario.id}>
              <div>
                <strong>{scenario.label}</strong>
                <code>{scenario.id}</code>
              </div>
              <p>{scenario.description}</p>
              <span className={`expected-chip ${expectedTone(scenario.expected)}`}>{scenario.expected}</span>
              <button
                className="button secondary"
                onClick={() => onRun(scenario.id)}
                disabled={Boolean(runningId) || !apiOnline}
              >
                {isRunning ? 'Running…' : 'Run live'}
              </button>
            </article>
          )
        })}
      </section>

      <section className="scenario-note">
        <strong>No fixture decisions.</strong>
        <span>
          Scenario controls mutate or omit actual runtime context, then ask ActionProof to retrieve and decide.
        </span>
      </section>
    </main>
  )
}

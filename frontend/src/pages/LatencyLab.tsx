import { useState } from 'react'
import type {
  BenchmarkRun,
  BenchmarkScenario,
  EvaluationResult,
  ProductScenarioResult,
} from '../types'
import { runBenchmark } from '../lib/api'
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

function formatNs(value: number) {
  if (value < 1_000) return value.toLocaleString() + ' ns'
  if (value < 1_000_000) return (value / 1_000).toFixed(1) + ' µs'
  return (value / 1_000_000).toFixed(value < 10_000_000 ? 2 : 1) + ' ms'
}

function row(label: string, metric: BenchmarkRun['metrics']['moss_retrieval']) {
  return (
    <div className="benchmark-row" key={label}>
      <strong>{label}</strong>
      <span>{formatNs(metric.p50_ns)}</span>
      <span>{formatNs(metric.p95_ns)}</span>
      <span>{formatNs(metric.p99_ns)}</span>
      <span>{formatNs(metric.max_ns)}</span>
    </div>
  )
}

export default function LatencyLab({ result, showingFinal }: Props) {
  const evaluation = showingFinal && result?.final_evaluation
    ? result.final_evaluation
    : result?.primary_evaluation || null

  const [iterations, setIterations] = useState<100 | 500 | 1000>(100)
  const [scenario, setScenario] = useState<BenchmarkScenario>('mixed')
  const [benchmark, setBenchmark] = useState<BenchmarkRun | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setRunning(true)
    setError(null)
    try {
      setBenchmark(await runBenchmark(iterations, scenario))
    } catch {
      setError('Benchmark could not complete cleanly. Check runtime health and try again.')
    } finally {
      setRunning(false)
    }
  }

  return (
    <main className="workspace utility-view">
      <section className="page-heading">
        <div>
          <div className="breadcrumb">ActionProof / Latency Lab</div>
          <h1>Measured preflight performance</h1>
          <p>
            Run the real ActionProof decision path and inspect observed latency distributions. Setup writes are excluded from timed samples.
          </p>
        </div>
      </section>

      <section className="latency-lab-grid">
        <div className="card latest-run-card">
          <div className="card-header">
            <div>
              <span className="section-kicker">LATEST ACTION</span>
              <h2>{result?.label || 'No scenario run yet'}</h2>
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

        <div className="card benchmark-panel">
          <div className="benchmark-panel-head">
            <div>
              <span className="section-kicker">DISTRIBUTION BENCHMARK</span>
              <h2>Repeatable latency run</h2>
              <p>Nearest-rank p50 / p95 / p99 / max from the real preflight engine.</p>
            </div>
            <button className="button primary" onClick={run} disabled={running}>
              {running ? 'Benchmark running…' : 'Run benchmark'}
            </button>
          </div>

          <div className="benchmark-controls">
            <div>
              <span>Workload</span>
              {(['safe', 'unsafe', 'mixed'] as BenchmarkScenario[]).map((value) => (
                <button
                  key={value}
                  className={scenario === value ? 'selected' : ''}
                  onClick={() => setScenario(value)}
                  disabled={running}
                >
                  {value}
                </button>
              ))}
            </div>
            <div>
              <span>Iterations</span>
              {([100, 500, 1000] as const).map((value) => (
                <button
                  key={value}
                  className={iterations === value ? 'selected' : ''}
                  onClick={() => setIterations(value)}
                  disabled={running}
                >
                  {value}
                </button>
              ))}
            </div>
          </div>

          {error && <div className="benchmark-error">{error}</div>}

          {benchmark ? (
            <>
              <div className="benchmark-table">
                <div className="benchmark-row header">
                  <strong>Metric</strong>
                  <span>p50</span>
                  <span>p95</span>
                  <span>p99</span>
                  <span>max</span>
                </div>
                {row('Moss retrieval', benchmark.metrics.moss_retrieval)}
                {row('Policy evaluation', benchmark.metrics.policy_eval)}
                {row('Proof build', benchmark.metrics.proof_build)}
                {row('Total preflight', benchmark.metrics.total_preflight)}
              </div>
              <div className="benchmark-meta">
                <span>{benchmark.iterations} measured</span>
                <span>{benchmark.warmup} warmup</span>
                <span>{benchmark.scenario} workload</span>
                <span>{(benchmark.error_rate * 100).toFixed(2)}% errors</span>
                <code>{benchmark.revision.slice(0, 12)}</code>
              </div>
            </>
          ) : (
            <div className="benchmark-empty">
              <strong>No distribution measured yet</strong>
              <span>Start with 100 mixed runs. Larger runs are available after the first baseline.</span>
            </div>
          )}

          <small className="benchmark-integrity">
            ActionProof measurements only. No sponsor benchmark numbers are copied into this view.
          </small>
        </div>
      </section>
    </main>
  )
}

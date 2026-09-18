import type { RuntimeEvent } from '../types'

type Props = {
  events: RuntimeEvent[]
  live: boolean
}

const labels: Record<string, string> = {
  SCENARIO_STARTED: 'Scenario',
  INCIDENT_CREATED: 'Incident',
  AGENT_INTENT_CREATED: 'Agent intent',
  ACTION_NORMALIZED: 'Action normalized',
  MOSS_QUERY_STARTED: 'Moss retrieval',
  MOSS_QUERY_COMPLETED: 'Moss context',
  CONTEXT_VALIDATED: 'Context validated',
  POLICY_EVALUATED: 'Decision',
  PROOF_CREATED: 'Proof',
  ACTION_ALLOWED: 'Allowed',
  ACTION_BLOCKED: 'Blocked',
  ACTION_EXECUTED: 'Action',
  POSTFLIGHT_VERIFIED: 'Postflight',
  POSTFLIGHT_FAILED: 'Postflight failed',
}

function eventTone(event: string) {
  if (event === 'ACTION_BLOCKED' || event === 'POSTFLIGHT_FAILED') return 'bad'
  if (event === 'ACTION_ALLOWED' || event === 'POSTFLIGHT_VERIFIED') return 'good'
  if (event.includes('MOSS') || event === 'CONTEXT_VALIDATED') return 'moss'
  return 'neutral'
}

function formatTime(timestamp: string) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
    hour12: false,
  })
}

export default function IncidentTimeline({ events, live }: Props) {
  return (
    <section className="card timeline-card">
      <div className="card-header">
        <div>
          <span className="section-kicker">TIMELINE</span>
          <h2>Incident progression</h2>
        </div>
        <span className={live ? 'stream-chip live' : 'stream-chip'}>
          <span className="stream-dot" />
          {live ? 'live stream' : 'stream reconnecting'}
        </span>
      </div>

      {events.length ? (
        <div className="timeline-list">
          {events.map((event) => (
            <article className="timeline-item" key={event.sequence}>
              <div className={`timeline-marker ${eventTone(event.event)}`} />
              <time>{formatTime(event.timestamp)}</time>
              <div>
                <strong>{labels[event.event] || event.event}</strong>
                <p>{event.summary}</p>
              </div>
              <code>#{event.sequence}</code>
            </article>
          ))}
        </div>
      ) : (
        <div className="panel-empty timeline-empty">
          <strong>No runtime events yet</strong>
          <span>Start a scenario and this timeline will advance from incident to postflight.</span>
        </div>
      )}
    </section>
  )
}

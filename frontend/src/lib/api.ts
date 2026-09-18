import type {
  ProductScenarioResult,
  RetrievalStatus,
  RuntimeEvent,
  ScenarioDefinition,
} from '../types'

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

const EVENT_NAMES = [
  'SCENARIO_STARTED',
  'INCIDENT_CREATED',
  'AGENT_INTENT_CREATED',
  'ACTION_NORMALIZED',
  'MOSS_QUERY_STARTED',
  'MOSS_QUERY_COMPLETED',
  'CONTEXT_VALIDATED',
  'POLICY_EVALUATED',
  'PROOF_CREATED',
  'ACTION_ALLOWED',
  'ACTION_BLOCKED',
  'ACTION_EXECUTED',
  'POSTFLIGHT_VERIFIED',
  'POSTFLIGHT_FAILED',
] as const

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
  })

  if (!response.ok) {
    let message = 'ActionProof could not complete the request.'
    try {
      const body = await response.json() as { detail?: string }
      if (body.detail) message = body.detail
    } catch {
      // Keep product-language fallback when the response is not JSON.
    }
    throw new ApiError(message, response.status)
  }

  return response.json() as Promise<T>
}

export async function getHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/api/health`)
    return response.ok
  } catch {
    return false
  }
}

export function getRetrievalStatus(): Promise<RetrievalStatus> {
  return requestJson('/api/retrieval/status')
}

export function listScenarios(): Promise<ScenarioDefinition[]> {
  return requestJson('/api/runtime/scenarios')
}

export function runScenario(id: string): Promise<ProductScenarioResult> {
  return requestJson(`/api/runtime/scenarios/${encodeURIComponent(id)}`, {
    method: 'POST',
  })
}

export function subscribeRuntimeEvents(
  onEvent: (event: RuntimeEvent) => void,
  onConnection: (connected: boolean) => void,
): () => void {
  const source = new EventSource(`${API_URL}/api/runtime/events/stream`)

  const handlers = EVENT_NAMES.map((name) => {
    const handler = (raw: Event) => {
      const event = raw as MessageEvent<string>
      try {
        onEvent(JSON.parse(event.data) as RuntimeEvent)
      } catch {
        // Ignore malformed event payloads instead of surfacing raw parser errors.
      }
    }
    source.addEventListener(name, handler)
    return [name, handler] as const
  })

  source.onopen = () => onConnection(true)
  source.onerror = () => onConnection(false)

  return () => {
    handlers.forEach(([name, handler]) => {
      source.removeEventListener(name, handler)
    })
    source.close()
  }
}

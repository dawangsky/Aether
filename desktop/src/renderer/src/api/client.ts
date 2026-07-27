export type GameKey = 'ssq' | 'dlt'

let baseUrl = 'http://127.0.0.1:8765'

export function setApiBaseUrl(url: string) {
  baseUrl = url.replace(/\/$/, '')
}

export function getApiBaseUrl() {
  return baseUrl
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers || {})
      }
    })
  } catch {
    throw new Error('无法连接本地 API（Failed to fetch）。请确认右上角状态为 LIVE，或重启应用等待依赖安装完成。')
  }
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || JSON.stringify(body)
    } catch {
      // ignore
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string; version: string }>('/health'),
  draws: (game: GameKey, limit = 20) =>
    request<{ game: GameKey; total: number; items: Array<any> }>(
      `/draws?game=${game}&limit=${limit}`
    ),
  update: (game: GameKey | 'all' = 'all') =>
    request<{ results: Array<{ game: string; total: number; added: number }> }>('/update', {
      method: 'POST',
      body: JSON.stringify({ game, limit: 120 })
    }),
  analyze: (game: GameKey, window = 50) =>
    request<any>(`/analyze?game=${game}&window=${window}`),
  predict: (body: { game: GameKey; n: number; window?: number; seed?: number | null }) =>
    request<any>('/predict', { method: 'POST', body: JSON.stringify(body) }),
  backtest: (body: {
    game: GameKey
    window: number
    n: number
    periods: number
    seed?: number
  }) => request<any>('/backtest', { method: 'POST', body: JSON.stringify(body) }),
  check: (body: { game: GameKey; issue: string; main: number[]; special: number[] }) =>
    request<any>('/check', { method: 'POST', body: JSON.stringify(body) }),
  ticketPlan: (body: {
    game: GameKey
    mode: 'single' | 'compound'
    main_count?: number | null
    special_count?: number | null
    window?: number
  }) => request<any>('/ticket/plan', { method: 'POST', body: JSON.stringify(body) }),
  ticketQuote: (body: { game: GameKey; main: number[]; special: number[] }) =>
    request<any>('/ticket/quote', { method: 'POST', body: JSON.stringify(body) })
}

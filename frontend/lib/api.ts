/**
 * API client for Hindsight Economics backend
 */

// Production API URL - ALWAYS use HTTPS
const PROD_API = 'https://hindsight-production-38c1.up.railway.app/api'
const DEV_API = 'http://localhost:8000/api'

// Get API URL - checks window.location at runtime
function getApiUrl(): string {
  // Server-side rendering - use production URL
  if (typeof window === 'undefined') {
    return PROD_API
  }
  
  // Client-side - check actual hostname
  const hostname = window.location.hostname
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return DEV_API
  }
  
  // Any other hostname (production) - use HTTPS
  return PROD_API
}

// Getter that returns fresh URL each time
function getAPI(): string {
  return getApiUrl()
}

// Types
export interface ScenarioBase {
  id: number
  display_label: string | null
}

export interface MonthlyData {
  month_index: number
  is_forward: boolean
  idx_stocks: number
  idx_bonds: number
  idx_cash: number
  idx_gold: number
  gdp_growth_yoy: number | null
  unemployment_rate: number | null
  inflation_rate_yoy: number | null
  fed_funds_rate: number | null
  industrial_prod_yoy: number | null
}

export interface ScenarioHistory {
  scenario_id: number
  display_label: string | null
  monthly_data: MonthlyData[]
}

export interface Predictions {
  above_15pct: number
  above_10pct: number
  above_5pct: number
  above_0pct: number
}

export interface Allocation {
  stocks: number
  bonds: number
  cash: number
  gold: number
}

export interface GameCreateInput {
  scenario_id: number
  predictions: Predictions
  allocation: Allocation
  rationale: string
}

export interface GameSession {
  session_token: string
  scenario_id: number
  created_at: string
}

export interface PredictionResult {
  threshold: string
  user_prediction: string
  user_confidence: number
  actual_outcome: boolean
  correct: boolean
  brier_contribution: number
}

export interface GameReveal {
  session_token: string
  actual_start_date: string
  actual_period: string
  historical_context: string | null
  historical_description: string | null
  monthly_data: MonthlyData[]
  prediction_results: PredictionResult[]
  brier_score: number
  allocation: Allocation
  asset_returns: Record<string, number>
  portfolio_return: number
  portfolio_sharpe: number
  optimal_allocation: Allocation
  optimal_return: number
  optimal_sharpe: number
  benchmark_return: number
  benchmark_sharpe: number
  excess_return: number
  excess_sharpe: number
  rationale: string | null
}

export interface LeaderboardEntry {
  rank: number
  username: string
  games_played: number
  avg_brier_score: number
  avg_sharpe: number
  avg_excess_return: number
}

export interface Leaderboard {
  entries: LeaderboardEntry[]
  user_rank: number | null
  user_stats: LeaderboardEntry | null
}

export interface User {
  id: number
  email: string
  username: string | null
  games_played: number
  wins_vs_benchmark: number
  losses_vs_benchmark: number
}

// API functions
async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    credentials: 'include', // Include cookies for auth
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

export const api = {
  // Get a random scenario for a new game
  async getRandomScenario(): Promise<ScenarioBase> {
    return fetchJSON<ScenarioBase>(`${getAPI()}/scenarios/random`)
  },
  
  // Get historical data for a scenario (24 months, no dates)
  async getScenarioHistory(scenarioId: number): Promise<ScenarioHistory> {
    return fetchJSON<ScenarioHistory>(`${getAPI()}/scenarios/${scenarioId}/history`)
  },
  
  // Create a new game session with predictions
  async createGame(input: GameCreateInput): Promise<GameSession> {
    return fetchJSON<GameSession>(`${getAPI()}/games/`, {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },
  
  // Get game reveal with results and scores
  async getGameReveal(sessionToken: string): Promise<GameReveal> {
    return fetchJSON<GameReveal>(`${getAPI()}/games/${sessionToken}/reveal`)
  },
  
  // Join leaderboard with username
  async joinLeaderboard(sessionToken: string, username: string): Promise<void> {
    await fetchJSON(`${getAPI()}/games/${sessionToken}/leaderboard`, {
      method: 'POST',
      body: JSON.stringify({ username }),
    })
  },
  
  // Get leaderboard
  async getLeaderboard(limit: number = 50): Promise<Leaderboard> {
    return fetchJSON<Leaderboard>(`${getAPI()}/leaderboard?limit=${limit}`)
  },
  
  // Add reflection after reveal
  async addReflection(sessionToken: string, reflection: string): Promise<void> {
    await fetchJSON(`${getAPI()}/games/${sessionToken}/reflection`, {
      method: 'POST',
      body: JSON.stringify({ reflection }),
    })
  },
  
  // Auth - Request magic link
  async requestMagicLink(email: string): Promise<{ message: string }> {
    return fetchJSON(`${getAPI()}/auth/magic-link`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  },
  
  // Auth - Get current user
  async getCurrentUser(): Promise<User | null> {
    try {
      return await fetchJSON<User>(`${getAPI()}/auth/me`)
    } catch {
      return null
    }
  },
  
  // Auth - Set username
  async setUsername(username: string): Promise<User> {
    return fetchJSON<User>(`${getAPI()}/auth/username`, {
      method: 'POST',
      body: JSON.stringify({ username }),
    })
  },
  
  // Auth - Logout
  async logout(): Promise<void> {
    await fetchJSON(`${getAPI()}/auth/logout`, {
      method: 'POST',
    })
  },
  
  // Auth - Link game to user
  async linkGameToUser(gameToken: string): Promise<void> {
    await fetchJSON(`${getAPI()}/auth/link-game/${gameToken}`, {
      method: 'POST',
    })
  },
}



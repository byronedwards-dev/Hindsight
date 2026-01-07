'use client'

import { useState, useEffect } from 'react'
import { AssetChart } from '@/components/AssetChart'
import { MacroIndicators } from '@/components/MacroIndicators'
import { PredictionForm } from '@/components/PredictionForm'
import { AllocationSliders } from '@/components/AllocationSliders'
import { RationaleInput } from '@/components/RationaleInput'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { api, ScenarioHistory, GameCreateInput } from '@/lib/api'

type GameState = 'loading' | 'playing' | 'submitting' | 'reveal'

export default function Home() {
  const [gameState, setGameState] = useState<GameState>('loading')
  const [scenario, setScenario] = useState<ScenarioHistory | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [hardMode, setHardMode] = useState(false)
  
  // Prediction state
  const [predictions, setPredictions] = useState({
    above_15pct: 0.3,
    above_10pct: 0.4,
    above_5pct: 0.6,
    above_0pct: 0.75,
  })
  
  // Allocation state
  const [allocation, setAllocation] = useState({
    stocks: 60,
    bonds: 30,
    cash: 5,
    gold: 5,
  })
  
  // Rationale state
  const [rationale, setRationale] = useState('')

  // Load a random scenario on mount
  useEffect(() => {
    loadNewScenario()
  }, [])

  async function loadNewScenario() {
    setGameState('loading')
    setError(null)
    
    try {
      // Get a random scenario
      const randomScenario = await api.getRandomScenario()
      
      // Load the historical data
      const history = await api.getScenarioHistory(randomScenario.id)
      setScenario(history)
      setGameState('playing')
    } catch (err) {
      console.error('Failed to load scenario:', err)
      setError('Failed to load game data. Please check that the backend is running.')
      setGameState('loading')
    }
  }

  async function handleSubmit() {
    if (!scenario) return
    
    // Validate rationale (optional, but max 500 chars)
    if (rationale.length > 500) {
      setError('Rationale must be 500 characters or less.')
      return
    }
    
    // Validate allocation sums to 100
    const total = allocation.stocks + allocation.bonds + allocation.cash + allocation.gold
    if (total !== 100) {
      setError(`Allocations must sum to 100%. Currently: ${total}%`)
      return
    }
    
    setGameState('submitting')
    setError(null)
    
    try {
      const input: GameCreateInput = {
        scenario_id: scenario.scenario_id,
        predictions,
        allocation,
        rationale,
      }
      
      const session = await api.createGame(input)
      
      // Redirect to reveal page
      window.location.href = `/reveal/${session.session_token}`
    } catch (err: any) {
      console.error('Failed to submit game:', err)
      setError(err.message || 'Failed to submit predictions. Please try again.')
      setGameState('playing')
    }
  }

  if (gameState === 'loading') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-terminal-muted">Loading scenario...</p>
          {error && (
            <div className="mt-4 p-4 bg-loss/10 border border-loss/30 rounded-lg text-loss max-w-md">
              {error}
            </div>
          )}
        </div>
      </div>
    )
  }

  if (!scenario) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center max-w-md">
          <p className="text-terminal-muted">No scenario data available.</p>
          <button 
            onClick={loadNewScenario}
            className="mt-4 px-4 py-2 bg-stocks text-white rounded-lg hover:bg-stocks/80 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Game Introduction */}
      <div className="mb-8 text-center">
        <p className="text-terminal-text text-lg leading-relaxed max-w-3xl mx-auto">
          You're shown <span className="text-stocks font-medium">24 months of real economic data</span> from the past 50 years. 
          Your mission: predict what happens in the <span className="text-stocks font-medium">next 12 months</span> and allocate your portfolio accordingly.
        </p>
      </div>

      {/* Difficulty Toggle */}
      <div className="flex items-center justify-end mb-6 gap-4">
        <button
          onClick={() => setHardMode(!hardMode)}
          className={`flex items-center gap-3 px-4 py-2 rounded-lg border transition-all ${
            hardMode 
              ? 'bg-loss/20 border-loss/50 text-loss' 
              : 'bg-terminal-bg border-terminal-border text-terminal-muted hover:border-terminal-text'
          }`}
        >
          <span className="text-sm font-medium">
            {hardMode ? '🔥 Hard Mode' : 'Normal Mode'}
          </span>
          <div className={`relative w-10 h-5 rounded-full transition-colors ${
            hardMode ? 'bg-loss' : 'bg-terminal-border'
          }`}>
            <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
              hardMode ? 'translate-x-5' : 'translate-x-0.5'
            }`} />
          </div>
        </button>
      </div>

      {/* Hard Mode Explanation */}
      {hardMode && (
        <div className="mb-6 p-4 bg-loss/10 border border-loss/30 rounded-lg">
          <p className="text-sm text-loss font-medium">
            🔥 Hard Mode Active — Economic indicators are indexed to 100, hiding absolute values that could reveal the time period.
          </p>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="mb-6 p-4 bg-loss/10 border border-loss/30 rounded-lg text-loss">
          {error}
        </div>
      )}

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Historical Data */}
        <div className="lg:col-span-2 space-y-6">
          {/* Section Header - Historical */}
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-terminal-muted"></div>
            <h2 className="text-xl font-semibold text-terminal-text">Historical Data</h2>
            <div className="flex-1 h-px bg-terminal-border"></div>
            <span className="text-sm font-mono text-terminal-muted px-3 py-1 bg-terminal-bg rounded-full border border-terminal-border">
              24 months
            </span>
          </div>

          {/* Asset prices chart */}
          <div className="bg-terminal-card border border-terminal-border rounded-xl p-6">
            <h3 className="text-lg font-medium mb-4">Asset Prices (Indexed to 100)</h3>
            <AssetChart data={scenario.monthly_data} />
          </div>

          {/* Macro indicators */}
          <div className="bg-terminal-card border border-terminal-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">
                Economic Indicators
                {hardMode && <span className="ml-2 text-sm text-loss">(Indexed)</span>}
              </h3>
            </div>
            <MacroIndicators data={scenario.monthly_data} hardMode={hardMode} />
          </div>
        </div>

        {/* Right column: Predictions */}
        <div className="space-y-6">
          {/* Section Header - Predictions */}
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-stocks animate-pulse"></div>
            <h2 className="text-xl font-semibold text-stocks">Your Predictions</h2>
            <div className="flex-1 h-px bg-stocks/30"></div>
            <span className="text-sm font-mono text-stocks px-3 py-1 bg-stocks/10 rounded-full border border-stocks/30">
              Next 12 months
            </span>
          </div>

          {/* Market predictions */}
          <div className="bg-terminal-card border-2 border-stocks/30 rounded-xl p-6">
            <h3 className="text-lg font-medium mb-2 text-terminal-text">Market Predictions</h3>
            <p className="text-sm text-terminal-muted mb-4">
              Will real S&P 500 returns exceed these thresholds?
            </p>
            <PredictionForm 
              predictions={predictions}
              onChange={setPredictions}
            />
          </div>

          {/* Asset allocation */}
          <div className="bg-terminal-card border-2 border-stocks/30 rounded-xl p-6">
            <h3 className="text-lg font-medium mb-2 text-terminal-text">Asset Allocation</h3>
            <p className="text-sm text-terminal-muted mb-4">
              How would you invest $100,000?
            </p>
            <AllocationSliders
              allocation={allocation}
              onChange={setAllocation}
            />
          </div>

          {/* Rationale */}
          <div className="bg-terminal-card border-2 border-stocks/30 rounded-xl p-6">
            <h3 className="text-lg font-medium mb-4 text-terminal-text">Your Rationale</h3>
            <RationaleInput
              value={rationale}
              onChange={setRationale}
            />
          </div>

          {/* Submit button */}
          <button
            onClick={handleSubmit}
            disabled={gameState === 'submitting'}
            className="w-full py-4 bg-stocks text-white font-semibold rounded-xl 
                     hover:bg-stocks/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                     shadow-lg shadow-stocks/20"
          >
            {gameState === 'submitting' ? 'Submitting...' : 'Submit Predictions →'}
          </button>
        </div>
      </div>
    </div>
  )
}

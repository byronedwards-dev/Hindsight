'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { api, GameReveal } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { AssetChart } from '@/components/AssetChart'
import { MacroIndicators } from '@/components/MacroIndicators'

export default function RevealPage() {
  const params = useParams()
  const router = useRouter()
  const token = params.token as string
  const { user, loading: authLoading } = useAuth()
  
  const [reveal, setReveal] = useState<GameReveal | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [username, setUsername] = useState('')
  const [joinedLeaderboard, setJoinedLeaderboard] = useState(false)
  const [gameLinkStatus, setGameLinkStatus] = useState<'idle' | 'linking' | 'linked'>('idle')

  useEffect(() => {
    if (token) {
      loadReveal()
    }
  }, [token])

  async function loadReveal() {
    try {
      const data = await api.getGameReveal(token)
      setReveal(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load results')
    } finally {
      setLoading(false)
    }
  }

  async function handleJoinLeaderboard() {
    // Use existing username from user account or the input field
    const usernameToUse = user?.username || username
    
    if (!usernameToUse || usernameToUse.length < 3) {
      setError('Username must be at least 3 characters')
      return
    }
    
    try {
      // If user is logged in but doesn't have a username, set it first
      if (user && !user.username && username) {
        await api.setUsername(username)
      }
      
      // Link game to user if logged in
      if (user) {
        try {
          await api.linkGameToUser(token)
        } catch {
          // Game might already be linked
        }
      }
      
      await api.joinLeaderboard(token, usernameToUse)
      setJoinedLeaderboard(true)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to join leaderboard')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-terminal-muted">Loading results...</p>
        </div>
      </div>
    )
  }

  if (error && !reveal) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center max-w-md">
          <p className="text-loss">{error}</p>
          <a 
            href="/"
            className="mt-4 inline-block px-4 py-2 bg-stocks text-white rounded-lg hover:bg-stocks/80 transition-colors"
          >
            Play Again
          </a>
        </div>
      </div>
    )
  }

  if (!reveal) return null

  const beatBenchmark = reveal.excess_return > 0

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Header with period reveal */}
      <div className="text-center mb-8 animate-fade-in">
        <h2 className="text-3xl font-bold mb-2 text-white">The Reveal</h2>
        <p className="text-xl text-stocks font-mono">{reveal.actual_period}</p>
        {reveal.historical_context && (
          <p className="text-lg text-white mt-2 font-medium">{reveal.historical_context}</p>
        )}
      </div>

      {/* Historical Description */}
      {reveal.historical_description && (
        <div className="bg-terminal-card border border-stocks/30 rounded-xl p-6 mb-6 animate-slide-up">
          <h3 className="text-lg font-semibold mb-3 text-stocks">What Happened Next</h3>
          <p className="text-terminal-text leading-relaxed">
            {reveal.historical_description}
          </p>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="mb-6 p-4 bg-loss/10 border border-loss/30 rounded-lg text-loss">
          {error}
        </div>
      )}

      {/* Main content grid - matching play page layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Charts (same as play page) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Section Header */}
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-gain"></div>
            <h2 className="text-xl font-semibold text-white">Full Period Data</h2>
            <div className="flex-1 h-px bg-terminal-border"></div>
            <span className="text-sm font-mono text-gain px-3 py-1 bg-gain/10 rounded-full border border-gain/30">
              36 months
            </span>
          </div>

          {/* Asset Prices with Forward Period */}
          <div className="bg-terminal-card border border-terminal-border rounded-xl p-6 animate-slide-up">
            <h3 className="text-lg font-medium mb-2 text-white">Asset Prices (Indexed to 100)</h3>
            <p className="text-sm text-terminal-text mb-4">
              The dashed line shows where you made your prediction. Green area shows the forward period.
            </p>
            <AssetChart 
              data={reveal.monthly_data} 
              showForward={true}
              showPredictionLine={true}
              startDate={reveal.actual_start_date}
            />
          </div>

          {/* Economic Indicators with Forward Period */}
          <div className="bg-terminal-card border border-terminal-border rounded-xl p-6 animate-slide-up animate-delay-100">
            <h3 className="text-lg font-medium mb-4 text-white">Economic Indicators</h3>
            <MacroIndicators 
              data={reveal.monthly_data} 
              showForward={true}
              showPredictionLine={true}
              startDate={reveal.actual_start_date}
            />
          </div>
        </div>

        {/* Right column: Results (same position as prediction inputs) */}
        <div className="space-y-6">
          {/* Section Header */}
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-stocks"></div>
            <h2 className="text-xl font-semibold text-stocks">Your Results</h2>
            <div className="flex-1 h-px bg-stocks/30"></div>
          </div>

          {/* Market Predictions Results */}
          <div className="bg-terminal-card border-2 border-stocks/30 rounded-xl p-6 animate-slide-up animate-delay-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-white">Market Predictions</h3>
              <div className="text-right">
                <span className="text-sm text-terminal-text">Brier Score</span>
                <p className="font-mono text-xl font-semibold text-white">
                  {reveal.brier_score.toFixed(4)}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              {reveal.prediction_results.map((result, i) => (
                <div 
                  key={i}
                  className="flex items-center justify-between py-2 border-b border-terminal-border last:border-0"
                >
                  <span className="font-mono text-sm text-white">{result.threshold}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-terminal-text">
                      You: {result.user_prediction} ({(result.user_confidence * 100).toFixed(0)}%)
                    </span>
                    <span className={`text-sm font-medium ${result.correct ? 'text-gain' : 'text-loss'}`}>
                      {result.correct ? '✓' : '✗'} Actual: {result.actual_outcome ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-terminal-border text-sm text-terminal-text">
              {reveal.brier_score < 0.10 ? '🎯 Excellent calibration!' :
               reveal.brier_score < 0.15 ? '✓ Good calibration' :
               reveal.brier_score < 0.20 ? 'Decent calibration' :
               reveal.brier_score < 0.25 ? 'Near random guessing' :
               'Worse than random'} (Lower is better)
            </div>
          </div>

          {/* Asset Allocation Results */}
          <div className="bg-terminal-card border-2 border-stocks/30 rounded-xl p-6 animate-slide-up animate-delay-300">
            <h3 className="text-lg font-medium mb-4 text-white">Asset Allocation Results</h3>

            {/* Your Portfolio */}
            <div className="mb-4">
              <h4 className="text-sm text-terminal-text mb-2">Your Portfolio</h4>
              <div className="space-y-1 text-sm font-mono">
                <div className="flex justify-between">
                  <span className="text-white">Stocks ({reveal.allocation.stocks}%)</span>
                  <span className={reveal.asset_returns.stocks >= 0 ? 'text-gain' : 'text-loss'}>
                    {(reveal.asset_returns.stocks * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white">Bonds ({reveal.allocation.bonds}%)</span>
                  <span className={reveal.asset_returns.bonds >= 0 ? 'text-gain' : 'text-loss'}>
                    {(reveal.asset_returns.bonds * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white">Gold ({reveal.allocation.gold}%)</span>
                  <span className={reveal.asset_returns.gold >= 0 ? 'text-gain' : 'text-loss'}>
                    {(reveal.asset_returns.gold * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white">Cash ({reveal.allocation.cash}%)</span>
                  <span className={reveal.asset_returns.cash >= 0 ? 'text-gain' : 'text-loss'}>
                    {(reveal.asset_returns.cash * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Optimal Allocation (Hindsight) */}
            <div className="pt-4 border-t border-terminal-border">
              <h4 className="text-sm text-terminal-text mb-2">Optimal Allocation (Hindsight)</h4>
              <div className="space-y-1 text-sm font-mono mb-3">
                {reveal.optimal_allocation && (
                  <>
                    {reveal.optimal_allocation.stocks > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gold">100% Stocks</span>
                        <span className="text-gain">{(reveal.asset_returns.stocks * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {reveal.optimal_allocation.bonds > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gold">100% Bonds</span>
                        <span className="text-gain">{(reveal.asset_returns.bonds * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {reveal.optimal_allocation.gold > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gold">100% Gold</span>
                        <span className="text-gain">{(reveal.asset_returns.gold * 100).toFixed(1)}%</span>
                      </div>
                    )}
                    {reveal.optimal_allocation.cash > 0 && (
                      <div className="flex justify-between">
                        <span className="text-gold">100% Cash</span>
                        <span className="text-gain">{(reveal.asset_returns.cash * 100).toFixed(1)}%</span>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Comparison vs Optimal */}
            <div className="pt-4 border-t border-terminal-border">
              <h4 className="text-sm text-terminal-text mb-2">Your Performance vs Optimal</h4>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-white">Your Return</span>
                  <span className={`font-mono ${reveal.portfolio_return >= 0 ? 'text-gain' : 'text-loss'}`}>
                    {(reveal.portfolio_return * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white">Optimal Return</span>
                  <span className={`font-mono ${reveal.optimal_return >= 0 ? 'text-gain' : 'text-loss'}`}>
                    {(reveal.optimal_return * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white">Your Sharpe</span>
                  <span className="font-mono text-white">{reveal.portfolio_sharpe.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white">Optimal Sharpe</span>
                  <span className="font-mono text-white">{reveal.optimal_sharpe.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Result banner */}
            <div className={`mt-4 p-3 rounded-lg text-center ${
              beatBenchmark ? 'bg-gain/20 border border-gain/40' : 'bg-loss/20 border border-loss/40'
            }`}>
              <span className={`font-semibold ${beatBenchmark ? 'text-gain' : 'text-loss'}`}>
                {beatBenchmark 
                  ? `🎉 You matched the optimal allocation!`
                  : `You left ${(Math.abs(reveal.excess_return) * 100).toFixed(1)}% on the table vs optimal`
                }
              </span>
            </div>
          </div>

          {/* Your Rationale - only show if provided */}
          {reveal.rationale && reveal.rationale.length > 0 && (
            <div className="bg-terminal-card border-2 border-stocks/30 rounded-xl p-6 animate-slide-up animate-delay-400">
              <h3 className="text-lg font-medium mb-3 text-white">Your Rationale</h3>
              <blockquote className="text-terminal-text italic border-l-2 border-stocks pl-4">
                "{reveal.rationale}"
              </blockquote>
            </div>
          )}

          {/* Leaderboard CTA */}
          <div className="bg-terminal-card border-2 border-stocks/30 rounded-xl p-6 animate-slide-up animate-delay-500">
            <h3 className="text-lg font-medium mb-4 text-white">Join the Leaderboard</h3>
            
            {!authLoading && !user ? (
              // Not logged in - prompt to login
              <div className="text-center">
                <p className="text-terminal-muted mb-4">Log in to save your scores and track your performance</p>
                <button
                  onClick={() => {
                    // Store this game token to link after login
                    localStorage.setItem('pending_game_link', token)
                    localStorage.setItem('auth_return_to', `/reveal/${token}`)
                    router.push('/login')
                  }}
                  className="px-6 py-3 bg-stocks text-white rounded-lg hover:bg-stocks/80 transition-colors"
                >
                  Log In to Join Leaderboard
                </button>
              </div>
            ) : joinedLeaderboard ? (
              <div className="text-center py-2">
                <p className="text-gain mb-3">✓ You've joined as {username || user?.username || user?.email.split('@')[0]}</p>
                <a 
                  href="/leaderboard"
                  className="inline-block px-4 py-2 bg-stocks text-white rounded-lg hover:bg-stocks/80 transition-colors"
                >
                  View Leaderboard
                </a>
              </div>
            ) : (
              <div className="space-y-4">
                {!user?.username && (
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Choose a username"
                      className="flex-1 px-4 py-2 bg-terminal-bg border border-terminal-border rounded-lg
                               text-white placeholder-terminal-muted/50
                               focus:outline-none focus:border-stocks transition-colors"
                      maxLength={50}
                    />
                  </div>
                )}
                <button
                  onClick={handleJoinLeaderboard}
                  className="w-full px-6 py-2 bg-stocks text-white rounded-lg hover:bg-stocks/80 transition-colors"
                >
                  {user?.username ? 'Join as ' + user.username : 'Join Leaderboard'}
                </button>
              </div>
            )}
          </div>

          {/* Play Again */}
          <a 
            href="/"
            className="block w-full py-4 bg-stocks text-white font-semibold rounded-xl text-center
                     hover:bg-stocks/80 transition-colors shadow-lg shadow-stocks/20"
          >
            Play Again →
          </a>
        </div>
      </div>
    </div>
  )
}

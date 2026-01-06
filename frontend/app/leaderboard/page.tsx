'use client'

import { useState, useEffect } from 'react'
import { api, Leaderboard } from '@/lib/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'

export default function LeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState<Leaderboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadLeaderboard()
  }, [])

  async function loadLeaderboard() {
    try {
      const data = await api.getLeaderboard(50)
      setLeaderboard(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load leaderboard')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <LoadingSpinner />
          <p className="mt-4 text-terminal-muted">Loading leaderboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center max-w-md">
          <p className="text-loss">{error}</p>
          <p className="mt-2 text-terminal-muted">
            Make sure the backend is running and there are completed games.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold mb-2">Leaderboard</h2>
        <p className="text-terminal-muted">
          Top forecasters ranked by Brier score (lower is better)
        </p>
      </div>

      {leaderboard && leaderboard.entries.length > 0 ? (
        <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
          {/* Header */}
          <div className="grid grid-cols-6 gap-4 px-6 py-3 bg-terminal-bg border-b border-terminal-border text-sm text-terminal-muted font-medium">
            <div>Rank</div>
            <div>Player</div>
            <div className="text-right">Games</div>
            <div className="text-right">Avg Brier</div>
            <div className="text-right">Avg Sharpe</div>
            <div className="text-right">Excess Return</div>
          </div>

          {/* Entries */}
          <div className="divide-y divide-terminal-border">
            {leaderboard.entries.map((entry, i) => (
              <div 
                key={entry.username}
                className={`grid grid-cols-6 gap-4 px-6 py-4 ${
                  i < 3 ? 'bg-stocks/5' : ''
                }`}
              >
                <div className="font-mono">
                  {entry.rank === 1 && '🥇 '}
                  {entry.rank === 2 && '🥈 '}
                  {entry.rank === 3 && '🥉 '}
                  {entry.rank > 3 && `#${entry.rank}`}
                </div>
                <div className="font-medium truncate">{entry.username}</div>
                <div className="text-right font-mono text-terminal-muted">
                  {entry.games_played}
                </div>
                <div className="text-right font-mono">
                  {entry.avg_brier_score.toFixed(4)}
                </div>
                <div className="text-right font-mono">
                  {entry.avg_sharpe.toFixed(2)}
                </div>
                <div className={`text-right font-mono ${
                  entry.avg_excess_return >= 0 ? 'text-gain' : 'text-loss'
                }`}>
                  {entry.avg_excess_return >= 0 ? '+' : ''}{(entry.avg_excess_return * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-terminal-muted">
          <p>No entries yet. Be the first to join the leaderboard!</p>
          <a 
            href="/"
            className="inline-block mt-4 px-6 py-3 bg-stocks text-white rounded-lg hover:bg-stocks/80 transition-colors"
          >
            Play Now
          </a>
        </div>
      )}

      {/* Scoring explanation */}
      <div className="mt-8 bg-terminal-card border border-terminal-border rounded-xl p-6">
        <h3 className="text-lg font-medium mb-4">Scoring Guide</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div>
            <h4 className="font-medium text-stocks mb-2">Brier Score</h4>
            <p className="text-terminal-muted mb-2">
              Measures prediction calibration. Lower is better.
            </p>
            <ul className="space-y-1 text-terminal-muted">
              <li>• &lt; 0.10: Excellent</li>
              <li>• 0.10 - 0.15: Good</li>
              <li>• 0.15 - 0.20: Decent</li>
              <li>• 0.20 - 0.25: Poor (random = 0.25)</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-stocks mb-2">Sharpe Ratio</h4>
            <p className="text-terminal-muted mb-2">
              Risk-adjusted returns. Higher is better.
            </p>
            <ul className="space-y-1 text-terminal-muted">
              <li>• &gt; 1.0: Excellent</li>
              <li>• 0.5 - 1.0: Good</li>
              <li>• 0 - 0.5: Average</li>
              <li>• &lt; 0: Negative returns</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}



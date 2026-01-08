'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { api } from '@/lib/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'

export default function WelcomePage() {
  const router = useRouter()
  const { user, loading: authLoading, refreshUser } = useAuth()
  const [username, setUsername] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    // If not logged in, redirect to login
    if (!authLoading && !user) {
      router.push('/login')
    }
    // If already has username, redirect to home
    if (!authLoading && user?.username) {
      router.push('/')
    }
  }, [authLoading, user, router])

  async function handleSetUsername(e: React.FormEvent) {
    e.preventDefault()
    
    const trimmed = username.trim()
    if (trimmed.length < 3) {
      setError('Username must be at least 3 characters')
      return
    }
    if (trimmed.length > 20) {
      setError('Username must be 20 characters or less')
      return
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
      setError('Username can only contain letters, numbers, underscores, and hyphens')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      await api.setUsername(trimmed)
      await refreshUser()
      
      // Check for return URL
      const returnTo = localStorage.getItem('auth_return_to')
      localStorage.removeItem('auth_return_to')
      
      router.push(returnTo || '/')
    } catch (err: any) {
      setError(err.message || 'Failed to set username')
      setSubmitting(false)
    }
  }

  if (authLoading || (user?.username)) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-terminal-card border border-terminal-border rounded-xl p-8">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold mb-2">Welcome to Hindsight! 🎉</h1>
            <p className="text-terminal-muted">
              Choose a username to appear on the leaderboard
            </p>
          </div>

          <form onSubmit={handleSetUsername} className="space-y-4">
            <div>
              <label className="block text-sm text-terminal-muted mb-2">
                Username <span className="text-stocks">(public)</span>
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter a username"
                className="w-full px-4 py-3 bg-terminal-bg border border-terminal-border rounded-lg
                         text-white placeholder-terminal-muted/50
                         focus:outline-none focus:border-stocks transition-colors"
                maxLength={20}
                autoFocus
              />
              <p className="mt-2 text-xs text-terminal-muted">
                3-20 characters. Letters, numbers, underscores, hyphens only.
              </p>
            </div>

            {error && (
              <div className="p-3 bg-loss/10 border border-loss/30 rounded-lg text-loss text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting || username.trim().length < 3}
              className="w-full py-3 bg-stocks text-white font-semibold rounded-lg
                       hover:bg-stocks/80 transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Setting up...' : 'Continue'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-terminal-muted">
            Your email ({user?.email}) stays private. Only your username is shown publicly.
          </p>
        </div>
      </div>
    </div>
  )
}


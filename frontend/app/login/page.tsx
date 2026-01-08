'use client'

import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { api } from '@/lib/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'

function LoginContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const returnTo = searchParams.get('returnTo')
  
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    
    if (!email.trim()) {
      setError('Please enter your email')
      return
    }
    
    setStatus('sending')
    setError(null)
    
    try {
      await api.requestMagicLink(email.trim())
      setStatus('sent')
      
      // Store return URL for after verification
      if (returnTo) {
        localStorage.setItem('auth_return_to', returnTo)
      }
    } catch (err: any) {
      setStatus('error')
      setError(err.message || 'Failed to send login link')
    }
  }

  if (status === 'sent') {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="max-w-md w-full text-center">
          <div className="bg-terminal-card border border-terminal-border rounded-xl p-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gain/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-gain" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-2xl font-semibold mb-2">Check your email</h1>
            <p className="text-terminal-muted mb-4">
              We sent a login link to <span className="text-terminal-text font-medium">{email}</span>
            </p>
            <p className="text-sm text-terminal-muted">
              Click the link in the email to log in. The link expires in 15 minutes.
            </p>
            <button
              onClick={() => setStatus('idle')}
              className="mt-6 text-stocks hover:text-stocks/80 text-sm"
            >
              Use a different email
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="max-w-md w-full">
        <div className="bg-terminal-card border border-terminal-border rounded-xl p-8">
          <h1 className="text-2xl font-semibold mb-2 text-center">Log In</h1>
          <p className="text-terminal-muted text-center mb-6">
            Track your performance across multiple games
          </p>
          
          {error && (
            <div className="mb-4 p-3 bg-loss/10 border border-loss/30 rounded-lg text-loss text-sm">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-2">
                Email address
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 bg-terminal-bg border border-terminal-border rounded-lg
                         focus:outline-none focus:border-stocks transition-colors
                         placeholder:text-terminal-muted"
                disabled={status === 'sending'}
              />
            </div>
            
            <button
              type="submit"
              disabled={status === 'sending'}
              className="w-full py-3 bg-stocks text-white font-semibold rounded-lg
                       hover:bg-stocks/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status === 'sending' ? 'Sending...' : 'Send Login Link'}
            </button>
          </form>
          
          <p className="mt-6 text-center text-sm text-terminal-muted">
            No password needed — we'll email you a login link.
          </p>
        </div>
        
        <p className="mt-4 text-center text-sm text-terminal-muted">
          New here? Enter your email to create an account.
          <br />
          <span className="text-terminal-text">
            You'll choose a public username for the leaderboard.
          </span>
        </p>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-[60vh] flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    }>
      <LoginContent />
    </Suspense>
  )
}

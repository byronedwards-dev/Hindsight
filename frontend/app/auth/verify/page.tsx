'use client'

import { Suspense, useEffect, useState, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { getApiUrl } from '@/lib/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'

function VerifyContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')
  const { refreshUser } = useAuth()
  
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [error, setError] = useState<string | null>(null)
  const hasAttempted = useRef(false)

  useEffect(() => {
    async function verify() {
      // Prevent double-calling (React StrictMode or dependency changes)
      if (hasAttempted.current) return
      hasAttempted.current = true

      if (!token) {
        setStatus('error')
        setError('No verification token provided')
        return
      }
      
      try {
        // Get stored game token to link
        const pendingGameToken = localStorage.getItem('pending_game_link')
        
        // Verify the magic link - this will redirect from the server
        // but we need to handle the case where we're on the frontend
        const API_BASE = getApiUrl()
        const url = new URL(`${API_BASE}/auth/verify`)
        url.searchParams.set('token', token)
        if (pendingGameToken) {
          url.searchParams.set('game_token', pendingGameToken)
        }
        
        const response = await fetch(url.toString(), {
          credentials: 'include',
          redirect: 'manual'
        })
        
        if (response.type === 'opaqueredirect' || response.ok || response.status === 302) {
          // Clear pending game link
          localStorage.removeItem('pending_game_link')
          
          // Refresh user state
          await refreshUser()
          
          setStatus('success')
          
          // Check for return URL
          const returnTo = localStorage.getItem('auth_return_to')
          localStorage.removeItem('auth_return_to')
          
          // Redirect after brief delay
          setTimeout(() => {
            router.push(returnTo || '/')
          }, 1500)
        } else {
          const data = await response.json().catch(() => ({ detail: 'Verification failed' }))
          throw new Error(data.detail || 'Verification failed')
        }
      } catch (err: any) {
        setStatus('error')
        setError(err.message || 'Failed to verify login link')
      }
    }
    
    verify()
  }, [token, router, refreshUser])

  if (status === 'verifying') {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-terminal-muted">Verifying your login...</p>
        </div>
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="max-w-md w-full text-center">
          <div className="bg-terminal-card border border-terminal-border rounded-xl p-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gain/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-gain" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-semibold mb-2">You're logged in!</h1>
            <p className="text-terminal-muted">
              Redirecting you now...
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="max-w-md w-full text-center">
        <div className="bg-terminal-card border border-terminal-border rounded-xl p-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-loss/20 flex items-center justify-center">
            <svg className="w-8 h-8 text-loss" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h1 className="text-2xl font-semibold mb-2">Login Failed</h1>
          <p className="text-terminal-muted mb-4">
            {error || 'The login link is invalid or has expired.'}
          </p>
          <a
            href="/login"
            className="inline-block px-6 py-3 bg-stocks text-white font-semibold rounded-lg
                     hover:bg-stocks/80 transition-colors"
          >
            Try Again
          </a>
        </div>
      </div>
    </div>
  )
}

export default function VerifyPage() {
  return (
    <Suspense fallback={
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-terminal-muted">Loading...</p>
        </div>
      </div>
    }>
      <VerifyContent />
    </Suspense>
  )
}

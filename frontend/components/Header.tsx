'use client'

import { useAuth } from '@/lib/auth-context'

export function Header() {
  const { user, loading, logout } = useAuth()

  return (
    <header className="border-b border-terminal-border px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <a href="/" className="text-xl font-semibold tracking-tight hover:opacity-80 transition-opacity">
          <span className="text-stocks">Hindsight</span>{' '}
          <span className="text-terminal-muted">Economics</span>
        </a>
        <nav className="flex items-center gap-6 text-sm">
          <a href="/" className="text-terminal-muted hover:text-terminal-text transition-colors">
            Play
          </a>
          <a href="/leaderboard" className="text-terminal-muted hover:text-terminal-text transition-colors">
            Leaderboard
          </a>
          {!loading && (
            <>
              {user ? (
                <div className="flex items-center gap-4">
                  <span className="text-terminal-text">
                    {user.username || user.email.split('@')[0]}
                  </span>
                  <button
                    onClick={() => logout()}
                    className="text-terminal-muted hover:text-terminal-text transition-colors"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <a 
                  href="/login" 
                  className="px-4 py-2 bg-stocks text-white rounded-lg hover:bg-stocks/80 transition-colors"
                >
                  Log In
                </a>
              )}
            </>
          )}
        </nav>
      </div>
    </header>
  )
}


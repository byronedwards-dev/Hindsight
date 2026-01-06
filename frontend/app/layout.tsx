import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/lib/auth-context'
import { Header } from '@/components/Header'

export const metadata: Metadata = {
  title: 'Hindsight Economics',
  description: 'Test your economic intuition with historical market data',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-terminal-bg">
        <AuthProvider>
          <div className="min-h-screen flex flex-col">
            <Header />
            <main className="flex-1">
              {children}
            </main>
            <footer className="border-t border-terminal-border px-6 py-4 text-center text-sm text-terminal-muted">
              Test your economic intuition with real historical data
            </footer>
          </div>
        </AuthProvider>
      </body>
    </html>
  )
}

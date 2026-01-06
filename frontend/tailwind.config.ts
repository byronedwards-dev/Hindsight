import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Custom palette inspired by financial terminals
        terminal: {
          bg: '#0a0f14',
          card: '#111820',
          border: '#1e2a36',
          text: '#e2e8f0',
          muted: '#64748b',
        },
        gain: '#22c55e',
        loss: '#ef4444',
        stocks: '#3b82f6',
        bonds: '#22c55e', 
        cash: '#94a3b8',
        gold: '#eab308',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['Instrument Sans', 'system-ui', 'sans-serif'],
      },
      animation: {
        'reveal': 'reveal 2s ease-out forwards',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
      },
      keyframes: {
        reveal: {
          '0%': { width: '0%' },
          '100%': { width: '100%' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
export default config



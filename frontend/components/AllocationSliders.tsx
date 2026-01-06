'use client'

import { Allocation } from '@/lib/api'

interface AllocationSlidersProps {
  allocation: Allocation
  onChange: (allocation: Allocation) => void
}

interface SliderRowProps {
  label: string
  value: number
  color: string
  onChange: (value: number) => void
  disabled?: boolean
  isRemainder?: boolean
}

function SliderRow({ label, value, color, onChange, disabled = false, isRemainder = false }: SliderRowProps) {
  const dollarAmount = (value / 100 * 100000).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })

  return (
    <div className={`flex items-center gap-4 py-2 ${isRemainder ? 'opacity-70' : ''}`}>
      <div className="w-24 flex items-center gap-2">
        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
        <span className="text-sm">{label}</span>
      </div>
      
      <input
        type="range"
        min={0}
        max={100}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        disabled={disabled}
        className={`flex-1 h-2 rounded-lg cursor-pointer ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
        style={{
          background: `linear-gradient(to right, ${color} 0%, ${color} ${value}%, #1e2a36 ${value}%, #1e2a36 100%)`,
        }}
      />
      
      <div className="w-24 text-right">
        <span className="font-mono text-sm">{value}%</span>
        {isRemainder && <span className="text-xs text-terminal-muted ml-1">(auto)</span>}
      </div>
      
      <div className="w-24 text-right">
        <span className="font-mono text-sm text-terminal-muted">{dollarAmount}</span>
      </div>
    </div>
  )
}

export function AllocationSliders({ allocation, onChange }: AllocationSlidersProps) {
  const total = allocation.stocks + allocation.bonds + allocation.cash + allocation.gold
  const isValid = total === 100

  // When stocks, bonds, or gold change, adjust cash to maintain 100%
  function updateAllocationWithCashAdjust(key: 'stocks' | 'bonds' | 'gold', value: number) {
    const otherAssets = key === 'stocks' ? allocation.bonds + allocation.gold :
                        key === 'bonds' ? allocation.stocks + allocation.gold :
                        allocation.stocks + allocation.bonds
    
    // Cap the value so total doesn't exceed 100
    const maxValue = 100 - otherAssets
    const cappedValue = Math.min(value, maxValue)
    
    // Calculate remaining for cash
    const newCash = 100 - cappedValue - otherAssets
    
    onChange({
      ...allocation,
      [key]: cappedValue,
      cash: Math.max(0, newCash),
    })
  }

  // Cash slider adjusts directly (user can override auto-calculation)
  function updateCash(value: number) {
    const otherAssets = allocation.stocks + allocation.bonds + allocation.gold
    const maxCash = 100 - otherAssets
    onChange({
      ...allocation,
      cash: Math.min(value, maxCash),
    })
  }

  // Quick presets
  function applyPreset(preset: Allocation) {
    onChange(preset)
  }

  // Calculate if cash is the "remainder"
  const cashIsRemainder = allocation.cash === (100 - allocation.stocks - allocation.bonds - allocation.gold)

  return (
    <div>
      <SliderRow
        label="Stocks"
        value={allocation.stocks}
        color="#3b82f6"
        onChange={(v) => updateAllocationWithCashAdjust('stocks', v)}
      />
      <SliderRow
        label="Bonds"
        value={allocation.bonds}
        color="#22c55e"
        onChange={(v) => updateAllocationWithCashAdjust('bonds', v)}
      />
      <SliderRow
        label="Gold"
        value={allocation.gold}
        color="#eab308"
        onChange={(v) => updateAllocationWithCashAdjust('gold', v)}
      />
      <SliderRow
        label="Cash"
        value={allocation.cash}
        color="#94a3b8"
        onChange={updateCash}
        isRemainder={cashIsRemainder}
      />
      
      {/* Total indicator */}
      <div className="mt-4 pt-4 border-t border-terminal-border flex items-center justify-between">
        <span className="text-sm">Total</span>
        <span className={`font-mono text-lg font-medium ${isValid ? 'text-gain' : 'text-loss'}`}>
          {total}% {isValid ? '✓' : `(${total > 100 ? '+' : ''}${total - 100})`}
        </span>
      </div>
      
      {/* Presets */}
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => applyPreset({ stocks: 60, bonds: 40, cash: 0, gold: 0 })}
          className="px-3 py-1 text-xs bg-terminal-bg border border-terminal-border rounded-lg 
                   hover:border-stocks transition-colors"
        >
          60/40
        </button>
        <button
          type="button"
          onClick={() => applyPreset({ stocks: 100, bonds: 0, cash: 0, gold: 0 })}
          className="px-3 py-1 text-xs bg-terminal-bg border border-terminal-border rounded-lg 
                   hover:border-stocks transition-colors"
        >
          All Stocks
        </button>
        <button
          type="button"
          onClick={() => applyPreset({ stocks: 0, bonds: 100, cash: 0, gold: 0 })}
          className="px-3 py-1 text-xs bg-terminal-bg border border-terminal-border rounded-lg 
                   hover:border-bonds transition-colors"
        >
          All Bonds
        </button>
        <button
          type="button"
          onClick={() => applyPreset({ stocks: 0, bonds: 0, cash: 100, gold: 0 })}
          className="px-3 py-1 text-xs bg-terminal-bg border border-terminal-border rounded-lg 
                   hover:border-cash transition-colors"
        >
          All Cash
        </button>
        <button
          type="button"
          onClick={() => applyPreset({ stocks: 25, bonds: 25, cash: 25, gold: 25 })}
          className="px-3 py-1 text-xs bg-terminal-bg border border-terminal-border rounded-lg 
                   hover:border-gold transition-colors"
        >
          Equal
        </button>
      </div>
    </div>
  )
}

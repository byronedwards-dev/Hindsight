'use client'

import { Allocation } from '@/lib/api'

interface AllocationSlidersProps {
  allocation: Allocation
  onChange: (allocation: Allocation) => void
}

const ALLOCATION_PRESETS: { name: string; allocation: Allocation; color: string }[] = [
  { name: '60/40 Stocks/Bonds', allocation: { stocks: 60, bonds: 40, cash: 0, gold: 0 }, color: 'stocks' },
  { name: 'All Stocks', allocation: { stocks: 100, bonds: 0, cash: 0, gold: 0 }, color: 'stocks' },
  { name: 'All Bonds', allocation: { stocks: 0, bonds: 100, cash: 0, gold: 0 }, color: 'bonds' },
  { name: 'All Gold', allocation: { stocks: 0, bonds: 0, cash: 0, gold: 100 }, color: 'gold' },
  { name: 'Equal Split', allocation: { stocks: 25, bonds: 25, cash: 25, gold: 25 }, color: 'terminal-text' },
]

function allocationEquals(a: Allocation, b: Allocation): boolean {
  return a.stocks === b.stocks && a.bonds === b.bonds && a.cash === b.cash && a.gold === b.gold
}

export function AllocationSliders({ allocation, onChange }: AllocationSlidersProps) {
  const selectedPreset = ALLOCATION_PRESETS.find(p => allocationEquals(p.allocation, allocation))

  return (
    <div className="space-y-4">
      {/* Preset Buttons */}
      <div className="grid grid-cols-1 gap-3">
        {ALLOCATION_PRESETS.map((preset) => {
          const isSelected = allocationEquals(preset.allocation, allocation)
          return (
            <button
              key={preset.name}
              type="button"
              onClick={() => onChange(preset.allocation)}
              className={`w-full px-4 py-4 rounded-xl border-2 transition-all text-left ${
                isSelected 
                  ? `bg-${preset.color}/20 border-${preset.color} text-white` 
                  : 'bg-terminal-bg border-terminal-border text-terminal-muted hover:border-terminal-text hover:text-terminal-text'
              }`}
              style={isSelected ? {
                backgroundColor: preset.color === 'stocks' ? 'rgba(59, 130, 246, 0.2)' :
                                preset.color === 'bonds' ? 'rgba(34, 197, 94, 0.2)' :
                                preset.color === 'gold' ? 'rgba(234, 179, 8, 0.2)' :
                                'rgba(255, 255, 255, 0.1)',
                borderColor: preset.color === 'stocks' ? '#3b82f6' :
                             preset.color === 'bonds' ? '#22c55e' :
                             preset.color === 'gold' ? '#eab308' :
                             '#94a3b8'
              } : {}}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-base">{preset.name}</span>
                {isSelected && (
                  <span className="text-gain text-lg">✓</span>
                )}
              </div>
              <div className="mt-1 text-sm opacity-70 font-mono">
                {preset.allocation.stocks > 0 && `${preset.allocation.stocks}% Stocks`}
                {preset.allocation.bonds > 0 && `${preset.allocation.stocks > 0 ? ' · ' : ''}${preset.allocation.bonds}% Bonds`}
                {preset.allocation.gold > 0 && `${(preset.allocation.stocks > 0 || preset.allocation.bonds > 0) ? ' · ' : ''}${preset.allocation.gold}% Gold`}
                {preset.allocation.cash > 0 && `${(preset.allocation.stocks > 0 || preset.allocation.bonds > 0 || preset.allocation.gold > 0) ? ' · ' : ''}${preset.allocation.cash}% Cash`}
              </div>
            </button>
          )
        })}
      </div>

      {/* Display current allocation summary */}
      <div className="mt-4 pt-4 border-t border-terminal-border">
        <div className="flex items-center justify-between text-sm">
          <span className="text-terminal-muted">Your Allocation</span>
          <span className="font-mono text-terminal-text">
            {selectedPreset ? selectedPreset.name : 'Custom'}
          </span>
        </div>
        <div className="mt-2 flex gap-1 h-3 rounded-full overflow-hidden">
          {allocation.stocks > 0 && (
            <div 
              className="bg-stocks transition-all" 
              style={{ width: `${allocation.stocks}%` }}
              title={`Stocks: ${allocation.stocks}%`}
            />
          )}
          {allocation.bonds > 0 && (
            <div 
              className="bg-bonds transition-all" 
              style={{ width: `${allocation.bonds}%` }}
              title={`Bonds: ${allocation.bonds}%`}
            />
          )}
          {allocation.gold > 0 && (
            <div 
              className="bg-gold transition-all" 
              style={{ width: `${allocation.gold}%` }}
              title={`Gold: ${allocation.gold}%`}
            />
          )}
          {allocation.cash > 0 && (
            <div 
              className="bg-cash transition-all" 
              style={{ width: `${allocation.cash}%` }}
              title={`Cash: ${allocation.cash}%`}
            />
          )}
        </div>
      </div>
    </div>
  )
}

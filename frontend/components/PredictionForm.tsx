'use client'

import { Predictions } from '@/lib/api'

interface PredictionFormProps {
  predictions: Predictions
  onChange: (predictions: Predictions) => void
}

interface PredictionRowProps {
  threshold: string
  value: number
  onChange: (value: number) => void
}

function PredictionRow({ threshold, value, onChange }: PredictionRowProps) {
  // Determine if user thinks Yes or No based on probability
  const isYes = value >= 0.5
  const confidence = isYes ? value : 1 - value
  
  function handleDirectionChange(newIsYes: boolean) {
    // Keep same confidence level, just flip direction
    const newValue = newIsYes ? confidence : 1 - confidence
    onChange(newValue)
  }
  
  function handleConfidenceChange(newConfidence: number) {
    // Apply to current direction
    const newValue = isYes ? newConfidence : 1 - newConfidence
    onChange(newValue)
  }

  return (
    <div className="space-y-2 py-3 border-b border-terminal-border last:border-0">
      <div className="flex items-center justify-between">
        <span className="font-mono text-sm">Returns &gt; {threshold}</span>
        <span className="font-mono text-sm text-terminal-muted">
          {(value * 100).toFixed(0)}% prob
        </span>
      </div>
      
      <div className="flex items-center gap-4">
        {/* Yes/No selection */}
        <div className="flex rounded-lg overflow-hidden border border-terminal-border">
          <button
            type="button"
            onClick={() => handleDirectionChange(true)}
            className={`px-3 py-1 text-sm transition-colors ${
              isYes 
                ? 'bg-gain text-white' 
                : 'bg-terminal-bg text-terminal-muted hover:text-terminal-text'
            }`}
          >
            Yes
          </button>
          <button
            type="button"
            onClick={() => handleDirectionChange(false)}
            className={`px-3 py-1 text-sm transition-colors ${
              !isYes 
                ? 'bg-loss text-white' 
                : 'bg-terminal-bg text-terminal-muted hover:text-terminal-text'
            }`}
          >
            No
          </button>
        </div>
        
        {/* Confidence slider */}
        <div className="flex-1 flex items-center gap-2">
          <span className="text-xs text-terminal-muted">50%</span>
          <input
            type="range"
            min={50}
            max={100}
            value={confidence * 100}
            onChange={(e) => handleConfidenceChange(Number(e.target.value) / 100)}
            className="flex-1"
          />
          <span className="text-xs text-terminal-muted">100%</span>
        </div>
        
        <span className="font-mono text-sm w-16 text-right">
          {(confidence * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  )
}

export function PredictionForm({ predictions, onChange }: PredictionFormProps) {
  function updatePrediction(key: keyof Predictions, value: number) {
    const newPredictions = { ...predictions, [key]: value }
    
    // Ensure monotonicity: P(>15%) <= P(>10%) <= P(>5%) <= P(>0%)
    if (key === 'above_15pct') {
      newPredictions.above_10pct = Math.max(newPredictions.above_10pct, value)
      newPredictions.above_5pct = Math.max(newPredictions.above_5pct, newPredictions.above_10pct)
      newPredictions.above_0pct = Math.max(newPredictions.above_0pct, newPredictions.above_5pct)
    } else if (key === 'above_10pct') {
      newPredictions.above_15pct = Math.min(newPredictions.above_15pct, value)
      newPredictions.above_5pct = Math.max(newPredictions.above_5pct, value)
      newPredictions.above_0pct = Math.max(newPredictions.above_0pct, newPredictions.above_5pct)
    } else if (key === 'above_5pct') {
      newPredictions.above_15pct = Math.min(newPredictions.above_15pct, value)
      newPredictions.above_10pct = Math.min(Math.max(newPredictions.above_10pct, newPredictions.above_15pct), value)
      newPredictions.above_0pct = Math.max(newPredictions.above_0pct, value)
    } else if (key === 'above_0pct') {
      newPredictions.above_15pct = Math.min(newPredictions.above_15pct, value)
      newPredictions.above_10pct = Math.min(newPredictions.above_10pct, value)
      newPredictions.above_5pct = Math.min(newPredictions.above_5pct, value)
    }
    
    onChange(newPredictions)
  }

  return (
    <div>
      <PredictionRow
        threshold="+15%"
        value={predictions.above_15pct}
        onChange={(v) => updatePrediction('above_15pct', v)}
      />
      <PredictionRow
        threshold="+10%"
        value={predictions.above_10pct}
        onChange={(v) => updatePrediction('above_10pct', v)}
      />
      <PredictionRow
        threshold="+5%"
        value={predictions.above_5pct}
        onChange={(v) => updatePrediction('above_5pct', v)}
      />
      <PredictionRow
        threshold="0%"
        value={predictions.above_0pct}
        onChange={(v) => updatePrediction('above_0pct', v)}
      />
    </div>
  )
}



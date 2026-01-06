'use client'

interface RationaleInputProps {
  value: string
  onChange: (value: string) => void
  maxLength?: number
}

export function RationaleInput({ 
  value, 
  onChange,
  maxLength = 500 
}: RationaleInputProps) {
  const length = value.length
  const isTooLong = length > maxLength

  return (
    <div>
      <p className="text-sm text-terminal-muted mb-2">
        Why did you make these predictions? (optional, max {maxLength} characters)
      </p>
      
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Share your reasoning... What patterns do you see? What's your economic thesis?"
        className="w-full h-32 px-4 py-3 bg-terminal-bg border border-terminal-border rounded-lg
                 text-terminal-text placeholder-terminal-muted/50 resize-none
                 focus:outline-none focus:border-stocks transition-colors"
        maxLength={maxLength + 50} // Allow some overflow for editing
      />
      
      {/* Character count */}
      <div className="mt-2 flex items-center justify-between text-xs">
        <span className={`${
          isTooLong ? 'text-loss' : 
          length > 0 ? 'text-gain' : 
          'text-terminal-muted'
        }`}>
          {isTooLong && `${length - maxLength} characters over limit`}
          {!isTooLong && length > 0 && '✓ Rationale added'}
          {length === 0 && 'Optional'}
        </span>
        <span className={`font-mono ${
          isTooLong ? 'text-loss' : 'text-terminal-muted'
        }`}>
          {length}/{maxLength}
        </span>
      </div>
    </div>
  )
}

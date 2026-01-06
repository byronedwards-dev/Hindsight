'use client'

import { useState } from 'react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea
} from 'recharts'
import { MonthlyData } from '@/lib/api'

interface MacroIndicatorsProps {
  data: MonthlyData[]
  showForward?: boolean
  showPredictionLine?: boolean
  hardMode?: boolean  // Index values to 100 instead of showing actual numbers
  startDate?: string  // Date of month 24 (the prediction point, e.g., "2010-01-01")
}

// Helper to format month index to actual date label
function getMonthLabel(monthIndex: number, startDateStr?: string): string {
  if (!startDateStr) {
    return `Month ${monthIndex}`
  }
  // Parse the date string (YYYY-MM-DD) to get year and month directly
  const [year, month] = startDateStr.split('-').map(Number)
  // startDateStr is month 24, calculate offset from there
  // monthIndex 24 = startDate, monthIndex 1 = 23 months before, monthIndex 36 = 12 months after
  const totalMonths = (year * 12 + (month - 1)) + (monthIndex - 24)
  const resultYear = Math.floor(totalMonths / 12)
  const resultMonth = totalMonths % 12
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${monthNames[resultMonth]} ${resultYear}`
}

interface IndicatorConfig {
  key: string
  label: string
  shortLabel: string
  color: string
  unit: string
  referenceValue?: number
  referenceLabel?: string
  dataKey: keyof MonthlyData
  description: string
  hardModeLabel: string  // Label when in hard mode
}

const INDICATORS: IndicatorConfig[] = [
  {
    key: 'gdp',
    label: 'GDP Growth (YoY)',
    shortLabel: 'GDP',
    color: '#3b82f6',
    unit: '%',
    referenceValue: 0,
    referenceLabel: '0% (no growth)',
    dataKey: 'gdp_growth_yoy',
    description: 'Year-over-year real GDP growth rate',
    hardModeLabel: 'Economic Output Growth'
  },
  {
    key: 'unemployment',
    label: 'Unemployment Rate',
    shortLabel: 'Unemployment',
    color: '#ef4444',
    unit: '%',
    referenceValue: 5,
    referenceLabel: '5% (natural rate)',
    dataKey: 'unemployment_rate',
    description: 'Civilian unemployment rate (U-3)',
    hardModeLabel: 'Labor Market Slack'
  },
  {
    key: 'inflation',
    label: 'Inflation Rate (YoY)',
    shortLabel: 'Inflation',
    color: '#f97316',
    unit: '%',
    referenceValue: 2,
    referenceLabel: '2% (Fed target)',
    dataKey: 'inflation_rate_yoy',
    description: 'Year-over-year CPI inflation',
    hardModeLabel: 'Price Level Change'
  },
  {
    key: 'fedfunds',
    label: 'Federal Funds Rate',
    shortLabel: 'Fed Funds',
    color: '#8b5cf6',
    unit: '%',
    dataKey: 'fed_funds_rate',
    description: 'Federal Reserve target interest rate',
    hardModeLabel: 'Policy Rate'
  },
  {
    key: 'industrial',
    label: 'Industrial Production (YoY)',
    shortLabel: 'Industrial',
    color: '#06b6d4',
    unit: '%',
    referenceValue: 0,
    referenceLabel: '0% (no change)',
    dataKey: 'industrial_prod_yoy',
    description: 'Year-over-year change in industrial output',
    hardModeLabel: 'Manufacturing Activity'
  },
]

export function MacroIndicators({ data, showForward = false, showPredictionLine = false, hardMode = false, startDate }: MacroIndicatorsProps) {
  const [activeTab, setActiveTab] = useState(0)
  
  // Filter to historical data unless showForward is true
  const chartData = showForward 
    ? data 
    : data.filter(d => !d.is_forward)

  const activeIndicator = INDICATORS[activeTab]
  
  // Prepare chart data for active indicator
  const rawData = chartData
    .map(d => ({
      month: getMonthLabel(d.month_index, startDate),
      monthIndex: d.month_index,
      value: d[activeIndicator.dataKey] as number | null,
    }))
    .filter(d => d.value !== null)
  
  // Find the label for month 24 (prediction point) from actual data
  const month24Label = rawData.find(d => d.monthIndex === 24)?.month
  const month25Label = rawData.find(d => d.monthIndex === 25)?.month
  const lastMonthLabel = rawData[rawData.length - 1]?.month

  // In hard mode, index values to 100 based on first value
  const baseValue = rawData.length > 0 && rawData[0].value !== null ? rawData[0].value : 1
  
  const formattedData = hardMode 
    ? rawData.map(d => ({
        ...d,
        value: d.value !== null ? (d.value / Math.abs(baseValue || 1)) * 100 : null
      }))
    : rawData

  // Calculate stats
  const values = formattedData.map(d => d.value).filter((v): v is number => v !== null)
  const currentValue = values.length > 0 ? values[values.length - 1] : null
  const startValue = values.length > 0 ? values[0] : null
  const minValue = values.length > 0 ? Math.min(...values) : 0
  const maxValue = values.length > 0 ? Math.max(...values) : 0
  const change = currentValue !== null && startValue !== null ? currentValue - startValue : null
  const changePercent = startValue !== null && change !== null ? (change / Math.abs(startValue || 1)) * 100 : null

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip bg-terminal-card border border-terminal-border rounded-lg p-3">
          <p className="font-mono text-sm text-terminal-text mb-1">{label}</p>
          <p className="font-mono text-lg" style={{ color: activeIndicator.color }}>
            {payload[0].value?.toFixed(1)}{hardMode ? '' : activeIndicator.unit}
          </p>
          {hardMode && (
            <p className="text-xs text-terminal-muted mt-1">
              Indexed to 100
            </p>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <div>
      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-4">
        {INDICATORS.map((indicator, index) => (
          <button
            key={indicator.key}
            onClick={() => setActiveTab(index)}
            className={`px-4 py-2 rounded-lg font-mono text-sm transition-all ${
              activeTab === index
                ? 'bg-terminal-accent text-white'
                : 'bg-terminal-bg text-terminal-muted hover:bg-terminal-border hover:text-terminal-text'
            }`}
            style={activeTab === index ? { backgroundColor: indicator.color } : {}}
          >
            {indicator.shortLabel}
          </button>
        ))}
      </div>

      {/* Stats Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="text-lg font-medium text-terminal-text">
            {hardMode ? activeIndicator.hardModeLabel : activeIndicator.label}
          </h4>
          <p className="text-sm text-terminal-muted">
            {hardMode ? 'Values indexed to 100 at start' : activeIndicator.description}
          </p>
        </div>
        <div className="text-right">
          <div className="font-mono text-2xl font-medium" style={{ color: activeIndicator.color }}>
            {currentValue !== null ? currentValue.toFixed(1) : '—'}{hardMode ? '' : activeIndicator.unit}
          </div>
          {change !== null && (
            <div className={`text-sm font-mono ${change >= 0 ? 'text-gain' : 'text-loss'}`}>
              {change >= 0 ? '↑' : '↓'} {Math.abs(change).toFixed(1)} from start
              {hardMode && changePercent !== null && (
                <span className="text-terminal-muted ml-1">
                  ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(0)}%)
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2a36" />
            <XAxis 
              dataKey="month" 
              tick={{ fill: '#64748b', fontSize: 11 }}
              tickLine={{ stroke: '#1e2a36' }}
              axisLine={{ stroke: '#1e2a36' }}
              interval={5}
            />
            <YAxis 
              tick={{ fill: '#64748b', fontSize: 11 }}
              tickLine={{ stroke: '#1e2a36' }}
              axisLine={{ stroke: '#1e2a36' }}
              domain={
                hardMode 
                  ? ['auto', 'auto']
                  : [
                      Math.min(minValue, activeIndicator.referenceValue ?? minValue) - 1,
                      Math.max(maxValue, activeIndicator.referenceValue ?? maxValue) + 1
                    ]
              }
              tickFormatter={(value) => {
                const numValue = Number(value)
                if (hardMode) {
                  return numValue.toFixed(0)
                }
                return `${numValue.toFixed(1)}${activeIndicator.unit}`
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Shaded area for forward period */}
            {showPredictionLine && showForward && month25Label && lastMonthLabel && (
              <ReferenceArea
                x1={month25Label}
                x2={lastMonthLabel}
                fill="#22c55e"
                fillOpacity={0.15}
                ifOverflow="visible"
              />
            )}
            
            {/* Vertical line at month 24 - the prediction point */}
            {showPredictionLine && month24Label && (
              <ReferenceLine 
                x={month24Label} 
                stroke="#f59e0b" 
                strokeWidth={3}
                strokeDasharray="8 4"
                ifOverflow="extendDomain"
                isFront={true}
                label={{
                  value: "← Your Prediction",
                  position: 'insideTopLeft',
                  fill: '#f59e0b',
                  fontSize: 11,
                  fontWeight: 'bold'
                }}
              />
            )}
            
            {/* Reference lines only in normal mode */}
            {!hardMode && activeIndicator.referenceValue !== undefined && (
              <ReferenceLine 
                y={activeIndicator.referenceValue} 
                stroke="#64748b" 
                strokeDasharray="5 5"
                label={{
                  value: activeIndicator.referenceLabel,
                  position: 'right',
                  fill: '#64748b',
                  fontSize: 10
                }}
              />
            )}
            
            {/* Reference line at 100 in hard mode */}
            {hardMode && (
              <ReferenceLine 
                y={100} 
                stroke="#64748b" 
                strokeDasharray="5 5"
                label={{
                  value: "Base (100)",
                  position: 'right',
                  fill: '#64748b',
                  fontSize: 10
                }}
              />
            )}
            
            <Line 
              type="monotone" 
              dataKey="value" 
              name={activeIndicator.label}
              stroke={activeIndicator.color} 
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 6, fill: activeIndicator.color }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Mini indicators for context */}
      <div className="grid grid-cols-5 gap-2 mt-4">
        {INDICATORS.map((indicator, index) => {
          const indicatorRawData = chartData
            .map(d => d[indicator.dataKey] as number | null)
            .filter((v): v is number => v !== null)
          
          let displayValue: number | null = null
          if (indicatorRawData.length > 0) {
            const rawVal = indicatorRawData[indicatorRawData.length - 1]
            const baseVal = indicatorRawData[0]
            displayValue = hardMode 
              ? (rawVal / Math.abs(baseVal || 1)) * 100 
              : rawVal
          }
          
          return (
            <button
              key={indicator.key}
              onClick={() => setActiveTab(index)}
              className={`p-2 rounded text-center transition-all ${
                activeTab === index
                  ? 'bg-terminal-border ring-1 ring-terminal-accent'
                  : 'bg-terminal-bg hover:bg-terminal-border'
              }`}
            >
              <div className="text-xs text-terminal-muted truncate">{indicator.shortLabel}</div>
              <div 
                className="font-mono text-sm font-medium"
                style={{ color: indicator.color }}
              >
                {displayValue !== null ? displayValue.toFixed(hardMode ? 0 : 1) : '—'}{hardMode ? '' : indicator.unit}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
